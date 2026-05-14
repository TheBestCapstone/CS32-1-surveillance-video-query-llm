"""MEVID FastAPI — video pipeline + agent pipeline unified service."""
from __future__ import annotations

import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_AGENT_ROOT = _PROJECT_ROOT / "agent"
for _p in (str(_PROJECT_ROOT), str(_AGENT_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from models import (  # noqa: E402
    EvalRunRequest,
    EvalSummary,
    EvalCaseResult,
    HealthResponse,
    IngestFromSeedsRequest,
    IngestFromVideosRequest,
    IngestResult,
    QueryRequest,
    QueryResponse,
    SelectDatabaseRequest,
)
from service import agent_service  # noqa: E402
import pipeline_service  # noqa: E402
import eval_service  # noqa: E402

_DATA_DIR = Path(__file__).resolve().parent / "data"

app = FastAPI(
    title="MEVID Agent API",
    version="1.0.0",
    description="Multi-camera video pipeline + LangGraph agent — MEVID evaluation service.",
)


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/healthz", response_model=HealthResponse)
def healthz() -> HealthResponse:
    db = agent_service.db_info
    return HealthResponse(
        status="ok",
        database_selected=agent_service.database_selected,
        sqlite_path=db.get("sqlite_path", ""),
        chroma_path=db.get("chroma_path", ""),
        namespace=db.get("namespace", ""),
    )


# ── Ingest ────────────────────────────────────────────────────────────────────

@app.post("/api/v1/ingest/seeds", response_model=IngestResult)
def ingest_seeds(payload: IngestFromSeedsRequest) -> IngestResult:
    """Build SQLite + Chroma from pre-generated events_vector_flat seed files."""
    output_base = str(_DATA_DIR / "runtime" / payload.namespace)
    try:
        result = pipeline_service.ingest_from_seeds(
            seeds_dir=payload.seeds_dir,
            namespace=payload.namespace,
            output_base=output_base,
            reset_existing=payload.reset_existing,
        )
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    # Auto-select the newly built database
    agent_service.select_database(
        sqlite_path=result["sqlite_path"],
        chroma_path=result["chroma_path"],
        namespace=result["namespace"],
    )
    return IngestResult(**result)


@app.post("/api/v1/ingest/videos", response_model=IngestResult)
def ingest_videos(payload: IngestFromVideosRequest) -> IngestResult:
    """Run full multi-camera pipeline (YOLO+Re-ID+matching) and build databases."""
    output_base = str(_DATA_DIR / "runtime" / payload.namespace)
    try:
        result = pipeline_service.ingest_from_videos(
            camera_videos=payload.camera_videos,
            namespace=payload.namespace,
            output_base=output_base,
            conf=payload.conf,
            iou=payload.iou,
            reid_device=payload.reid_device,
            refine=payload.refine,
            refine_model=payload.refine_model,
            reset_existing=payload.reset_existing,
        )
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    agent_service.select_database(
        sqlite_path=result["sqlite_path"],
        chroma_path=result["chroma_path"],
        namespace=result["namespace"],
    )
    return IngestResult(**result)


# ── Database ──────────────────────────────────────────────────────────────────

@app.post("/api/v1/database/select")
def select_database(payload: SelectDatabaseRequest) -> dict:
    """Manually point the agent at an existing database."""
    try:
        agent_service.select_database(
            sqlite_path=payload.sqlite_path,
            chroma_path=payload.chroma_path,
            namespace=payload.namespace,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"status": "ok", "namespace": payload.namespace}


# ── Agent ─────────────────────────────────────────────────────────────────────

@app.post("/api/v1/agent/query", response_model=QueryResponse)
def agent_query(payload: QueryRequest) -> QueryResponse:
    """Run a single natural-language query through the LangGraph agent."""
    try:
        result = agent_service.run_query(
            query=payload.query,
            thread_id=payload.thread_id,
            user_id=payload.user_id,
            include_rows=payload.include_rows,
            include_node_trace=payload.include_node_trace,
            top_k_rows=payload.top_k_rows,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return QueryResponse(**result)


# ── Eval ──────────────────────────────────────────────────────────────────────

@app.post("/api/v1/eval/run", response_model=EvalSummary)
def run_eval(payload: EvalRunRequest) -> EvalSummary:
    """Run evaluation suite through the agent and return accuracy / IoU metrics."""
    if not agent_service.database_selected:
        raise HTTPException(
            status_code=400,
            detail="请先调用 /api/v1/ingest/seeds 或 /api/v1/database/select 选择数据库",
        )

    def _query_fn(question: str) -> dict:
        return agent_service.run_query(
            query=question,
            thread_id=None,
            user_id="eval_runner",
            include_rows=True,
            include_node_trace=False,
            top_k_rows=5,
        )

    try:
        summary = eval_service.run_eval(
            questions_file=payload.questions_file,
            agent_query_fn=_query_fn,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    cases = [EvalCaseResult(**{k: v for k, v in c.items() if k != "answer_raw"}) for c in summary["cases"]]
    return EvalSummary(**{**summary, "cases": cases})
