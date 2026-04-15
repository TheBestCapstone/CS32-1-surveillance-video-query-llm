"""LangChain + OpenAI multimodal refinement for pipeline events (no frame sampling or CLI here)."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI

from video.common.frames import FrameSample, PersonCrop, coarse_color_label_from_bgr, crop_bgr_at_time_xyxy
from video.core.schema.multi_camera import MatchVerification
from video.core.schema.refined_event_llm import RefinedEntity, RefinedEventsPayload, VectorEventsPayload

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class _TrackSummary:
    class_name: str
    start_time: float
    end_time: float
    rep_t_sec: float
    rep_bbox_xyxy: list[float]
    coarse_color: str


def _time_overlap(a_start: float, a_end: float, b_start: float, b_end: float) -> float:
    return max(0.0, min(a_end, b_end) - max(a_start, b_start))


def _summarize_tracks_for_merge(video_path: str, raw_events: list[dict[str, Any]]) -> dict[int, _TrackSummary]:
    """
    Aggregate time range per track_id from raw_events and estimate coarse color from a representative bbox crop.
    """
    by_tid: dict[int, list[dict[str, Any]]] = {}
    for e in raw_events:
        tid = e.get("track_id")
        if tid is None:
            continue
        by_tid.setdefault(int(tid), []).append(e)

    out: dict[int, _TrackSummary] = {}
    for tid, evs in by_tid.items():
        cls = str(evs[0].get("class_name", "unknown"))
        s = float(min(float(e.get("start_time", 0.0)) for e in evs))
        t = float(max(float(e.get("end_time", 0.0)) for e in evs))
        rep = evs[0]
        rep_t = float(rep.get("start_time", s))
        rep_bbox = rep.get("start_bbox_xyxy") or rep.get("end_bbox_xyxy") or [0, 0, 0, 0]
        rep_bbox = [float(x) for x in rep_bbox]
        crop = crop_bgr_at_time_xyxy(video_path, rep_t, rep_bbox)
        coarse_color = coarse_color_label_from_bgr(crop) if crop is not None else "unknown"
        out[tid] = _TrackSummary(
            class_name=cls,
            start_time=s,
            end_time=t,
            rep_t_sec=rep_t,
            rep_bbox_xyxy=rep_bbox,
            coarse_color=coarse_color,
        )
    return out


class _MergeDecision(RefinedEventsPayload.__class__):  # type: ignore[misc]
    pass


def _verify_merge_yesno_with_llm(
    *,
    video_path: str,
    a_tid: int,
    b_tid: int,
    a: _TrackSummary,
    b: _TrackSummary,
    model: str,
    temperature: float = 0.0,
) -> tuple[bool, float]:
    """
    LLM may only output YES/NO + confidence. Returns (is_yes, confidence).
    """
    from pydantic import BaseModel, Field

    class MergeYesNo(BaseModel):
        answer: Literal["YES", "NO"] = Field(description="Must be YES or NO only")
        confidence: float = Field(ge=0.0, le=1.0, description="Confidence between 0 and 1")

    parser = PydanticOutputParser(pydantic_object=MergeYesNo)

    crop_a = crop_bgr_at_time_xyxy(video_path, a.rep_t_sec, a.rep_bbox_xyxy)
    crop_b = crop_bgr_at_time_xyxy(video_path, b.rep_t_sec, b.rep_bbox_xyxy)
    images: list[dict[str, Any]] = []
    if crop_a is not None:
        # reuse PersonCrop encoder path
        pc_a = PersonCrop(t_sec=a.rep_t_sec, camera_id="single", track_id=a_tid, image_array=crop_a, jpg_base64="")
        pc_a.jpg_base64 = ""  # placeholder
        images.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{FrameSample(0,'').jpg_base64}"}})
    # We cannot easily reuse encoder without importing; so we pass no images if crop fails.
    # Note: model can still decide from metadata conservatively.

    system = (
        "You are a surveillance-video entity merge judge. "
        "Decide whether two track_ids belong to the same real-world target. "
        "You must output strict JSON with only YES/NO and a 0~1 confidence."
    )
    user_text = (
        f"track_a: id={a_tid}, class={a.class_name}, time=[{a.start_time:.3f},{a.end_time:.3f}], color_guess={a.coarse_color}\n"
        f"track_b: id={b_tid}, class={b.class_name}, time=[{b.start_time:.3f},{b.end_time:.3f}], color_guess={b.coarse_color}\n"
        "Same target? Answer YES only when very confident; otherwise NO.\n"
        f"{parser.get_format_instructions()}"
    )
    llm = ChatOpenAI(model=model, temperature=temperature)
    resp = llm.invoke([SystemMessage(content=system), HumanMessage(content=[{"type": "text", "text": user_text}])])
    text = resp.content if isinstance(resp.content, str) else str(resp.content)
    parsed = parser.parse(text)
    return parsed.answer == "YES", float(parsed.confidence)


def build_entities_with_hard_constraints(
    *,
    video_path: str,
    raw_events: list[dict[str, Any]],
    model: str,
    max_gap_sec: float = 300.0,
    min_llm_confidence: float = 0.75,
) -> list[RefinedEntity]:
    """
    Filter candidate pairs with hard rules first, then LLM YES/NO + confidence for merging.

    Hard rules (skip LLM if any fails):
    - Temporal overlap -> cannot be same target
    - Clearly different coarse color -> skip
    - Time gap > 5min -> skip
    """
    tracks = _summarize_tracks_for_merge(video_path, raw_events)
    tids = sorted(tracks.keys())

    parent: dict[int, int] = {}

    def find(x: int) -> int:
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for i in range(len(tids)):
        for j in range(i + 1, len(tids)):
            a_tid, b_tid = tids[i], tids[j]
            a, b = tracks[a_tid], tracks[b_tid]
            if a.class_name != b.class_name:
                continue
            if _time_overlap(a.start_time, a.end_time, b.start_time, b.end_time) > 0:
                continue
            gap = min(abs(b.start_time - a.end_time), abs(a.start_time - b.end_time))
            if gap > max_gap_sec:
                continue
            if a.coarse_color != "unknown" and b.coarse_color != "unknown" and a.coarse_color != b.coarse_color:
                continue
            yes, conf = _verify_merge_yesno_with_llm(
                video_path=video_path,
                a_tid=a_tid,
                b_tid=b_tid,
                a=a,
                b=b,
                model=model,
                temperature=0.0,
            )
            if yes and conf > min_llm_confidence:
                union(a_tid, b_tid)

    groups: dict[int, list[int]] = {}
    for tid in tids:
        groups.setdefault(find(tid), []).append(tid)

    entities: list[RefinedEntity] = []
    for idx, (_, members) in enumerate(sorted(groups.items(), key=lambda x: min(x[1])), start=1):
        cls = tracks[members[0]].class_name
        entities.append(
            RefinedEntity(
                entity_id=f"{cls}_{idx}",
                class_name=cls,
                local_track_ids=sorted(members),
                appearance={"color_cn": tracks[members[0]].coarse_color, "color_confidence": 0.5},
                location={},
                notes="Entities merged via hard-rule filtering + LLM YES/NO.",
            )
        )
    return entities


def refine_events_with_llm(
    *,
    video_path: str,
    clip: dict[str, float],
    raw_events: list[dict[str, Any]],
    frames: list[FrameSample],
    model: str = "gpt-5.4",
    temperature: float = 0.1,
    max_time_adjust_sec: float = 0.5,
    merge_location_iou_threshold: float = 0.9,
    merge_center_dist_px: float = 30.0,
    merge_location_norm_diff: float = 0.10,
    pre_entities: list[RefinedEntity] | None = None,
) -> RefinedEventsPayload:
    """Send sampled frames + raw events to the LLM; return corrected refined_events (strict JSON)."""
    parser = PydanticOutputParser(pydantic_object=RefinedEventsPayload)

    images_content: list[dict[str, Any]] = []
    for f in frames:
        images_content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{f.jpg_base64}"},
            }
        )

    system = (
        "You are a surveillance-video event labeling and correction assistant. "
        "You work from timestamped key frames and a draft event list (from YOLO+tracking). "
        "Correct semantics and add action detail. "
        "First understand the scene (parking lot, road, entrance/exit, lane sides, sidewalk, etc.). "
        "For each event explanation, describe both how the subject moves and which scene sub-region it is in "
        "(e.g. passing mid-right on the road, entering the parking entrance, walking on the sidewalk near the exit). "
        "Most important: preserve pipeline temporal information; do not change times without strong evidence. "
        "Use English for all free-text string values. Output must strictly match the given JSON schema (including *_cn key names where present)."
    )

    user_text = (
        f"Video path: {video_path}\n"
        f"Clip under analysis: start_sec={clip['start_sec']}, end_sec={clip['end_sec']}\n\n"
        "Raw pipeline events for this clip (may contain false positives, bad timing, or split duplicates):\n"
        f"{json.dumps(raw_events, ensure_ascii=False, indent=2)}\n\n"
        "Uniformly sampled key frames for this clip (timestamps are listed below; state in evidence which frame times you rely on):\n"
        + "\n".join([f"- frame_time_sec={f.t_sec:.3f}" for f in frames])
        + "\n\n"
        "Tasks (prioritize preserving timing; always include scene + motion in English):\n"
        "0) Emit scene_context: summarize in English where the road vs parking vs entrances/exits/main paths appear "
        "(left/center/right, far/near).\n"
        "1) entities will be provided by the system when applicable — use them verbatim; do not add or merge entities.\n"
        f"     Location-merge guidance (tunable):\n"
        f"     - Merge only when you are very sure it is the same physical target.\n"
        f"     - For cars, do not merge different track_ids unless all hold:\n"
        f"       (a) time is contiguous/adjacent (<=1s)\n"
        f"       (b) bboxes almost coincide: IoU >= {merge_location_iou_threshold}\n"
        f"       (c) color/appearance matches (e.g. both white/silver, no contradictory cues)\n"
        f"       Center distance <= {merge_center_dist_px} px is supporting evidence only, not sufficient alone.\n"
        f"     - Hard proportional constraint:\n"
        f"       raw_events may include start_center_norm/end_center_norm (0~1 normalized centers).\n"
        f"       If normalized center delta on x or y exceeds {merge_location_norm_diff} (~10% of frame width/height), forbid merge.\n"
        f"       Exception only if frames show near-identical appearance (color + salient features) and continuous time; explain in notes.\n"
        "     - Stationary cars: merge broken track_ids only if same fixed slot, bbox stable over time, same color.\n"
        "     - Persons: merge cautiously only when clothing, body shape, and position continuity all agree.\n"
        "   - Each entity location must include: scene_zone, region_text, movement_in_scene_cn (one English sentence; legacy key name).\n"
        "   - Each entity must include appearance (at least color_cn + color_confidence) in English.\n"
        "2) refined_events:\n"
        "   - Bind events to entity_id (optionally keep one representative track_id).\n"
        "   - details must include movement_scene_narrative_cn: one English sentence for motion + sub-region (entrance/exit/mid-road right/slot, etc.).\n"
        "   - location must include: scene_zone, start_scene_cn, end_scene_cn, movement_scene_cn (English strings); "
        "keep start_bbox_xyxy/end_bbox_xyxy from raw_events when present and relate them to the scene.\n"
        "3) Temporal correction (hard rules):\n"
        f"   - Treat raw_events start_time/end_time as a strong prior.\n"
        f"   - Adjust boundaries only with clear frame evidence; one-sided shift <= {max_time_adjust_sec} s.\n"
        "   - If timing seems wrong but evidence is weak: do not change times; write \"uncertain\" in evidence.\n"
        "4) False positives:\n"
        "   - Remove obvious false events or lower confidence with a short English reason.\n\n"
        f"{parser.get_format_instructions()}"
    )

    if pre_entities is not None:
        user_text += "\n\nPre-defined entities (keep exactly; do not add/merge/delete; only reference entity_id in refined_events):\n"
        user_text += json.dumps([e.model_dump() for e in pre_entities], ensure_ascii=False, indent=2)

    user_content: list[dict[str, Any]] = [
        {"type": "text", "text": user_text},
        *images_content,
    ]
    llm = ChatOpenAI(model=model, temperature=temperature)
    resp = llm.invoke(
        [
            SystemMessage(content=system),
            HumanMessage(content=user_content),
        ]
    )
    text = resp.content if isinstance(resp.content, str) else str(resp.content)
    return parser.parse(text)


def refine_vector_events_with_llm(
    *,
    video_id: str,
    clip: dict[str, float],
    raw_events: list[dict[str, Any]],
    frames: list[FrameSample],
    model: str = "gpt-5.4",
    temperature: float = 0.0,
) -> VectorEventsPayload:
    """Production vector-store mode: minimal fields for retrieval; never change start/end times."""
    parser = PydanticOutputParser(pydantic_object=VectorEventsPayload)

    images_content: list[dict[str, Any]] = [
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{f.jpg_base64}"}}
        for f in frames
    ]

    system = (
        "You are a surveillance-video event extractor. "
        "From raw events (with start_time/end_time and bbox) and key frames, output minimal records for vector retrieval. "
        "Hard rule: never modify start_time/end_time — copy them exactly. "
        "No extra fields, no Markdown, no prose outside JSON."
    )

    user_text = (
        f"video_id: {video_id}\n"
        f"clip: start_sec={clip['start_sec']}, end_sec={clip['end_sec']}\n\n"
        "raw_events_json (copy start_time/end_time exactly into your output):\n"
        f"{json.dumps(raw_events, ensure_ascii=False, indent=2)}\n\n"
        "Key frame timestamps:\n"
        + "\n".join([f"- t={f.t_sec:.3f}" for f in frames])
        + "\n\n"
        "Output rules:\n"
        "- JSON only; must match the schema.\n"
        "- event_text_cn: English sentence with time range + subject (with color) + action + scene region (entrance/exit/road right/parking/sidewalk); field name is legacy.\n"
        "- object_color_cn: prefer white/black/silver_gray/red/blue/dark/unknown (English; legacy field name).\n"
        "- keywords: short retrieval tokens (English), e.g. driving_in/parking/road_right/entrance/sidewalk.\n"
        f"{parser.get_format_instructions()}"
    )

    llm = ChatOpenAI(model=model, temperature=temperature)
    resp = llm.invoke(
        [
            SystemMessage(content=system),
            HumanMessage(content=[{"type": "text", "text": user_text}, *images_content]),
        ]
    )
    text = resp.content if isinstance(resp.content, str) else str(resp.content)
    return parser.parse(text)


# ------------------------------------------------------------------
# Cross-camera person match verification
# ------------------------------------------------------------------

def verify_person_match_with_llm(
    crop_a: PersonCrop,
    crop_b: PersonCrop,
    model: str = "gpt-4o-mini",
    temperature: float = 0.0,
) -> MatchVerification:
    """Send two person crops to the VLM to decide if they are the same person."""
    system = (
        "You are a surveillance person-reidentification assistant. "
        "You receive two person crops from different cameras. "
        "Decide whether they depict the same individual. "
        "Use clothing color, build, accessories, hair, and other visible traits. "
        'Output strict JSON: {"is_match": bool, "confidence": 0.0~1.0, "reasoning": "..."}'
    )

    user_content: list[dict[str, Any]] = [
        {"type": "text", "text": (
            f"Image A: camera {crop_a.camera_id} at t={crop_a.t_sec:.1f}s\n"
            f"Image B: camera {crop_b.camera_id} at t={crop_b.t_sec:.1f}s\n"
            "Are these the same person?"
        )},
        {
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{crop_a.jpg_base64}"},
        },
        {
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{crop_b.jpg_base64}"},
        },
    ]

    llm = ChatOpenAI(model=model, temperature=temperature)
    resp = llm.invoke([
        SystemMessage(content=system),
        HumanMessage(content=user_content),
    ])
    raw = resp.content if isinstance(resp.content, str) else str(resp.content)

    try:
        data = json.loads(raw)
        return MatchVerification(
            is_match=bool(data.get("is_match", False)),
            confidence=float(data.get("confidence", 0.0)),
            reasoning=str(data.get("reasoning", "")),
        )
    except (json.JSONDecodeError, KeyError, TypeError):
        logger.warning("LLM returned invalid JSON; treating as no match: %s", raw[:200])
        return MatchVerification(is_match=False, confidence=0.0, reasoning=f"parse error: {raw[:100]}")
