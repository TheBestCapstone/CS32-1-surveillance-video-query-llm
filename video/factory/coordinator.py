"""
离线流水线编排：视频 → 事件/clip JSON →（可选）LLM 精炼。
供业务代码单点 import，无需关心 processors 内部文件名。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from video.common.paths import pipeline_output_dir
from video.factory.processors.event_track_pipeline import run_pipeline, save_pipeline_output
from video.factory.refinement_runner import RefineEventsConfig, run_refine_events_from_files


def run_video_to_events(
    video_path: str,
    out_dir: str | Path | None = None,
    save: bool = True,
    **run_kwargs: Any,
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, float]],
    dict[str, Any],
    tuple[Path, Path] | None,
]:
    """
    跑完整跟踪+事件切片。save=True 时写入 *_events.json / *_clips.json；
    out_dir 缺省则使用仓库根下 pipeline_output/。

    返回: (events, clip_segments, meta, saved_paths 或 None)
    """
    events, clip_segments, meta = run_pipeline(video_path, **run_kwargs)
    saved: tuple[Path, Path] | None = None
    if save:
        od = Path(out_dir) if out_dir is not None else pipeline_output_dir()
        saved = save_pipeline_output(events, clip_segments, meta, od)
    return events, clip_segments, meta, saved


def run_refine_events(
    events_json: str | Path,
    clips_json: str | Path,
    config: RefineEventsConfig | None = None,
) -> Path:
    """对 pipeline 产物做 LLM 精炼，返回输出 JSON 路径。"""
    return run_refine_events_from_files(events_json, clips_json, config)
