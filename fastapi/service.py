import os
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Iterator

from langchain_core.messages import AIMessage, HumanMessage

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_AGENT_ROOT = _PROJECT_ROOT / "agent"
if str(_AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(_AGENT_ROOT))

from db.config import (  # noqa: E402
    get_graph_chroma_child_collection,
    get_graph_chroma_event_collection,
    get_graph_chroma_namespace,
    get_graph_chroma_parent_collection,
    get_graph_chroma_path,
    get_graph_sqlite_db_path,
)
import graph as graph_module  # noqa: E402
from memory.short_term import add_turn, format_history_for_prompt, get_history  # noqa: E402
from tools.bm25_index import BM25Index  # noqa: E402


def _select_final_rows(final_state: dict[str, Any]) -> list[dict[str, Any]]:
    if "rerank_result" in final_state:
        return list(final_state.get("rerank_result") or [])
    if "merged_result" in final_state:
        return list(final_state.get("merged_result") or [])
    if "hybrid_result" in final_state:
        return list(final_state.get("hybrid_result") or [])
    return list(final_state.get("sql_result") or [])


def _strip_sources(text: str | None) -> str:
    body = str(text or "").strip()
    if "\nSources:" in body:
        body = body.split("\nSources:", 1)[0].strip()
    return body


def _build_messages_with_history(
    question: str,
    thread_id: str,
    user_id: str,
) -> list:
    """Build the messages list for graph invocation, prepending conversation
    history if short-term memory is enabled."""
    messages: list = []
    history_turns = get_history(thread_id, user_id)
    for turn in history_turns:
        messages.append(HumanMessage(content=str(turn["query"])))
        messages.append(AIMessage(content=str(turn["answer"])))
    messages.append(HumanMessage(content=question))
    return messages


