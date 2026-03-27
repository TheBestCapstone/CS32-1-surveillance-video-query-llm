"""仓库根目录与约定路径（config、默认输出目录等）。"""

from pathlib import Path


def repo_root() -> Path:
    """本文件位于 video/common/paths.py，向上两级为仓库根。"""
    return Path(__file__).resolve().parents[2]


def botsort_reid_config_path() -> Path:
    return repo_root() / "config" / "trackers" / "botsort_reid.yaml"


def pipeline_output_dir() -> Path:
    return repo_root() / "pipeline_output"
