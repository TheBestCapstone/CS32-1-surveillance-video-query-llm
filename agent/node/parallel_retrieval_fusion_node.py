import json
import os
import re
import sqlite3
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from typing import Any, Dict, List, Tuple

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.store.base import BaseStore

from agents.shared import weighted_rrf_fuse
from tools.hybrid_tools import dynamic_weighted_vector_search
from .retrieval_contracts import (
    build_routing_metrics,
    build_search_config,
    extract_structured_filters,
    extract_text_tokens_for_sql,
    infer_sql_plan,
    normalize_hybrid_rows,
    normalize_sql_rows,
)
from .types import AgentState, InputValidator
from .types import default_sqlite_db_path


def _safe_sub_agent_call(func, *args) -> Tuple[str, List[Dict[str, Any]], str | None]:
    try:
        summary, rows = func(*args)
        return summary or "", rows or [], None
    except Exception as exc:
        return "", [], str(exc)


def _run_sql_branch(user_query: str, search_config: Dict[str, Any]) -> Tuple[str, List[Dict[str, Any]]]:
    db_path = default_sqlite_db_path()
    filters = extract_structured_filters(user_query)
    params: List[Any] = []
    clauses: List[str] = []
    if "object_type" in filters:
        clauses.append("lower(object_type) = ?")
        params.append(filters["object_type"])
    if "object_color_en" in filters:
        clauses.append("lower(object_color_en) = ?")
        params.append(filters["object_color_en"])
    if "scene_zone_en" in filters:
        clauses.append("lower(scene_zone_en) LIKE ?")
        params.append(f"%{filters['scene_zone_en']}%")

    tokens = extract_text_tokens_for_sql(user_query, filters)
    text_clauses = []
    for t in tokens:
        text_clauses.append(
            "(lower(coalesce(event_text_en,'')) LIKE ? OR lower(coalesce(event_summary_en,'')) LIKE ? OR lower(coalesce(appearance_notes_en,'')) LIKE ?)"
        )
        params.extend([f"%{t}%", f"%{t}%", f"%{t}%"])
    if text_clauses:
        clauses.append("(" + " OR ".join(text_clauses) + ")")

    where_sql = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    sql = (
        "SELECT event_id, video_id, track_id, start_time, end_time, object_type, "
        "object_color_en, scene_zone_en, event_summary_en "
        "FROM episodic_events"
        f"{where_sql} ORDER BY start_time ASC LIMIT {int(search_config.get('sql_limit', 80))}"
    )
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = normalize_sql_rows([dict(r) for r in conn.execute(sql, params).fetchall()])
    return f"SQL direct retrieval rows={len(rows)}", rows


def _run_hybrid_branch(user_query: str, search_config: Dict[str, Any]) -> Tuple[str, List[Dict[str, Any]]]:
    if not (user_query or "").strip():
        return "Hybrid retrieval skipped: empty query", []
    filters = extract_structured_filters(user_query)
    msg = dynamic_weighted_vector_search.invoke(
        {
            "query": user_query,
            "filters": filters,
            "alpha": float(search_config.get("hybrid_alpha", 0.7)),
            "limit": int(search_config.get("hybrid_limit", 50)),
        }
    )
    lowered = (msg or "").lower()
    if "failed on chroma" in lowered or "error code" in lowered:
        raise RuntimeError(msg)

    # Retry with looser semantic emphasis when metadata filters are too strict.
    if "returned no results on chroma" in lowered and filters:
        fallback_msg = dynamic_weighted_vector_search.invoke(
            {
                "query": user_query,
                "filters": {},
                "alpha": float(search_config.get("hybrid_fallback_alpha", 0.9)),
                "limit": int(search_config.get("hybrid_limit", 50)),
            }
        )
        fallback_lowered = (fallback_msg or "").lower()
        if "failed on chroma" in fallback_lowered or "error code" in fallback_lowered:
            raise RuntimeError(fallback_msg)
        if ":\n" in fallback_msg:
            msg = fallback_msg
        else:
            return f"{msg} | fallback={fallback_msg}", []

    if ":\n" not in msg:
        return msg, []
    payload = msg.split(":\n", 1)[1]
    rows = json.loads(payload)
    normalized = normalize_hybrid_rows(rows)
    return "Hybrid direct retrieval complete", normalized


