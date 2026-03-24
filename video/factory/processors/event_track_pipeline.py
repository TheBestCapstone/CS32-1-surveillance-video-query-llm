"""
编排入口：串联 vision（检测跟踪）与 analyzer（事件切片），并写 JSON。
详细算法见 vision.py / analyzer.py。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from video.common.paths import pipeline_output_dir
from video.factory.processors.analyzer import aggregate_tracks, slice_events
from video.factory.processors.vision import resolve_model, run_yolo_track_on_video


def run_pipeline(
    video_path: str,
    model_path: str = "n",
    conf: float = 0.25,
    iou: float = 0.45,
    motion_threshold: float = 5.0,
    min_clip_duration: float = 1.0,
    max_static_duration: float = 30.0,
    motion_window_sec: float = 1.5,
    motion_window_sum_threshold: float = 20.0,
    motion_segment_pad_sec: float = 0.8,
    tracker: str = "botsort_reid",
    save_annotated_video: bool = False,
    annotated_video_path: str | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, float]], dict[str, Any]]:
    """主流程：读视频 → YOLO 跟踪 → 轨迹聚合 → 事件切片。"""
    model_resolved, _ = resolve_model(model_path)
    fps, total_frames, frame_detections, tracker_label = run_yolo_track_on_video(
        video_path,
        model_path=model_resolved,
        conf=conf,
        iou=iou,
        tracker=tracker,
        save_annotated_video=save_annotated_video,
        annotated_video_path=annotated_video_path,
    )
    tracks = aggregate_tracks(fps, frame_detections)
    events, clip_segments = slice_events(
        tracks,
        fps,
        frame_detections,
        motion_threshold=motion_threshold,
        min_clip_duration=min_clip_duration,
        max_static_duration=max_static_duration,
        motion_window_sec=motion_window_sec,
        motion_window_sum_threshold=motion_window_sum_threshold,
        motion_segment_pad_sec=motion_segment_pad_sec,
    )

    meta = {
        "video_path": str(Path(video_path).resolve()),
        "fps": fps,
        "total_frames": total_frames,
        "num_tracks": len(tracks),
        "num_events": len(events),
        "num_clips": len(clip_segments),
        "tracker": tracker_label,
        "model": model_resolved,
        "model_input": model_path.strip(),
        "conf": conf,
        "iou": iou,
    }
    return events, clip_segments, meta


def save_pipeline_output(
    events: list[dict[str, Any]],
    clip_segments: list[dict[str, float]],
    meta: dict[str, Any],
    out_dir: str | Path,
    base_name: str | None = None,
) -> tuple[Path, Path]:
    """将事件列表与 clip 时间段写入 JSON。返回 (events 路径, clips 路径)。"""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if base_name is None:
        base_name = Path(meta["video_path"]).stem

    events_path = out_dir / f"{base_name}_events.json"
    clips_path = out_dir / f"{base_name}_clips.json"

    payload_events = {"meta": meta, "events": events}
    with open(events_path, "w", encoding="utf-8") as f:
        json.dump(payload_events, f, ensure_ascii=False, indent=2)

    payload_clips = {"meta": meta, "clip_segments": clip_segments}
    with open(clips_path, "w", encoding="utf-8") as f:
        json.dump(payload_clips, f, ensure_ascii=False, indent=2)

    return events_path, clips_path


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="视频 → YOLO+跟踪 → 事件与 clip 时间段")
    parser.add_argument("video", nargs="?", default="VIRAT_S_000200_00_000100_000171.mp4", help="视频路径")
    parser.add_argument(
        "--tracker",
        type=str,
        default="botsort_reid",
        help="botsort_reid(默认 BoT-SORT+ReID) | botsort | bytetrack | 某.yaml 路径",
    )
    parser.add_argument("--model", "-m", type=str, default="n", help="YOLO 权重")
    parser.add_argument("--conf", type=float, default=0.25, help="检测置信度阈值")
    parser.add_argument("--iou", type=float, default=0.25, help="检测 NMS IoU 阈值")
    parser.add_argument("--save-video", action="store_true", help="输出带框+track_id 的标注视频")
    parser.add_argument("--save-video-path", type=str, default=None, help="标注视频输出路径")
    args = parser.parse_args()

    out_dir = pipeline_output_dir()
    print(
        f"正在运行: {args.video} | 模型={args.model} conf={args.conf} iou={args.iou} | tracker={args.tracker}"
    )
    events, clip_segments, meta = run_pipeline(
        args.video,
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

    events_path, clips_path = save_pipeline_output(events, clip_segments, meta, out_dir)
    print(f"元信息: {json.dumps(meta, ensure_ascii=False, indent=2)}")
    print(f"事件已保存: {events_path}，共 {len(events)} 条")
    print(f"Clip 段已保存: {clips_path}，共 {len(clip_segments)} 段")
    print("\n前 3 条事件:")
    print(json.dumps(events[:3], ensure_ascii=False, indent=2))
    print("\n前 5 段 clip (start_sec, end_sec):")
    print(json.dumps(clip_segments[:5], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
