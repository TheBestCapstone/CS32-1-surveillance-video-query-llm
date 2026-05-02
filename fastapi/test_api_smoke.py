from __future__ import annotations

import io
import sys
from collections.abc import Iterator
from pathlib import Path

from fastapi.testclient import TestClient

_FASTAPI_DIR = Path(__file__).resolve().parent
if str(_FASTAPI_DIR) not in sys.path:
    sys.path.insert(0, str(_FASTAPI_DIR))

from main import app
from service import agent_graph_service
from video_service import video_ingest_service


class _FakeGraph:
    def stream(self, inputs: dict, config: dict, stream_mode: str = "values") -> Iterator[dict]:
        del inputs, config, stream_mode
        yield {"current_node": "self_query_node"}
        yield {"current_node": "query_classification_node"}
        yield {
            "current_node": "summary_node",
            "final_answer": "Yes. The relevant clip is in Demo001, around 0:00:05 - 0:00:12.\nSources: [sql] Demo001 | event_id=1 | 5-12",
            "raw_final_answer": "Yes. The relevant clip is in Demo001, around 0:00:05 - 0:00:12.",
            "answer_type": "existence",
            "summary_result": {
                "citations": [
                    {
                        "source_type": "sql",
                        "video_id": "Demo001",
                        "event_id": 1,
                        "start_time": 5,
                        "end_time": 12,
                        "record_level": "child",
                    }
                ]
            },
            "verifier_result": {"decision": "exact", "confidence": 0.95},
            "classification_result": {"label": "semantic"},
            "routing_metrics": {"hybrid_weight": 0.7},
            "sql_debug": {"fusion_meta": {"degraded": False}},
            "rerank_result": [{"video_id": "Demo001", "event_id": 1, "start_time": 5, "end_time": 12}],
        }


def _with_fake_graph() -> TestClient:
    original = agent_graph_service._graph
    original_selected = agent_graph_service._selected_database
    agent_graph_service._graph = _FakeGraph()
    agent_graph_service._selected_database = {
        "id": "demo-db",
        "label": "Demo DB",
        "sqlite_path": "/tmp/demo.sqlite",
        "chroma_path": "/tmp/chroma",
        "chroma_namespace": "demo",
        "source": "uploaded",
        "selected": True,
    }
    client = TestClient(app)

    def _restore() -> None:
        agent_graph_service._graph = original
        agent_graph_service._selected_database = original_selected

    client.__dict__["_restore_graph"] = _restore
    return client