class AgentGraphService:
    def __init__(self) -> None:
        self._graph = getattr(graph_module, "graph", None)
        self._selected_database: dict[str, Any] | None = None

    @property
    def graph(self):
        if self._graph is None:
            self._graph = graph_module.create_graph()
        return self._graph

    def set_runtime_targets(self, *, sqlite_path: str, chroma_path: str, chroma_namespace: str) -> None:
        os.environ["AGENT_SQLITE_DB_PATH"] = sqlite_path
        os.environ["AGENT_CHROMA_PATH"] = chroma_path
        os.environ["AGENT_CHROMA_NAMESPACE"] = chroma_namespace
        BM25Index.clear_cache()
        self._graph = None

    @property
    def data_root(self) -> Path:
        return Path(__file__).resolve().parent / "data"

    def _configured_database(self) -> dict[str, Any]:
        return {
            "id": "configured-default",
            "label": "当前配置数据库",
            "sqlite_path": str(get_graph_sqlite_db_path()),
            "chroma_path": str(get_graph_chroma_path()),
            "chroma_namespace": get_graph_chroma_namespace(),
            "source": "configured",
        }

    def _uploaded_databases(self) -> list[dict[str, Any]]:
        job_root = self.data_root / "video_jobs"
        if not job_root.exists():
            return []
        databases: list[dict[str, Any]] = []
        for job_dir in sorted(job_root.iterdir(), reverse=True):
            if not job_dir.is_dir():
                continue
            runtime_dir = job_dir / "runtime"
            sqlite_path = runtime_dir / "episodic_events.sqlite"
            chroma_path = runtime_dir / "chroma"
            if not sqlite_path.exists() or not chroma_path.exists():
                continue
            upload_dir = job_dir / "upload"
            uploaded_files = [p.name for p in sorted(upload_dir.iterdir()) if p.is_file()] if upload_dir.exists() else []
            if len(uploaded_files) <= 1:
                label_prefix = uploaded_files[0] if uploaded_files else job_dir.name
            else:
                label_prefix = f"{uploaded_files[0]} +{len(uploaded_files) - 1} files"
            namespace = f"upload_{job_dir.name.replace('-', '_')}"
            databases.append(
                {
                    "id": job_dir.name,
                    "label": f"{label_prefix} ({job_dir.name})",
                    "sqlite_path": str(sqlite_path),
                    "chroma_path": str(chroma_path),
                    "chroma_namespace": namespace,
                    "source": "uploaded",
                }
            )
        return databases

    def list_databases(self) -> list[dict[str, Any]]:
        options: list[dict[str, Any]] = []
        seen_ids: set[str] = set()
        seen_targets: set[tuple[str, str, str]] = set()
        selected_first: list[dict[str, Any]] = [dict(self._selected_database)] if self._selected_database else []
        for item in [*selected_first, self._configured_database(), *self._uploaded_databases()]:
            db_id = str(item.get("id") or "").strip()
            target_key = (
                str(item.get("sqlite_path") or ""),
                str(item.get("chroma_path") or ""),
                str(item.get("chroma_namespace") or ""),
            )
            if not db_id or db_id in seen_ids or target_key in seen_targets:
                continue
            seen_ids.add(db_id)
            seen_targets.add(target_key)
            option = dict(item)
            option["selected"] = bool(self._selected_database and self._selected_database.get("id") == db_id)
            options.append(option)
        return options

    def get_selected_database(self) -> dict[str, Any] | None:
        return dict(self._selected_database) if self._selected_database else None

    def select_database(self, database_id: str) -> dict[str, Any]:
        target_id = str(database_id or "").strip()
        if not target_id:
            raise ValueError("database_id must not be empty")
        for item in self.list_databases():
            if item["id"] != target_id:
                continue
            self.set_runtime_targets(
                sqlite_path=str(item["sqlite_path"]),
                chroma_path=str(item["chroma_path"]),
                chroma_namespace=str(item["chroma_namespace"]),
            )
            self._selected_database = {
                "id": item["id"],
                "label": item["label"],
                "sqlite_path": item["sqlite_path"],
                "chroma_path": item["chroma_path"],
                "chroma_namespace": item["chroma_namespace"],
                "source": item["source"],
                "selected": True,
            }
            return dict(self._selected_database)
        raise ValueError(f"unknown database_id: {target_id}")

    def health_payload(self) -> dict[str, Any]:
        selected = self.get_selected_database()
        return {
            "status": "ok",
            "graph_ready": self._graph is not None,
            "execution_mode": os.getenv("AGENT_EXECUTION_MODE", "parallel_fusion").strip().lower(),
            "sqlite_path": str(get_graph_sqlite_db_path()),
            "chroma_path": str(get_graph_chroma_path()),
            "chroma_namespace": get_graph_chroma_namespace(),
            "chroma_child_collection": get_graph_chroma_child_collection(),
            "chroma_parent_collection": get_graph_chroma_parent_collection(),
            "chroma_event_collection": get_graph_chroma_event_collection(),
            "selected_database_id": selected.get("id") if selected else None,
            "database_selected": bool(selected),
        }

    def run_query(
        self,
        *,
        query: str,
        thread_id: str | None,
        user_id: str,
        include_rows: bool,
        include_node_trace: bool,
        top_k_rows: int,
    ) -> dict[str, Any]:
        question = str(query).strip()
        if not question:
            raise ValueError("query must not be empty")
        if self._selected_database is None:
            raise ValueError("请先选择数据库后再查询")

        resolved_thread_id = thread_id or f"fastapi-{uuid.uuid4().hex[:12]}"
        config = {"configurable": {"thread_id": resolved_thread_id, "user_id": user_id}}

        messages = _build_messages_with_history(question, resolved_thread_id, user_id)
        last_chunk: dict[str, Any] = {}
        node_trace: list[str] = []
        t0 = time.perf_counter()
        for chunk in self.graph.stream({"messages": messages}, config, stream_mode="values"):
            last_chunk = chunk
            current_node = chunk.get("current_node")
            if include_node_trace and current_node and (not node_trace or node_trace[-1] != current_node):
                node_trace.append(str(current_node))
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)

        rows = _select_final_rows(last_chunk)
        summary_result = last_chunk.get("summary_result") if isinstance(last_chunk.get("summary_result"), dict) else {}
        sql_debug = last_chunk.get("sql_debug") if isinstance(last_chunk.get("sql_debug"), dict) else {}
        fusion_meta = sql_debug.get("fusion_meta") if isinstance(sql_debug.get("fusion_meta"), dict) else {}
        answer = _strip_sources(last_chunk.get("final_answer"))

        add_turn(resolved_thread_id, user_id, query=question, answer=answer)

        return {
            "query": question,
            "answer": answer,
            "final_answer": str(last_chunk.get("final_answer") or "").strip(),
            "raw_final_answer": str(last_chunk.get("raw_final_answer") or "").strip(),
            "thread_id": resolved_thread_id,
            "user_id": user_id,
            "elapsed_ms": elapsed_ms,
            "answer_type": str(last_chunk.get("answer_type") or "").strip(),
            "node_trace": node_trace,
            "citations": summary_result.get("citations") if isinstance(summary_result.get("citations"), list) else [],
            "verifier_result": last_chunk.get("verifier_result") if isinstance(last_chunk.get("verifier_result"), dict) else {},
            "classification_result": last_chunk.get("classification_result") if isinstance(last_chunk.get("classification_result"), dict) else {},
            "routing_metrics": last_chunk.get("routing_metrics") if isinstance(last_chunk.get("routing_metrics"), dict) else {},
            "fusion_meta": fusion_meta,
            "rows": rows[:top_k_rows] if include_rows else [],
        }

    def stream_query(
        self,
        *,
        query: str,
        thread_id: str | None,
        user_id: str,
        include_rows: bool,
        include_node_trace: bool,
        top_k_rows: int,
    ) -> Iterator[dict[str, Any]]:
        question = str(query).strip()
        if not question:
            raise ValueError("query must not be empty")

        resolved_thread_id = thread_id or f"fastapi-{uuid.uuid4().hex[:12]}"
        config = {"configurable": {"thread_id": resolved_thread_id, "user_id": user_id}}

        messages = _build_messages_with_history(question, resolved_thread_id, user_id)
        last_chunk: dict[str, Any] = {}
        node_trace: list[str] = []
        t0 = time.perf_counter()
        try:
            for index, chunk in enumerate(
                self.graph.stream({"messages": messages}, config, stream_mode="values"),
                start=1,
            ):
                last_chunk = chunk
                current_node = str(chunk.get("current_node") or "").strip()
                if include_node_trace and current_node and (not node_trace or node_trace[-1] != current_node):
                    node_trace.append(current_node)
                yield {
                    "event": "chunk",
                    "data": {
                        "index": index,
                        "query": question,
                        "thread_id": resolved_thread_id,
                        "user_id": user_id,
                        "current_node": current_node,
                        "elapsed_ms": round((time.perf_counter() - t0) * 1000, 2),
                        "node_trace": list(node_trace),
                    },
                }
        except Exception as exc:
            yield {
                "event": "error",
                "data": {
                    "query": question,
                    "thread_id": resolved_thread_id,
                    "user_id": user_id,
                    "detail": str(exc),
                },
            }
            return

        rows = _select_final_rows(last_chunk)
        summary_result = last_chunk.get("summary_result") if isinstance(last_chunk.get("summary_result"), dict) else {}
        sql_debug = last_chunk.get("sql_debug") if isinstance(last_chunk.get("sql_debug"), dict) else {}
        fusion_meta = sql_debug.get("fusion_meta") if isinstance(sql_debug.get("fusion_meta"), dict) else {}
        answer = _strip_sources(last_chunk.get("final_answer"))
        add_turn(resolved_thread_id, user_id, query=question, answer=answer)
        final_payload = {
            "query": question,
            "answer": answer,
            "final_answer": str(last_chunk.get("final_answer") or "").strip(),
            "raw_final_answer": str(last_chunk.get("raw_final_answer") or "").strip(),
            "thread_id": resolved_thread_id,
            "user_id": user_id,
            "elapsed_ms": round((time.perf_counter() - t0) * 1000, 2),
            "answer_type": str(last_chunk.get("answer_type") or "").strip(),
            "node_trace": node_trace,
            "citations": summary_result.get("citations") if isinstance(summary_result.get("citations"), list) else [],
            "verifier_result": last_chunk.get("verifier_result") if isinstance(last_chunk.get("verifier_result"), dict) else {},
            "classification_result": last_chunk.get("classification_result") if isinstance(last_chunk.get("classification_result"), dict) else {},
            "routing_metrics": last_chunk.get("routing_metrics") if isinstance(last_chunk.get("routing_metrics"), dict) else {},
            "fusion_meta": fusion_meta,
            "rows": rows[:top_k_rows] if include_rows else [],
        }
        yield {"event": "final", "data": final_payload}


agent_graph_service = AgentGraphService()
