import json
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi import Request
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from models import (
    CurrentDatabaseResponse,
    DatabaseListResponse,
    DatabaseOptionResponse,
    DatabaseSelectionRequest,
    DatabaseSelectionResponse,
    HealthResponse,
    QueryRequest,
    QueryResponse,
    VideoUploadResponse,
)
from service import agent_graph_service
from video_service import video_ingest_service

_FASTAPI_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="Capstone Agent API",
    version="0.1.0",
    description="FastAPI wrapper around the existing LangGraph agent.",
)
app.mount("/static", StaticFiles(directory=str(_FASTAPI_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(_FASTAPI_DIR / "templates"))


def _sse_line(*, event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@app.get("/")
def index(request: Request):
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "request": request,
            "page_title": "Capstone Video Agent",
            "max_upload_mb": 512,
        },
    )


@app.get("/healthz", response_model=HealthResponse)
def healthz() -> HealthResponse:
    return HealthResponse(**agent_graph_service.health_payload())


@app.get("/api/v1/databases", response_model=DatabaseListResponse)
def list_databases() -> DatabaseListResponse:
    payload = [DatabaseOptionResponse(**item) for item in agent_graph_service.list_databases()]
    return DatabaseListResponse(databases=payload)


@app.get("/api/v1/databases/current", response_model=CurrentDatabaseResponse)
def current_database() -> CurrentDatabaseResponse:
    selected = agent_graph_service.get_selected_database()
    return CurrentDatabaseResponse(
        selected_database=DatabaseOptionResponse(**selected) if selected else None,
        database_selected=bool(selected),
    )


@app.post("/api/v1/databases/select", response_model=DatabaseSelectionResponse)
def select_database(payload: DatabaseSelectionRequest) -> DatabaseSelectionResponse:
    try:
        selected = agent_graph_service.select_database(payload.database_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return DatabaseSelectionResponse(
        status="ok",
        selected_database=DatabaseOptionResponse(**selected),
    )


@app.post("/api/v1/query", response_model=QueryResponse)
def query_agent(payload: QueryRequest) -> QueryResponse:
    try:
        result = agent_graph_service.run_query(
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


@app.post("/api/v1/query/stream")
def stream_query_agent(payload: QueryRequest) -> StreamingResponse:
    def _event_stream():
        try:
            for item in agent_graph_service.stream_query(
                query=payload.query,
                thread_id=payload.thread_id,
                user_id=payload.user_id,
                include_rows=payload.include_rows,
                include_node_trace=payload.include_node_trace,
                top_k_rows=payload.top_k_rows,
            ):
                yield _sse_line(event=str(item.get("event") or "message"), data=item.get("data") or {})
        except ValueError as exc:
            yield _sse_line(event="error", data={"detail": str(exc)})
        except Exception as exc:
            yield _sse_line(event="error", data={"detail": str(exc)})

    return StreamingResponse(_event_stream(), media_type="text/event-stream")


@app.post("/api/v1/video/upload", response_model=VideoUploadResponse)
def upload_video_and_ingest(
    files: list[UploadFile] | None = File(default=None),
    file: UploadFile | None = File(default=None),
    tracker: str = Form("botsort_reid"),
    model_path: str = Form("11m"),
    conf: float = Form(0.25),
    iou: float = Form(0.25),
    target_classes: str | None = Form(None),
    camera_id: str | None = Form(None),
    refine_mode: str = Form("none"),
    refine_model: str = Form("gpt-5.4-mini"),
    import_to_db: bool = Form(True),
    sqlite_path: str | None = Form(None),
    chroma_path: str | None = Form(None),
    chroma_namespace: str | None = Form(None),
) -> VideoUploadResponse:
    normalized_refine_mode = str(refine_mode or "none").strip().lower()
    if normalized_refine_mode not in {"none", "vector", "full"}:
        raise HTTPException(status_code=400, detail="refine_mode must be one of: none, vector, full")
    upload_files = [item for item in (files or []) if item is not None]
    if file is not None:
        upload_files.append(file)
    if not upload_files:
        raise HTTPException(status_code=400, detail="at least one video file is required")
    try:
        result = video_ingest_service.process_uploads(
            upload_files=upload_files,
            tracker=tracker,
            model_path=model_path,
            conf=conf,
            iou=iou,
            target_classes=target_classes,
            camera_id=camera_id,
            refine_mode=normalized_refine_mode,
            refine_model=refine_model,
            import_to_db=import_to_db,
            sqlite_path=sqlite_path,
            chroma_path=chroma_path,
            chroma_namespace=chroma_namespace,
        )
        if result.get("imported_to_db"):
            selected = agent_graph_service.select_database(str(result.get("job_id") or ""))
            result["selected_database"] = selected
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return VideoUploadResponse(**result)
