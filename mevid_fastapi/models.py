"""Pydantic models for mevid_fastapi."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


# ── Ingest ────────────────────────────────────────────────────────────────────

class IngestFromSeedsRequest(BaseModel):
    seeds_dir: str = Field(..., description="事先生成好的 events_vector_flat 目录（绝对路径）")
    namespace: str = Field("mevid", description="Chroma 命名空间前缀")
    reset_existing: bool = Field(True, description="是否重建已有数据库")


class IngestFromVideosRequest(BaseModel):
    camera_videos: dict[str, str] = Field(
        ...,
        description='摄像头ID → 视频绝对路径，如 {"G329": "/data/G329.avi", ...}',
    )
    namespace: str = Field("mevid", description="Chroma 命名空间前缀")
    conf: float = Field(0.40, description="YOLO 检测置信度")
    iou: float = Field(0.40, description="YOLO 追踪 IoU")
    reid_device: str = Field("cpu", description="Re-ID 设备 (cpu/cuda)")
    refine: bool = Field(False, description="是否调用 LLM 事件细化")
    refine_model: str = Field("qwen-vl-max", description="LLM 细化模型名")
    reset_existing: bool = Field(True)


class IngestResult(BaseModel):
    status: str
    namespace: str
    sqlite_path: str
    chroma_path: str
    seed_file_count: int
    sqlite_rows: int
    chroma_child_records: int
    chroma_ge_records: int
    elapsed_ms: float


# ── Database ──────────────────────────────────────────────────────────────────

class DatabaseInfo(BaseModel):
    namespace: str
    sqlite_path: str
    chroma_path: str
    selected: bool = False


class SelectDatabaseRequest(BaseModel):
    namespace: str
    sqlite_path: str
    chroma_path: str


# ── Agent ─────────────────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    query: str
    thread_id: str | None = None
    user_id: str = "mevid_user"
    include_rows: bool = False
    include_node_trace: bool = True
    top_k_rows: int = 5


class QueryResponse(BaseModel):
    query: str
    answer: str
    answer_type: str = ""
    node_trace: list[str] = []
    elapsed_ms: float = 0.0
    verifier_result: dict[str, Any] = {}
    rows: list[dict[str, Any]] = []


# ── Eval ──────────────────────────────────────────────────────────────────────

class EvalRunRequest(BaseModel):
    questions_file: str | None = Field(
        None,
        description="sampled JSON 文件路径；None 时使用内置 sampled_10.json",
    )
    video_dir: str | None = Field(
        None,
        description="视频目录（用于 IoU 计算中的时间解析），可为空",
    )


class EvalCaseResult(BaseModel):
    case_id: str
    category: str
    question: str
    expected: str
    predicted: str
    correct: bool
    top_hit: bool
    iou: float
    elapsed_ms: float


class EvalSummary(BaseModel):
    total: int
    correct: int
    accuracy: float
    top_hit_total: int
    top_hit_rate: float
    mean_iou: float
    iou_threshold: float = 0.15
    n_iou_pass: int = 0
    iou_pass_rate: float = 0.0
    individual_iou: list[float] = []
    by_category: dict[str, dict[str, Any]]
    cases: list[EvalCaseResult]
    elapsed_total_ms: float


# ── Health ────────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    database_selected: bool
    sqlite_path: str
    chroma_path: str
    namespace: str
