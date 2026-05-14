"""Agent service — manages LangGraph graph lifecycle and DB selection."""
from __future__ import annotations

import os
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Iterator

from langchain_core.messages import AIMessage, HumanMessage

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_AGENT_ROOT = _PROJECT_ROOT / "agent"
for _p in (str(_PROJECT_ROOT), str(_AGENT_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import graph as graph_module  # noqa: E402
from tools.bm25_index import BM25Index  # noqa: E402


def _load_env() -> None:
    """Load .env from project root (API keys, model settings, etc.)."""
    env_file = _PROJECT_ROOT / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _strip_sources(text: str | None) -> str:
    body = str(text or "").strip()
    if "\nSources:" in body:
        body = body.split("\nSources:", 1)[0].strip()
    return body


class AgentService:
    def __init__(self) -> None:
        self._graph = None
        self._db: dict[str, str] = {}  # sqlite_path, chroma_path, namespace

    @property
    def graph(self):
        if self._graph is None:
            self._graph = graph_module.create_graph()
        return self._graph

    def select_database(
        self,
        *,
        sqlite_path: str,
        chroma_path: str,
        namespace: str,
    ) -> None:
        """Point the agent at a specific database and invalidate caches.

        Mirrors the env-var setup used in run_agent_eval.py exactly:
          AGENT_SQLITE_DB_PATH, AGENT_CHROMA_PATH, AGENT_CHROMA_NAMESPACE,
          AGENT_CHROMA_COLLECTION (legacy), AGENT_CHROMA_CHILD_COLLECTION,
          AGENT_CHROMA_PARENT_COLLECTION, AGENT_CHROMA_EVENT_COLLECTION,
          AGENT_CHROMA_RETRIEVAL_LEVEL=child
        """
        from agent.db.config import (
            CHROMA_CHILD_SUFFIX,
            CHROMA_EVENT_SUFFIX,
            CHROMA_PARENT_SUFFIX,
        )

        _load_env()  # pick up API keys / model settings from .env

        child_col = f"{namespace}_{CHROMA_CHILD_SUFFIX}"
        parent_col = f"{namespace}_{CHROMA_PARENT_SUFFIX}"
        event_col = f"{namespace}_{CHROMA_EVENT_SUFFIX}"

        os.environ["AGENT_SQLITE_DB_PATH"] = sqlite_path
        os.environ["AGENT_CHROMA_PATH"] = chroma_path
        os.environ["AGENT_CHROMA_NAMESPACE"] = namespace
        # Both old and new collection env vars — matches run_agent_eval.py
        os.environ["AGENT_CHROMA_COLLECTION"] = child_col
        os.environ["AGENT_CHROMA_CHILD_COLLECTION"] = child_col
        os.environ["AGENT_CHROMA_PARENT_COLLECTION"] = parent_col
        os.environ["AGENT_CHROMA_EVENT_COLLECTION"] = event_col
        os.environ["AGENT_CHROMA_RETRIEVAL_LEVEL"] = "child"

        BM25Index.clear_cache()
        self._graph = None
        self._db = {
            "sqlite_path": sqlite_path,
            "chroma_path": chroma_path,
            "namespace": namespace,
        }

    @property
    def db_info(self) -> dict[str, str]:
        return dict(self._db)

    @property
    def database_selected(self) -> bool:
        return bool(self._db)

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
        if not self.database_selected:
            raise ValueError("请先选择数据库后再查询 (call POST /api/v1/database/select)")

        resolved_thread_id = thread_id or f"mevid-{uuid.uuid4().hex[:12]}"
        config = {"configurable": {"thread_id": resolved_thread_id, "user_id": user_id}}
        messages: list = [HumanMessage(content=question)]

        last_chunk: dict[str, Any] = {}
        node_trace: list[str] = []
        t0 = time.perf_counter()
        for chunk in self.graph.stream({"messages": messages}, config, stream_mode="values"):
            last_chunk = chunk
            current_node = chunk.get("current_node")
            if include_node_trace and current_node and (not node_trace or node_trace[-1] != current_node):
                node_trace.append(str(current_node))
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)

        answer = _strip_sources(last_chunk.get("final_answer"))
        # Mirror _final_rows from run_agent_eval.py
        all_rows: list[dict] = []
        for key in ("rerank_result", "merged_result", "hybrid_result", "sql_result"):
            candidate = last_chunk.get(key)
            if isinstance(candidate, list):
                all_rows = [r for r in candidate if isinstance(r, dict)]
                break
        return {
            "query": question,
            "answer": answer,
            "final_answer": str(last_chunk.get("final_answer") or "").strip(),
            "answer_type": str(last_chunk.get("answer_type") or "").strip(),
            "node_trace": node_trace,
            "elapsed_ms": elapsed_ms,
            "verifier_result": last_chunk.get("verifier_result") if isinstance(last_chunk.get("verifier_result"), dict) else {},
            "rows": all_rows[:top_k_rows] if include_rows else [],
        }


agent_service = AgentService()
