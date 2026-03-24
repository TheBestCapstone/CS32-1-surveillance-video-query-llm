"""读取 pipeline 产出的 JSON + 视频抽帧，调用 LLM 精炼并写回结果（无 argparse）。"""

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
    refine_events_with_llm,
    refine_vector_events_with_llm,
)
from video.core.schema.refined_event_llm import RefinedAllClipsPayload, RefinedEventsPayload, VectorEventsPayload


@dataclass
class RefineEventsConfig:
    mode: Literal["full", "vector"] = "vector"
    clip_index: int | None = None
    num_frames: int = 12
    model: str = "gpt-5.4-mini"
    temperature: float = 0.1
    max_time_adjust_sec: float = 0.5
    merge_location_iou_threshold: float = 0.9
    merge_center_dist_px: float = 30.0
    merge_location_norm_diff: float = 0.10


def run_refine_events_from_files(
    events_path: str | Path,
    clips_path: str | Path,
    config: RefineEventsConfig | None = None,
) -> Path:
    """
    对 *_events.json + *_clips.json 执行精炼，返回写入的输出文件路径。
    """
    cfg = config or RefineEventsConfig()
    events_path = Path(events_path)
    clips_path = Path(clips_path)

    events_data = json.loads(events_path.read_text(encoding="utf-8"))
    clips_data = json.loads(clips_path.read_text(encoding="utf-8"))

    video_path = events_data["meta"]["video_path"]
    vw, vh = get_video_size(video_path)
    raw_events = enrich_events_with_normalized_location(events_data["events"], vw, vh)

    clip_segments = clips_data.get("clip_segments", [])
    if not isinstance(clip_segments, list) or not clip_segments:
        raise RuntimeError("clips.json 中没有 clip_segments")

    if cfg.clip_index is None:
        indices = list(range(len(clip_segments)))
    else:
        if cfg.clip_index < 0 or cfg.clip_index >= len(clip_segments):
            raise ValueError(f"clip_index 超出范围：{cfg.clip_index} (0~{len(clip_segments)-1})")
        indices = [int(cfg.clip_index)]

    refined_list_full: list[RefinedEventsPayload] = []
    refined_list_vector: list[VectorEventsPayload] = []

    for idx in indices:
        clip = clip_segments[idx]
        clip_start = float(clip["start_sec"])
        clip_end = float(clip["end_sec"])
        clip_events = [
            e
            for e in raw_events
            if float(e.get("end_time", 0.0)) >= clip_start and float(e.get("start_time", 0.0)) <= clip_end
        ]
        if not clip_events:
            continue

        frames = sample_frames_uniform(
            video_path=video_path,
            start_sec=clip_start,
            end_sec=clip_end,
            num_frames=int(cfg.num_frames),
        )
        if not frames:
            raise RuntimeError(f"clip_index={idx} 未抽到任何帧，请检查 clip 时间段或视频路径")

        if cfg.mode == "full":
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
        if len(refined_list_full) == 1:
            out_path = events_path.with_name(events_path.stem + "_refined.json")
            out_path.write_text(refined_list_full[0].model_dump_json(indent=2, ensure_ascii=False), encoding="utf-8")
        else:
            out_path = events_path.with_name(events_path.stem + "_refined_all.json")
            payload = RefinedAllClipsPayload(video_path=video_path, clips=refined_list_full)
            out_path.write_text(payload.model_dump_json(indent=2, ensure_ascii=False), encoding="utf-8")
    else:
        flat_events: list[dict[str, Any]] = []
        for ve in refined_list_vector:
            for ev in ve.events:
                flat_events.append(ev.model_dump())

        out_path = events_path.with_name(events_path.stem + "_vector_flat.json")
        payload_flat = {
            "video_id": Path(video_path).name,
            "events": flat_events,
        }
        out_path.write_text(json.dumps(payload_flat, ensure_ascii=False, indent=2), encoding="utf-8")

    return out_path
