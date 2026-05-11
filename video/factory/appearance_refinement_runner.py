"""Crop-based person appearance refinement for multi-camera pipeline output.

The output deliberately reuses the existing vector event fields so downstream
RAG/agent code can benefit from richer appearance text without a schema change.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from openai import OpenAI

from video.factory.person_crop_sampler import (
    sample_person_crops_for_appearances,
    sample_person_crops_from_events,
)

logger = logging.getLogger(__name__)


@dataclass
class AppearanceRefinementConfig:
    api_key: str = ""
    base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    model: str = "qwen-vl-max-latest"
    temperature: float = 0.0
    max_tokens: int = 180
    max_entities: int = 0
    max_apps_per_entity: int = 6
    crops_per_app: int = 1
    cache_path: Path | None = None
    force: bool = False

    @classmethod
    def from_env(cls, **overrides: Any) -> "AppearanceRefinementConfig":
        values = {
            "api_key": os.getenv("DASHSCOPE_API_KEY", ""),
            "base_url": os.getenv("DASHSCOPE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
            "model": os.getenv("DASHSCOPE_CHAT_MODEL", "qwen-vl-max-latest"),
        }
        values.update(overrides)
        return cls(**values)


def _fmt_sec(seconds: float) -> str:
    minutes, sec = divmod(int(seconds), 60)
    return f"{minutes}:{sec:02d}"


def _json_object_from_text(text: str) -> dict[str, Any]:
    raw = (text or "").strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
        raw = re.sub(r"\s*```$", "", raw)
    try:
        return json.loads(raw)
    except Exception:
        pass
    start = raw.find("{")
    end = raw.rfind("}")
    if start >= 0 and end > start:
        return json.loads(raw[start:end + 1])
    raise ValueError(f"No JSON object found in response: {text[:200]}")


def appearance_keywords_from_text(text: str) -> list[str]:
    tl = text.lower().replace("-", " ")
    terms = [
        "hoodie", "jacket", "coat", "shirt", "pants", "trousers", "jeans",
        "bag", "backpack", "handbag", "hat", "cap", "hood", "scarf", "fur",
        "collar", "white", "black", "grey", "gray", "dark", "light", "beige",
        "brown", "red", "blue", "green",
    ]
    out: list[str] = []
    seen: set[str] = set()

    def add(token: str) -> None:
        token = token.strip().lower().replace(" ", "_").replace("gray", "grey")
        if token and token != "unknown" and token not in seen:
            out.append(token)
            seen.add(token)

    for term in terms:
        if re.search(rf"\b{re.escape(term)}\b", tl):
            add(term)
    if ("light grey" in tl or "light gray" in tl) and "hoodie" in tl:
        add("light_grey_hoodie")
    if "beige" in tl and ("jacket" in tl or "coat" in tl):
        add("beige_jacket")
    if ("dark" in tl or "black" in tl) and "coat" in tl:
        add("dark_coat")
    if ("dark" in tl or "black" in tl) and "hood" in tl:
        add("hood_up")
    if "fur" in tl and ("hood" in tl or "collar" in tl):
        add("fur_trimmed_hood")
    return out[:12]


def color_from_appearance(text: str) -> str:
    tl = text.lower().replace("-", " ")
    for phrase, color in [
        ("light grey", "light_grey"),
        ("light gray", "light_grey"),
        ("dark grey", "dark_grey"),
        ("dark gray", "dark_grey"),
        ("silver grey", "silver_grey"),
        ("silver gray", "silver_grey"),
    ]:
        if phrase in tl:
            return color
    for color in ["beige", "white", "black", "grey", "gray", "dark", "light", "brown", "red", "blue", "green"]:
        if re.search(rf"\b{color}\b", tl):
            return "grey" if color == "gray" else color
    return "unknown"


def _call_appearance_vlm(
    client: OpenAI,
    crops_b64: list[str],
    entity_id: str,
    trajectory: str,
    config: AppearanceRefinementConfig,
) -> dict[str, Any]:
    user_content: list[dict[str, Any]] = [{
        "type": "text",
        "text": (
            "You are describing one tracked person for surveillance retrieval.\n"
            f"Entity: {entity_id}\n"
            f"Trajectory: {trajectory}\n\n"
            "Look only at the person in the provided crops. Return strict JSON with:\n"
            "{\n"
            '  "object_color": "dominant upper-body color or unknown",\n'
            '  "appearance_notes": "short English clothing summary, e.g. light grey hoodie, dark pants, medium build",\n'
            '  "keywords": ["retrieval", "tokens"]\n'
            "}\n"
            "Use concrete visible clothing words. If uncertain, say unknown for that part, "
            "but do not invent colors or clothing."
        ),
    }]
    for b64 in crops_b64:
        user_content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
        })

    resp = client.chat.completions.create(
        model=config.model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You produce compact person appearance metadata for RAG. "
                    "Return only valid JSON. Do not include markdown."
                ),
            },
            {"role": "user", "content": user_content},
        ],
        temperature=float(config.temperature),
        max_tokens=int(config.max_tokens),
    )
    parsed = _json_object_from_text(resp.choices[0].message.content or "{}")
    appearance = str(parsed.get("appearance_notes") or "").strip()
    color = str(parsed.get("object_color") or "").strip().lower().replace(" ", "_")
    if not color or color == "unknown":
        color = color_from_appearance(appearance)
    keywords = parsed.get("keywords") or []
    if not isinstance(keywords, list):
        keywords = []
    normalized = [str(k).strip().lower().replace(" ", "_") for k in keywords if str(k).strip()]
    for token in appearance_keywords_from_text(" ".join([appearance, color])):
        if token not in normalized:
            normalized.append(token)
    return {
        "object_color": color or "unknown",
        "appearance_notes": appearance or "unknown",
        "keywords": [k for k in normalized if k and k != "unknown"][:12],
    }


def merge_refined_appearance(base: dict[str, Any] | None, appearance: dict[str, Any] | None) -> dict[str, Any]:
    """Append appearance-refined events to a clip-refined result."""
    if not base:
        return appearance or {}
    if not appearance:
        return base
    merged = json.loads(json.dumps(base))
    merged.setdefault("per_camera", {})
    for cam_id, cam_data in appearance.get("per_camera", {}).items():
        dst = merged["per_camera"].setdefault(cam_id, {"events": []})
        dst.setdefault("events", [])
        dst["events"].extend(cam_data.get("events", []))
    return merged


def _person_events_by_track(events: list[dict[str, Any]]) -> dict[int, list[dict[str, Any]]]:
    by_track: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        obj = str(event.get("class_name") or event.get("object_type") or "").lower()
        if obj not in {"person", "people", "pedestrian"}:
            continue
        tid = event.get("track_id")
        if tid is None:
            continue
        try:
            by_track[int(tid)].append(event)
        except Exception:
            continue
    return by_track


def run_appearance_refinement_for_events(
    *,
    video_path: str | Path,
    events: list[dict[str, Any]],
    video_id: str | None = None,
    camera_id: str | None = None,
    config: AppearanceRefinementConfig | None = None,
) -> dict[str, Any]:
    """Run crop-based appearance refinement for one camera/video.

    The returned payload is vector-refinement shaped::

        {"video_id": "...", "events": [...]}

    Each output event represents one person track and uses existing fields only,
    with ``entity_hint`` set to ``track_<id>``.
    """
    cfg = config or AppearanceRefinementConfig.from_env()
    if cfg.cache_path and cfg.cache_path.exists() and not cfg.force:
        logger.info("Loading cached single-camera appearance refinement from %s", cfg.cache_path)
        return json.loads(cfg.cache_path.read_text(encoding="utf-8"))
    if not cfg.api_key:
        raise RuntimeError("DASHSCOPE_API_KEY is required for appearance refinement")

    video_path = Path(video_path)
    out_video_id = video_id or video_path.name
    by_track = _person_events_by_track(events)
    track_items = sorted(
        by_track.items(),
        key=lambda item: min(float(e.get("start_time", 0.0)) for e in item[1]),
    )
    if cfg.max_entities > 0:
        track_items = track_items[:cfg.max_entities]

    client = OpenAI(api_key=cfg.api_key, base_url=cfg.base_url)
    refined_events: list[dict[str, Any]] = []
    t0 = time.time()

    for tid, track_events in track_items:
        crops = sample_person_crops_from_events(
            video_path,
            track_events,
            max_tracks=1,
            crops_per_track=max(1, cfg.crops_per_app),
        )
        if not crops:
            continue

        start = min(float(e.get("start_time", 0.0)) for e in track_events)
        end = max(float(e.get("end_time", start)) for e in track_events)
        entity_id = f"track_{tid}"
        trajectory = f"{camera_id or 'camera'} track#{tid} {_fmt_sec(start)}-{_fmt_sec(end)}"

        try:
            appearance = _call_appearance_vlm(client, crops, entity_id, trajectory, cfg)
        except Exception as exc:
            logger.warning("appearance refine failed for track_%s: %s", tid, exc)
            continue

        keywords = list(appearance["keywords"])
        for token in ("person", "appearance", entity_id):
            if token not in keywords:
                keywords.append(token)
        notes = appearance["appearance_notes"]
        event_text = (
            f"{entity_id} appeared in {camera_id or out_video_id} from "
            f"{_fmt_sec(start)} to {_fmt_sec(end)}. Appearance: {notes}."
        )
        refined_events.append({
            "video_id": out_video_id,
            "camera_id": camera_id,
            "track_id": tid,
            "entity_hint": entity_id,
            "clip_start_sec": start,
            "clip_end_sec": end,
            "start_time": start,
            "end_time": end,
            "object_type": "person",
            "object_color": appearance["object_color"],
            "appearance_notes": notes,
            "scene_zone": "unknown",
            "event_text": event_text,
            "keywords": keywords[:14],
            "start_bbox_xyxy": None,
            "end_bbox_xyxy": None,
        })

    result = {
        "video_id": out_video_id,
        "camera_id": camera_id,
        "elapsed_sec": round(time.time() - t0, 1),
        "events": sorted(refined_events, key=lambda e: float(e.get("start_time", 0.0))),
    }
    if cfg.cache_path:
        cfg.cache_path.parent.mkdir(parents=True, exist_ok=True)
        cfg.cache_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def run_appearance_refinement_for_pipeline(
    *,
    slot: str,
    pipeline: dict[str, Any],
    camera_to_video: dict[str, str | Path],
    camera_video_stems: dict[str, str] | None = None,
    config: AppearanceRefinementConfig | None = None,
) -> dict[str, Any]:
    """Run crop-based appearance refinement for all global person entities."""
    cfg = config or AppearanceRefinementConfig.from_env()
    if cfg.cache_path and cfg.cache_path.exists() and not cfg.force:
        logger.info("[%s] Loading cached appearance refinement from %s", slot, cfg.cache_path)
        return json.loads(cfg.cache_path.read_text(encoding="utf-8"))
    if not cfg.api_key:
        raise RuntimeError("DASHSCOPE_API_KEY is required for appearance refinement")

    per_cam = {
        cr.get("camera_id"): cr
        for cr in pipeline.get("per_camera", [])
        if cr.get("camera_id")
    }
    camera_to_events = {
        str(cam_id): list(cam_data.get("events", []))
        for cam_id, cam_data in per_cam.items()
    }
    client = OpenAI(api_key=cfg.api_key, base_url=cfg.base_url)
    per_cam_events: dict[str, list[dict[str, Any]]] = defaultdict(list)
    entities = list(pipeline.get("global_entities", []))
    if cfg.max_entities > 0:
        entities = entities[:cfg.max_entities]

    t0 = time.time()
    for ge in entities:
        entity_id = str(ge.get("global_entity_id") or "")
        apps = sorted(ge.get("appearances", []), key=lambda a: float(a.get("start_time", 0.0)))
        if not entity_id or not apps:
            continue

        trajectory = " -> ".join(
            f"{a.get('camera_id')} track#{a.get('track_id')} "
            f"{_fmt_sec(float(a.get('start_time', 0.0)))}-{_fmt_sec(float(a.get('end_time', 0.0)))}"
            for a in apps
        )
        crops = sample_person_crops_for_appearances(
            camera_to_video=camera_to_video,
            camera_to_events=camera_to_events,
            appearances=apps,
            max_apps=cfg.max_apps_per_entity,
            crops_per_app=cfg.crops_per_app,
        )
        if not crops:
            continue
        try:
            appearance = _call_appearance_vlm(client, crops, entity_id, trajectory, cfg)
        except Exception as exc:
            logger.warning("[%s] appearance refine failed for %s: %s", slot, entity_id, exc)
            continue

        color = appearance["object_color"]
        notes = appearance["appearance_notes"]
        keywords = list(appearance["keywords"])
        for token in ("person", "appearance", "cross_camera", "same_person", entity_id.lower()):
            if token not in keywords:
                keywords.append(token)
        event_text = (
            f"{entity_id} appeared across cameras: {trajectory}. "
            f"Appearance: {notes}."
        )
        for app in apps:
            cam_id = str(app.get("camera_id") or "")
            if not cam_id:
                continue
            per_cam_events[cam_id].append({
                "video_id": (camera_video_stems or {}).get(cam_id, ""),
                "camera_id": cam_id,
                "track_id": app.get("track_id"),
                "entity_hint": entity_id,
                "clip_start_sec": float(app.get("start_time", 0.0)),
                "clip_end_sec": float(app.get("end_time", 0.0)),
                "start_time": float(app.get("start_time", 0.0)),
                "end_time": float(app.get("end_time", 0.0)),
                "object_type": "person",
                "object_color": color,
                "appearance_notes": notes,
                "scene_zone": "unknown",
                "event_text": event_text,
                "keywords": keywords[:14],
                "start_bbox_xyxy": None,
                "end_bbox_xyxy": None,
            })

    result = {
        "slot": slot,
        "elapsed_sec": round(time.time() - t0, 1),
        "per_camera": {
            cam_id: {"events": sorted(events, key=lambda e: float(e.get("start_time", 0.0)))}
            for cam_id, events in per_cam_events.items()
        },
    }
    if cfg.cache_path:
        cfg.cache_path.parent.mkdir(parents=True, exist_ok=True)
        cfg.cache_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result
