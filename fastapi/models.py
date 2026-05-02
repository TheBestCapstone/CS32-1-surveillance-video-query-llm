from typing import Any, Literal

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, description="User query text.")
    thread_id: str | None = Field(default=None, description="Optional thread id for LangGraph state.")
    user_id: str = Field(default="fastapi-user", description="User id passed to graph config.")
    include_rows: bool = Field(default=False, description="Whether to include retrieved rows in the response.")
    include_node_trace: bool = Field(default=True, description="Whether to include executed node trace.")
    top_k_rows: int = Field(default=5, ge=1, le=20, description="Maximum retrieved rows returned to client.")


class QueryResponse(BaseModel):
    query: str
    answer: str
    final_answer: str
    raw_final_answer: str
    thread_id: str
    user_id: str
    elapsed_ms: float
    answer_type: str
    node_trace: list[str] = Field(default_factory=list)
    citations: list[dict[str, Any]] = Field(default_factory=list)
    verifier_result: dict[str, Any] = Field(default_factory=dict)
    classification_result: dict[str, Any] = Field(default_factory=dict)
    routing_metrics: dict[str, Any] = Field(default_factory=dict)
    fusion_meta: dict[str, Any] = Field(default_factory=dict)
    rows: list[dict[str, Any]] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str
    graph_ready: bool
    execution_mode: str
    sqlite_path: str
    chroma_path: str
    chroma_namespace: str
    chroma_child_collection: str
    chroma_parent_collection: str
    chroma_event_collection: str
    selected_database_id: str | None = None
    database_selected: bool = False


class VideoArtifactResponse(BaseModel):
    filename: str
    uploaded_video_path: str
    events_json_path: str
    clips_json_path: str
    refined_json_path: str | None = None
    db_seed_path: str | None = None


class DatabaseImportResponse(BaseModel):
    sqlite: dict[str, Any] = Field(default_factory=dict)
    chroma: dict[str, Any] = Field(default_factory=dict)


class DatabaseOptionResponse(BaseModel):
    id: str
    label: str
    sqlite_path: str
    chroma_path: str
    chroma_namespace: str
    source: Literal["uploaded", "configured"]
    selected: bool = False


class VideoUploadResponse(BaseModel):
    status: str
    job_id: str
    filename: str
    filenames: list[str] = Field(default_factory=list)
    file_count: int
    refine_mode: Literal["none", "vector", "full"]
    imported_to_db: bool
    pipeline_meta: dict[str, Any] = Field(default_factory=dict)
    events_count: int
    clip_count: int
    artifacts: list[VideoArtifactResponse] = Field(default_factory=list)
    database_import: DatabaseImportResponse | None = None
    selected_database: DatabaseOptionResponse | None = None


class DatabaseListResponse(BaseModel):
    databases: list[DatabaseOptionResponse] = Field(default_factory=list)


class DatabaseSelectionRequest(BaseModel):
    database_id: str = Field(..., min_length=1)


class DatabaseSelectionResponse(BaseModel):
    status: str
    selected_database: DatabaseOptionResponse


class CurrentDatabaseResponse(BaseModel):
    selected_database: DatabaseOptionResponse | None = None
    database_selected: bool = False
