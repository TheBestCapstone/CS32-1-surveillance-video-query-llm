"""
CLI 入口：加载 .env 后调用 video.factory.refinement_runner。
逻辑与 schema 分别在 refinement_runner / video.core.*，便于其它模块直接 import 调用。
"""

from __future__ import annotations

import argparse

from dotenv import load_dotenv

from video.factory.refinement_runner import RefineEventsConfig, run_refine_events_from_files

load_dotenv()


def main() -> None:
    parser = argparse.ArgumentParser(description="用 LangChain + ChatGPT 多模态纠错/细化 events")
    parser.add_argument("--events", required=True, help="*_events.json 路径")
    parser.add_argument("--clips", required=True, help="*_clips.json 路径")
    parser.add_argument(
        "--mode",
        type=str,
        default="vector",
        choices=["full", "vector"],
        help="输出模式：full=大结构；vector=上线最小检索事件(默认)",
    )
    parser.add_argument("--clip-index", type=int, default=None, help="仅处理某一个 clip 段")
    parser.add_argument("--num-frames", type=int, default=12, help="每段 clip 抽帧数量")
    parser.add_argument("--model", type=str, default="gpt-5.4-mini", help="OpenAI 多模态模型名")
    parser.add_argument("--temperature", type=float, default=0.1)
    parser.add_argument("--max-time-adjust-sec", type=float, default=0.5)
    parser.add_argument("--merge-location-iou", type=float, default=0.9)
    parser.add_argument("--merge-center-dist-px", type=float, default=30.0)
    parser.add_argument("--merge-location-norm-diff", type=float, default=0.10)
    args = parser.parse_args()

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
    )
    out_path = run_refine_events_from_files(args.events, args.clips, cfg)
    print(f"refined events saved to: {out_path}")


if __name__ == "__main__":
    main()
