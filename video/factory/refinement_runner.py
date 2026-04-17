"""Load pipeline JSON + sample frames and call LLM refinement; supports in-memory dict or file output."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from video.common.frames import (
    enrich_events_with_normalized_location,
    get_video_size,
    sample_frames_uniform,
)
from video.core.models.event_refinement_llm import (
    build_entities_with_hard_constraints,
    refine_events_with_llm,
    refine_vector_events_with_llm,
)
from video.core.schema.refined_event_llm import RefinedAllClipsPayload, RefinedEventsPayload, VectorEventsPayload


@dataclass
class RefineEventsConfig:
    mode: Literal["full", "vector"] = "vector"
    clip_index: int | None = None
    # Adaptive sampling: prefer frames_per_sec from clip duration
    # If num_frames > 0, use fixed count (backward compatible)
    num_frames: int = 0            # 0 = adaptive
    frames_per_sec: float = 0.1   # adaptive: frames per second (default ~1 frame / 10s)
    min_frames: int = 6
    max_frames: int = 48           # cap LLM token cost
    model: str = "gpt-5.4-mini"
    temperature: float = 0.1
    max_time_adjust_sec: float = 0.5
    merge_location_iou_threshold: float = 0.9
    merge_center_dist_px: float = 30.0
    merge_location_norm_diff: float = 0.10
    min_event_duration_sec: float = 1.0
    # Entity merge hard constraints (on by default)
    entity_merge_max_gap_sec: float = 300.0
    entity_merge_min_llm_confidence: float = 0.75

    def compute_num_frames(self, clip_duration_sec: float) -> int:
        """Compute sample count from clip duration."""
        if self.num_frames > 0:
            # fixed count (backward compatible)
            return int(self.num_frames)
        adaptive = round(clip_duration_sec * self.frames_per_sec)
        return max(self.min_frames, min(self.max_frames, adaptive))


def run_refine_events_to_dict(
    events_data: dict[str, Any],
    clips_data: dict[str, Any],
    config: RefineEventsConfig | None = None,
) -> dict[str, Any]:
    """
    Run refinement in memory; returns the same dict shape as written JSON (ready for json.dumps).

    events_data / clips_data match *_events.json and *_clips.json.
    """
    cfg = config or RefineEventsConfig()
    video_path = events_data["meta"]["video_path"]
    vw, vh = get_video_size(video_path)
    raw_events = enrich_events_with_normalized_location(events_data["events"], vw, vh)

    clip_segments = clips_data.get("clip_segments", [])
    if not isinstance(clip_segments, list) or not clip_segments:
        raise RuntimeError("clips.json has no clip_segments")

    if cfg.clip_index is None:
        indices = list(range(len(clip_segments)))
    else:
        if cfg.clip_index < 0 or cfg.clip_index >= len(clip_segments):
            raise ValueError(f"clip_index out of range: {cfg.clip_index} (valid 0..{len(clip_segments)-1})")
        indices = [int(cfg.clip_index)]

    refined_list_full: list[RefinedEventsPayload] = []
    refined_list_vector: list[VectorEventsPayload] = []

    for idx in indices:
        clip = clip_segments[idx]
        clip_start = float(clip["start_sec"])
        clip_end = float(clip["end_sec"])
        clip_events = []
        for e in raw_events:
            s = float(e.get("start_time", 0.0))
            t = float(e.get("end_time", 0.0))
            if t < clip_start or s > clip_end:
                continue
            if (t - s) < float(cfg.min_event_duration_sec):
                continue
            clip_events.append(e)
        if not clip_events:
            continue

        clip_duration = clip_end - clip_start
        n_frames = cfg.compute_num_frames(clip_duration)
        frames = sample_frames_uniform(
            video_path=video_path,
            start_sec=clip_start,
            end_sec=clip_end,
            num_frames=n_frames,
        )
        if not frames:
            raise RuntimeError(f"clip_index={idx}: no frames sampled; check clip range or video path")

        if cfg.mode == "full":
            pre_entities = build_entities_with_hard_constraints(
                video_path=video_path,
                raw_events=clip_events,
                model=cfg.model,
                max_gap_sec=float(cfg.entity_merge_max_gap_sec),
                min_llm_confidence=float(cfg.entity_merge_min_llm_confidence),
            )
            refined_list_full.append(
                refine_events_with_llm(
                    video_path=video_path,
                    clip={"start_sec": clip_start, "end_sec": clip_end},
                    raw_events=clip_events,
                    frames=frames,
                    model=cfg.model,
                    temperature=float(cfg.temperature),
                    max_time_adjust_sec=float(cfg.max_time_adjust_sec),
                    merge_location_iou_threshold=float(cfg.merge_location_iou_threshold),
                    merge_center_dist_px=float(cfg.merge_center_dist_px),
                    merge_location_norm_diff=float(cfg.merge_location_norm_diff),
                    pre_entities=pre_entities,
                )
            )
        else:
            refined_list_vector.append(
                refine_vector_events_with_llm(
                    video_id=Path(video_path).name,
                    clip={"start_sec": clip_start, "end_sec": clip_end},
                    raw_events=clip_events,
                    frames=frames,
                    model=cfg.model,
                    temperature=float(cfg.temperature),
                )
            )

    if cfg.mode == "full":
        if not refined_list_full:
            return {"video_path": str(video_path), "mode": "full"}
        if len(refined_list_full) == 1:
            return refined_list_full[0].model_dump()
        return RefinedAllClipsPayload(video_path=str(video_path), clips=refined_list_full).model_dump()

    flat_events: list[dict[str, Any]] = []
    for ve in refined_list_vector:
        for ev in ve.events:
            flat_events.append(ev.model_dump())

    return {
        "video_id": Path(video_path).name,
        "events": flat_events,
    }


def run_refine_events_from_files(
    events_path: str | Path,
    clips_path: str | Path,
    config: RefineEventsConfig | None = None,
) -> Path:
    """Refine *_events.json + *_clips.json; write output and return path."""
    cfg = config or RefineEventsConfig()
    events_path = Path(events_path)
    clips_path = Path(clips_path)

    events_data = json.loads(events_path.read_text(encoding="utf-8"))
    clips_data = json.loads(clips_path.read_text(encoding="utf-8"))
    out_dict = run_refine_events_to_dict(events_data, clips_data, cfg)
    text = json.dumps(out_dict, ensure_ascii=False, indent=2)

    if cfg.mode == "vector":
        out_path = events_path.with_name(events_path.stem + "_vector_flat.json")
    elif out_dict.get("mode") == "full" and "refined_events" not in out_dict and "clips" not in out_dict:
        out_path = events_path.with_name(events_path.stem + "_refined_empty.json")
    elif isinstance(out_dict.get("clips"), list) and len(out_dict["clips"]) > 1:
        out_path = events_path.with_name(events_path.stem + "_refined_all.json")
    else:
        out_path = events_path.with_name(events_path.stem + "_refined.json")

    out_path.write_text(text, encoding="utf-8")
    return out_path
