"""
历史命名保留：精炼相关类型与 runner 由此 re-export；CLI 实现位于 coordinator（惰性导入，避免拉取 YOLO/cv2）。

程序内请用：video.factory.coordinator.run_refine_events 或 refinement_runner.run_refine_events_from_files。
"""

from __future__ import annotations

from typing import Sequence

from video.factory.refinement_runner import RefineEventsConfig, run_refine_events_from_files


def cli_run_refine_events(argv: Sequence[str] | None = None) -> None:
    """转调 coordinator，仅在调用 CLI 时加载 coordinator（及其对 cv2 的间接依赖）。"""
    from video.factory.coordinator import cli_run_refine_events as _cli

    _cli(argv)


main = cli_run_refine_events

__all__ = [
    "RefineEventsConfig",
    "run_refine_events_from_files",
    "cli_run_refine_events",
    "main",
]


if __name__ == "__main__":
    cli_run_refine_events()
