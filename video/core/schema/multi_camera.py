"""Data structures for multi-camera cross-view person tracking."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class PersonCrop:
    """Single person crop image."""

    t_sec: float
    camera_id: str
    track_id: int
    image_array: np.ndarray
    jpg_base64: str


@dataclass
class CameraAppearance:
    """One appearance of a global entity on a camera."""

    camera_id: str
    track_id: int
    start_time: float
    end_time: float
    confidence: float


@dataclass
class GlobalEntity:
    """Merged global entity across cameras (same person)."""

    global_entity_id: str
    appearances: list[CameraAppearance] = field(default_factory=list)


@dataclass
class CameraResult:
    """Full Stage-1 result for one camera."""

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
    """Hyperparameters for cross-camera matching."""

    max_transition_sec: float = 30.0
    min_overlap_sec: float = 0.0
    embedding_threshold: float = 0.65
    llm_verify_top_k: int = 3
    person_only: bool = True
    # Same-camera fragment stitching
    same_camera_max_gap_sec: float = 3.0
    same_camera_reid_threshold: float = 0.80
    # Cross-camera combined score threshold
    cross_camera_min_score: float = 0.65
    # Trigger VLM only for borderline cosine
    llm_verify_cosine_min: float = 0.65
    llm_verify_cosine_max: float = 0.80


@dataclass
class MatchVerification:
    """Optional LLM verification result."""

    is_match: bool
    confidence: float
    reasoning: str


@dataclass
class MultiCameraOutput:
    """Final multi-camera pipeline output."""

    cameras: dict[str, str]
    config: CrossCameraConfig
    global_entities: list[GlobalEntity]
    per_camera: list[CameraResult]
    merged_events: list[dict[str, Any]] = field(default_factory=list)