def create_parallel_retrieval_fusion_node(llm=None, **kwargs):
    del kwargs
    del llm
    branch_timeout = float(os.getenv("AGENT_PARALLEL_BRANCH_TIMEOUT_SEC", "30"))
    fused_limit = int(os.getenv("AGENT_FUSION_TOP_K", "50"))

    def parallel_retrieval_fusion_node(state: AgentState, config: RunnableConfig, store: BaseStore) -> dict[str, Any]:
        del config, store
        user_query = InputValidator.resolve_active_query(state)
        search_config = build_search_config(state.get("search_config", {}))
        label = (
            (state.get("classification_result", {}) or {}).get("label")
            if isinstance(state.get("classification_result", {}), dict)
            else "mixed"
        ) or "mixed"
        sql_plan = infer_sql_plan(user_query, search_config)

        start = time.perf_counter()
        sql_summary = ""
        hybrid_summary = ""
        sql_rows: List[Dict[str, Any]] = []
        hybrid_rows: List[Dict[str, Any]] = []
        sql_error = None
        hybrid_error = None

        with ThreadPoolExecutor(max_workers=2) as ex:
            f_sql = ex.submit(_safe_sub_agent_call, _run_sql_branch, user_query, search_config)
            f_hybrid = ex.submit(_safe_sub_agent_call, _run_hybrid_branch, user_query, search_config)

            try:
                sql_summary, sql_rows, sql_error = f_sql.result(timeout=branch_timeout)
            except TimeoutError:
                sql_error = f"pure_sql timeout ({branch_timeout}s)"
            try:
                hybrid_summary, hybrid_rows, hybrid_error = f_hybrid.result(timeout=branch_timeout)
            except TimeoutError:
                hybrid_error = f"hybrid timeout ({branch_timeout}s)"

        both_failed = (sql_error is not None and hybrid_error is not None)
        if both_failed:
            duration = time.perf_counter() - start
            return {
                "sql_result": [],
                "hybrid_result": [],
                "merged_result": [],
                "rerank_result": [],
                "tool_error": f"Both branches failed: sql={sql_error}; hybrid={hybrid_error}",
                "current_node": "parallel_retrieval_fusion_node",
                "metrics": {
                    "duration": duration,
                    "degraded": True,
                    "degraded_reason": "both_failed",
                },
                "messages": [AIMessage(content="Parallel retrieval failed on both branches.")],
            }

        if sql_error and not hybrid_error:
            fused = hybrid_rows[:fused_limit]
            fusion_meta = {
                "label": label,
                "degraded": True,
                "degraded_reason": "sql_failed",
                "method": "fallback_hybrid_only",
            }
        elif hybrid_error and not sql_error:
            fused = sql_rows[:fused_limit]
            fusion_meta = {
                "label": label,
                "degraded": True,
                "degraded_reason": "hybrid_failed",
                "method": "fallback_sql_only",
            }
        else:
            fused, fusion_meta = weighted_rrf_fuse(sql_rows, hybrid_rows, label=label, limit=fused_limit)
            fusion_meta["degraded"] = False

        structured_filters = extract_structured_filters(user_query)
        if label == "structured" and not sql_rows and structured_filters:
            fused = []
            fusion_meta = {
                "label": label,
                "degraded": True,
                "degraded_reason": "structured_zero_guardrail",
                "method": "prefer_empty_sql_over_loose_semantic",
            }

        if hybrid_error:
            fusion_meta["degraded"] = True
        if sql_error:
            fusion_meta["degraded"] = True

        duration = time.perf_counter() - start
        routing_metrics = build_routing_metrics(
            execution_mode="parallel_fusion",
            label=label,
            query=user_query,
            sql_rows_count=len(sql_rows),
            hybrid_rows_count=len(hybrid_rows),
            sql_error=sql_error,
            hybrid_error=hybrid_error,
        )
        return {
            "sql_result": sql_rows,
            "hybrid_result": hybrid_rows,
            "merged_result": fused,
            "rerank_result": fused,
            "tool_error": None,
            "current_node": "parallel_retrieval_fusion_node",
            "search_explain": (
                "Parallel retrieval completed. "
                f"label={label}, sql_rows={len(sql_rows)}, hybrid_rows={len(hybrid_rows)}, fused_rows={len(fused)}"
            ),
            "routing_metrics": routing_metrics,
            "search_config": search_config,
            "sql_plan": sql_plan,
            "sql_debug": {
                "duration": duration,
                "sql_summary": sql_summary,
                "hybrid_summary": hybrid_summary,
                "sql_error": sql_error,
                "hybrid_error": hybrid_error,
                "fusion_meta": fusion_meta,
            },
            "messages": [
                AIMessage(
                    content=(
                        f"Parallel retrieval + fusion complete (label={label}, "
                        f"sql={len(sql_rows)}, hybrid={len(hybrid_rows)}, fused={len(fused)})."
                    )
                )
            ],
        }

    return parallel_retrieval_fusion_node
