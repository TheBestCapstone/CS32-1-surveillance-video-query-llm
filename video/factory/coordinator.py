"""
离线流水线编排：视频 → 事件/clip JSON → LLM 精炼。

- 程序内调用：run_video_to_events、run_refine_events
- 入库 / JSON：video.factory.pipeline_outputs（或本模块 re-export）中 video_events_as_json_dicts、refined_events_as_dict 等
- 命令行：cli_run_video_events、cli_run_refine_events，或 python -m video.factory.coordinator video|refine ...
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

from video.common.paths import pipeline_output_dir
from video.factory.pipeline_outputs import (
    refined_events_as_dict,
    refined_events_as_json_str,
    refined_events_from_json_files_as_dict,
    video_events_as_json_dicts,
    video_events_as_json_strings,
)
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


def _add_video_cli_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("video", nargs="?", default="VIRAT_S_000200_00_000100_000171.mp4", help="视频路径")
    p.add_argument(
        "--out-dir",
        type=str,
        default=None,
        help="输出目录（默认：仓库根下 pipeline_output/）",
    )
    p.add_argument(
        "--tracker",
        type=str,
        default="botsort_reid",
        help="botsort_reid | botsort | bytetrack | 某.yaml 路径",
    )
    p.add_argument("--model", "-m", type=str, default="11m", help="YOLO 权重（默认 yolo11m，存放于 _model/）")
    p.add_argument("--conf", type=float, default=0.25, help="检测置信度阈值")
    p.add_argument("--iou", type=float, default=0.25, help="检测 NMS IoU 阈值")
    p.add_argument("--save-video", action="store_true", help="输出带框+track_id 的标注视频")
    p.add_argument("--save-video-path", type=str, default=None, help="标注视频输出路径")


def _run_video_cli_namespace(args: argparse.Namespace) -> None:
    out = Path(args.out_dir) if args.out_dir else pipeline_output_dir()
    print(
        f"正在运行: {args.video} | 模型={args.model} conf={args.conf} iou={args.iou} | tracker={args.tracker}"
    )
    events, clip_segments, meta, paths = run_video_to_events(
        args.video,
        out_dir=out,
        save=True,
        model_path=args.model,
        conf=args.conf,
        iou=args.iou,
        motion_threshold=5.0,
        min_clip_duration=1.0,
        max_static_duration=30.0,
        tracker=args.tracker,
        save_annotated_video=bool(args.save_video),
        annotated_video_path=args.save_video_path,
    )
    assert paths is not None
    events_path, clips_path = paths
    print(f"元信息: {json.dumps(meta, ensure_ascii=False, indent=2)}")
    print(f"事件已保存: {events_path}，共 {len(events)} 条")
    print(f"Clip 段已保存: {clips_path}，共 {len(clip_segments)} 段")
    print("\n前 3 条事件:")
    print(json.dumps(events[:3], ensure_ascii=False, indent=2))
    print("\n前 5 段 clip (start_sec, end_sec):")
    print(json.dumps(clip_segments[:5], ensure_ascii=False, indent=2))


def cli_run_video_events(argv: Sequence[str] | None = None) -> None:
    """命令行：等价于原 pipeline_video_events.py（参数与以前一致，并支持 --out-dir）。"""
    parser = argparse.ArgumentParser(description="视频 → YOLO+跟踪 → 事件与 clip 时间段")
    _add_video_cli_args(parser)
    args = parser.parse_args(list(argv) if argv is not None else None)
    _run_video_cli_namespace(args)


def _add_refine_cli_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--events", required=True, help="*_events.json 路径")
    p.add_argument("--clips", required=True, help="*_clips.json 路径")
    p.add_argument(
        "--mode",
        type=str,
        default="vector",
        choices=["full", "vector"],
        help="full=大结构；vector=上线最小检索事件(默认)",
    )
    p.add_argument("--clip-index", type=int, default=None, help="仅处理某一个 clip 段")
    p.add_argument("--num-frames", type=int, default=12, help="每段 clip 抽帧数量")
    p.add_argument("--model", type=str, default="gpt-5.4-mini", help="OpenAI 多模态模型名")
    p.add_argument("--temperature", type=float, default=0.1)
    p.add_argument("--max-time-adjust-sec", type=float, default=0.5)
    p.add_argument("--merge-location-iou", type=float, default=0.9)
    p.add_argument("--merge-center-dist-px", type=float, default=30.0)
    p.add_argument("--merge-location-norm-diff", type=float, default=0.10)
    p.add_argument("--min-event-duration-sec", type=float, default=1.0, help="过滤短事件：小于该时长(秒)不送入 LLM")


def _run_refine_cli_namespace(args: argparse.Namespace) -> None:
    from dotenv import load_dotenv

    load_dotenv()
    cfg = RefineEventsConfig(
        mode=args.mode,
        clip_index=args.clip_index,
        num_frames=int(args.num_frames),
        model=args.model,
        temperature=float(args.temperature),
        max_time_adjust_sec=float(args.max_time_adjust_sec),
        merge_location_iou_threshold=float(args.merge_location_iou),
        merge_center_dist_px=float(args.merge_center_dist_px),
        merge_location_norm_diff=float(args.merge_location_norm_diff),
        min_event_duration_sec=float(args.min_event_duration_sec),
    )
    out_path = run_refine_events_from_files(args.events, args.clips, cfg)
    print(f"refined events saved to: {out_path}")


def cli_run_refine_events(argv: Sequence[str] | None = None) -> None:
    """命令行：等价于原 langchain_refine_events.py（会先 load_dotenv）。"""
    parser = argparse.ArgumentParser(description="LangChain + ChatGPT 多模态纠错/细化 events")
    _add_refine_cli_args(parser)
    args = parser.parse_args(list(argv) if argv is not None else None)
    _run_refine_cli_namespace(args)


def main(argv: Sequence[str] | None = None) -> None:
    """统一入口：python -m video.factory.coordinator video ... | refine ..."""
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(description="离线视频流水线：video（跟踪+事件）或 refine（LLM）")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_v = sub.add_parser("video", help="YOLO+跟踪 → 事件与 clips JSON")
    _add_video_cli_args(p_v)
    p_r = sub.add_parser("refine", help="精炼 *_events.json + *_clips.json")
    _add_refine_cli_args(p_r)
    args = parser.parse_args(argv)
    if args.cmd == "video":
        _run_video_cli_namespace(args)
    else:
        _run_refine_cli_namespace(args)


if __name__ == "__main__":
    main()
