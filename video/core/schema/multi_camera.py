"""多摄像头跨镜人物追踪的数据结构定义。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class PersonCrop:
    """单张人物裁剪图。"""

    t_sec: float
    camera_id: str
    track_id: int
    image_array: np.ndarray
    jpg_base64: str


@dataclass
class CameraAppearance:
    """某全局实体在某摄像头中的一次出现记录。"""

    camera_id: str
    track_id: int
    start_time: float
    end_time: float
    confidence: float


@dataclass
class GlobalEntity:
    """跨摄像头合并后的全局实体（同一个人）。"""

    global_entity_id: str
    appearances: list[CameraAppearance] = field(default_factory=list)


@dataclass
class CameraResult:
    """单路摄像头经过 Stage-1 处理后的完整结果。"""

    camera_id: str
    video_path: str
    tracks: list[dict[str, Any]]
    events: list[dict[str, Any]]
    clips: list[dict[str, float]]
    meta: dict[str, Any] = field(default_factory=dict)
    person_crops: dict[int, list[PersonCrop]] = field(default_factory=dict)
    person_embeddings: dict[int, np.ndarray] = field(default_factory=dict)


@dataclass
class CrossCameraConfig:
    """跨摄像头匹配超参数。"""

    max_transition_sec: float = 30.0
    min_overlap_sec: float = 0.0
    embedding_threshold: float = 0.65
    llm_verify_top_k: int = 3
    person_only: bool = True
    # 同摄像头碎片拼接
    same_camera_max_gap_sec: float = 3.0
    same_camera_reid_threshold: float = 0.80
    # 跨摄像头综合打分阈值
    cross_camera_min_score: float = 0.65
    # 只对边界相似度触发 VLM
    llm_verify_cosine_min: float = 0.65
    llm_verify_cosine_max: float = 0.80


@dataclass
class MatchVerification:
    """LLM 二次确认结果。"""

    is_match: bool
    confidence: float
    reasoning: str


@dataclass
class MultiCameraOutput:
    """多摄像头管线最终输出。"""

    cameras: dict[str, str]
    config: CrossCameraConfig
    global_entities: list[GlobalEntity]
    per_camera: list[CameraResult]
    merged_events: list[dict[str, Any]] = field(default_factory=list)