def test_query_endpoint_smoke() -> None:
    client = _with_fake_graph()
    try:
        response = client.post(
            "/api/v1/query",
            json={"query": "find the clip", "include_rows": True, "top_k_rows": 1},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["answer"] == "Yes. The relevant clip is in Demo001, around 0:00:05 - 0:00:12."
        assert payload["rows"][0]["video_id"] == "Demo001"
        assert payload["node_trace"] == ["self_query_node", "query_classification_node", "summary_node"]
    finally:
        client.__dict__["_restore_graph"]()


def test_stream_endpoint_smoke() -> None:
    client = _with_fake_graph()
    try:
        with client.stream(
            "POST",
            "/api/v1/query/stream",
            json={"query": "find the clip", "include_rows": False, "top_k_rows": 1},
        ) as response:
            assert response.status_code == 200
            body = "".join(response.iter_text())
        assert "event: chunk" in body
        assert "event: final" in body
        assert "Demo001" in body
    finally:
        client.__dict__["_restore_graph"]()


def test_video_upload_endpoint_smoke(monkeypatch) -> None:
    def _fake_process_uploads(**kwargs):
        assert kwargs["tracker"] == "botsort_reid"
        assert kwargs["refine_mode"] == "none"
        assert len(kwargs["upload_files"]) == 2
        return {
            "status": "ok",
            "job_id": "video-demo",
            "filename": "demo.mp4",
            "filenames": ["demo.mp4", "demo2.mp4"],
            "file_count": 2,
            "refine_mode": "none",
            "imported_to_db": True,
            "pipeline_meta": {"batch": True, "file_count": 2, "files": []},
            "events_count": 5,
            "clip_count": 2,
            "artifacts": [
                {
                    "filename": "demo.mp4",
                    "uploaded_video_path": "/tmp/demo.mp4",
                    "events_json_path": "/tmp/demo_events.json",
                    "clips_json_path": "/tmp/demo_clips.json",
                    "refined_json_path": None,
                    "db_seed_path": "/tmp/demo_events.json",
                },
                {
                    "filename": "demo2.mp4",
                    "uploaded_video_path": "/tmp/demo2.mp4",
                    "events_json_path": "/tmp/demo2_events.json",
                    "clips_json_path": "/tmp/demo2_clips.json",
                    "refined_json_path": None,
                    "db_seed_path": "/tmp/demo2_events.json",
                },
            ],
            "database_import": {
                "sqlite": {"inserted_rows": 5},
                "chroma": {"event_record_count": 5},
            },
        }

    monkeypatch.setattr(video_ingest_service, "process_uploads", _fake_process_uploads)
    monkeypatch.setattr(
        agent_graph_service,
        "select_database",
        lambda database_id: {
            "id": database_id,
            "label": "Demo DB",
            "sqlite_path": "/tmp/demo.sqlite",
            "chroma_path": "/tmp/chroma",
            "chroma_namespace": "demo",
            "source": "uploaded",
            "selected": True,
        },
    )
    client = TestClient(app)
    response = client.post(
        "/api/v1/video/upload",
        data={"tracker": "botsort_reid", "refine_mode": "none", "import_to_db": "true"},
        files=[
            ("files", ("demo.mp4", io.BytesIO(b"fake-video-bytes"), "video/mp4")),
            ("files", ("demo2.mp4", io.BytesIO(b"fake-video-bytes-2"), "video/mp4")),
        ],
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["job_id"] == "video-demo"
    assert payload["file_count"] == 2
    assert payload["events_count"] == 5
    assert payload["artifacts"][0]["uploaded_video_path"] == "/tmp/demo.mp4"
    assert payload["selected_database"]["id"] == "video-demo"
    assert payload["selected_database"]["selected"] is True


def test_database_endpoints_and_query_precondition(monkeypatch) -> None:
    original_selected = agent_graph_service._selected_database
    monkeypatch.setattr(
        agent_graph_service,
        "list_databases",
        lambda: [
            {
                "id": "db-a",
                "label": "Database A",
                "sqlite_path": "/tmp/a.sqlite",
                "chroma_path": "/tmp/chroma-a",
                "chroma_namespace": "db_a",
                "source": "uploaded",
                "selected": False,
            }
        ],
    )
    monkeypatch.setattr(
        agent_graph_service,
        "select_database",
        lambda database_id: {
            "id": database_id,
            "label": "Database A",
            "sqlite_path": "/tmp/a.sqlite",
            "chroma_path": "/tmp/chroma-a",
            "chroma_namespace": "db_a",
            "source": "uploaded",
            "selected": True,
        },
    )
    agent_graph_service._selected_database = None
    client = TestClient(app)
    try:
        home = client.get("/")
        assert home.status_code == 200
        assert "Video Upload & Retrieval Console" in home.text

        dbs = client.get("/api/v1/databases")
        assert dbs.status_code == 200
        assert dbs.json()["databases"][0]["id"] == "db-a"

        current = client.get("/api/v1/databases/current")
        assert current.status_code == 200
        assert current.json()["database_selected"] is False

        blocked = client.post("/api/v1/query", json={"query": "hello"})
        assert blocked.status_code == 400
        assert "请先选择数据库" in blocked.json()["detail"]

        selected = client.post("/api/v1/databases/select", json={"database_id": "db-a"})
        assert selected.status_code == 200
        assert selected.json()["selected_database"]["id"] == "db-a"
    finally:
        agent_graph_service._selected_database = original_selected


def test_list_databases_keeps_selected_uploaded_database(monkeypatch) -> None:
    original_selected = agent_graph_service._selected_database
    agent_graph_service._selected_database = {
        "id": "video-new",
        "label": "new upload",
        "sqlite_path": "/tmp/video-new.sqlite",
        "chroma_path": "/tmp/chroma-video-new",
        "chroma_namespace": "upload_video_new",
        "source": "uploaded",
        "selected": True,
    }
    monkeypatch.setattr(
        agent_graph_service,
        "_configured_database",
        lambda: {
            "id": "configured-default",
            "label": "Configured Default Database",
            "sqlite_path": "/tmp/configured.sqlite",
            "chroma_path": "/tmp/configured-chroma",
            "chroma_namespace": "configured",
            "source": "configured",
        },
    )
    monkeypatch.setattr(agent_graph_service, "_uploaded_databases", lambda: [])
    client = TestClient(app)
    try:
        response = client.get("/api/v1/databases")
        assert response.status_code == 200
        payload = response.json()
        assert payload["databases"][0]["id"] == "video-new"
        assert payload["databases"][0]["selected"] is True
    finally:
        agent_graph_service._selected_database = original_selected


def test_video_upload_refine_mode_validation() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v1/video/upload",
        data={"refine_mode": "bad_mode"},
        files={"file": ("demo.mp4", io.BytesIO(b"fake-video-bytes"), "video/mp4")},
    )
    assert response.status_code == 400
    assert "refine_mode" in response.json()["detail"]
