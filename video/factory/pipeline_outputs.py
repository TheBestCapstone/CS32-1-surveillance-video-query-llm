"""
供入库 / API 使用：返回与落盘 JSON 结构一致的 dict，或 JSON 字符串。

不自动写文件；写盘仍用 coordinator.run_video_to_events(save=True) 或 run_refine_events_from_files。

精炼相关 API 在函数内部再 import refinement_runner，便于仅调用 video_events_as_* 时不拉取 LangChain/OpenAI。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from video.factory.refinement_runner import RefineEventsConfig


def video_events_as_json_dicts(
    video_path: str,
    *,
    _run_pipeline: Callable[..., tuple[list[dict[str, Any]], list[dict[str, float]], dict[str, Any]]]
    | None = None,
    **run_kwargs: Any,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    跑 YOLO+跟踪+切片，返回两个与 *_events.json / *_clips.json 内容一致的字典。

    返回: (events_document, clips_document)，可直接写入 DB 或 json.dumps。

    _run_pipeline: 仅测试注入；默认使用 event_track_pipeline.run_pipeline。
    """
    if _run_pipeline is None:
        from video.factory.processors.event_track_pipeline import run_pipeline as _run_pipeline

    events, clip_segments, meta = _run_pipeline(video_path, **run_kwargs)
    events_document = {"meta": meta, "events": events}
    clips_document = {"meta": meta, "clip_segments": clip_segments}
    return events_document, clips_document


def video_events_as_json_strings(
    video_path: str,
    *,
    indent: int | None = 2,
    _run_pipeline: Callable[..., tuple[list[dict[str, Any]], list[dict[str, float]], dict[str, Any]]]
    | None = None,
    **run_kwargs: Any,
) -> tuple[str, str]:
    """同上，但返回 UTF-8 JSON 字符串（indent=None 则紧凑）。"""
    ev, cl = video_events_as_json_dicts(video_path, _run_pipeline=_run_pipeline, **run_kwargs)
    dump_kw: dict[str, Any] = {"ensure_ascii": False}
    if indent is not None:
        dump_kw["indent"] = indent
    return json.dumps(ev, **dump_kw), json.dumps(cl, **dump_kw)


def refined_events_as_dict(
    events_document: dict[str, Any],
    clips_document: dict[str, Any],
    config: RefineEventsConfig | None = None,
) -> dict[str, Any]:
    """
    基于内存中的 pipeline 文档做 LLM 精炼，返回与写盘 JSON 一致的字典。

    events_document / clips_document 结构同 video_events_as_json_dicts 的返回值。
    """
    from video.factory.refinement_runner import run_refine_events_to_dict

    return run_refine_events_to_dict(events_document, clips_document, config)


def refined_events_as_json_str(
    events_document: dict[str, Any],
    clips_document: dict[str, Any],
    config: RefineEventsConfig | None = None,
    *,
    indent: int | None = 2,
) -> str:
    """精炼结果的单文件 JSON 字符串（vector 模式为扁平 events；full 模式为一大块 schema）。"""
    payload = refined_events_as_dict(events_document, clips_document, config)
    dump_kw: dict[str, Any] = {"ensure_ascii": False}
    if indent is not None:
        dump_kw["indent"] = indent
    return json.dumps(payload, **dump_kw)


def refined_events_from_json_files_as_dict(
    events_path: str | Path,
    clips_path: str | Path,
    config: RefineEventsConfig | None = None,
) -> dict[str, Any]:
    """从磁盘读取 pipeline 产物 JSON，精炼后返回 dict（不写回文件）。"""
    events_path = Path(events_path)
    clips_path = Path(clips_path)
    events_data = json.loads(events_path.read_text(encoding="utf-8"))
    clips_data = json.loads(clips_path.read_text(encoding="utf-8"))
    return refined_events_as_dict(events_data, clips_data, config)
