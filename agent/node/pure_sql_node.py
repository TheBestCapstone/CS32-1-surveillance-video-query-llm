import time
from pathlib import Path
from typing import Any
import sqlite3

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.store.base import BaseStore

from .reflection_tool import do_reflection
from .rerank_tool import SimpleRerankTool
from .types import AgentState, default_sqlite_db_path


def create_pure_sql_node(
    db_path: Path | None = None,
    strategy: Any | None = None,
    row_mapper: Any | None = None,
    post_filter: Any | None = None,
    validate_config: Any | None = None,
    reload_hook: Any | None = None,
    connection_factory: Any | None = None,
):
    reranker = SimpleRerankTool()
    actual_db_path = db_path or default_sqlite_db_path()

    def _default_strategy(state: AgentState) -> tuple[str, list[Any], dict[str, Any]]:
        sql_plan = state.get("sql_plan", {}) if isinstance(state.get("sql_plan", {}), dict) else {}
        table = str(state.get("sql_table", sql_plan.get("table", "episodic_events"))).strip()
        fields = state.get("sql_fields", sql_plan.get("fields", ["event_id", "video_id", "camera_id", "track_id", "start_time", "end_time", "object_type", "object_color_cn"]))
        if not isinstance(fields, list) or not fields:
            raise ValueError("sql_fields 不能为空")
        field_clause = ", ".join([str(field).strip() for field in fields if str(field).strip()])
        where_items = state.get("sql_where", sql_plan.get("where", []))
        clauses: list[str] = []
        params: list[Any] = []
        if isinstance(where_items, list):
            for item in where_items:
                if not isinstance(item, dict):
                    continue
                field = str(item.get("field", "")).strip()
                op = str(item.get("op", "==")).strip().lower()
                value = item.get("value")
                if not field:
                    continue
                if op in {"=", "=="}:
                    clauses.append(f"{field} = ?")
                    params.append(value)
                elif op in {"!=", "<>"}:
                    clauses.append(f"{field} != ?")
                    params.append(value)
                elif op in {">", ">=", "<", "<="}:
                    clauses.append(f"{field} {op} ?")
                    params.append(value)
                elif op == "contains":
                    clauses.append(f"{field} LIKE ?")
                    params.append(f"%{value}%")
        where_clause = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        order_by = str(state.get("sql_order_by", sql_plan.get("order_by", "start_time ASC"))).strip()
        limit = int(state.get("sql_limit", sql_plan.get("limit", 80)))
        sql = f"SELECT {field_clause} FROM {table}{where_clause} ORDER BY {order_by} LIMIT ?"
        params.append(limit)
        return sql, params, {"table": table, "fields": fields}

    def _default_mapper(row: sqlite3.Row, selected_fields: list[str]) -> dict[str, Any]:
        result = {field: row[field] for field in selected_fields}
        result.setdefault("_distance", 0.0)
        if "event_summary_cn" not in result:
            result["event_summary_cn"] = (
                f"{result.get('object_color_cn', '')}{result.get('object_type', '')}"
                f" @{result.get('start_time', '')}-{result.get('end_time', '')}"
            )
        return result

    def _validate(state: AgentState) -> None:
        if callable(validate_config):
            validate_config(state)
            return
        sql_plan = state.get("sql_plan", {})
        if not isinstance(sql_plan, dict):
            raise ValueError("sql_plan 必须为 dict")

    def _post_filter(rows: list[dict[str, Any]], state: AgentState) -> list[dict[str, Any]]:
        if callable(post_filter):
            return post_filter(rows, state)
        return rows

    def _connect(path: Path):
        if callable(connection_factory):
            return connection_factory(path)
        return sqlite3.connect(path)

    def pure_sql_node(state: AgentState, config: RunnableConfig, store: BaseStore) -> dict[str, Any]:
        del config, store
        if callable(reload_hook):
            reload_hook()
        current_retry = int(state.get("retry_count", 0) or 0)
        max_retries = 3

        for attempt in range(max_retries - current_retry):
            try:
                _validate(state)
                start = time.perf_counter()
                query_builder = strategy or _default_strategy
                sql, params, query_meta = query_builder(state)
                selected_fields = [str(field).strip() for field in query_meta.get("fields", []) if str(field).strip()]
                conn = _connect(actual_db_path)
                conn.row_factory = sqlite3.Row
                try:
                    rows = conn.execute(sql, params).fetchall()
                finally:
                    conn.close()
                mapper = row_mapper or _default_mapper
                mapped_rows = [mapper(row, selected_fields) for row in rows]
                sql_result = _post_filter(mapped_rows, state)
                elapsed_ms = round((time.perf_counter() - start) * 1000, 2)

                reflection_result = do_reflection(
                    rows=sql_result,
                    event_list=state.get("event_list", []),
                    meta_list=state.get("meta_list", []),
                )

                rerank_top_k = int((state.get("search_config", {}) or {}).get("rerank_top_k", 5))
                reranked = reranker.rerank(
                    rows=sql_result,
                    event_list=state.get("event_list", []),
                    meta_list=state.get("meta_list", []),
                    top_k=rerank_top_k,
                )

                thought = (
                    f"Pure SQL检索完成: rows={len(sql_result)}, rerank={len(reranked)}, "
                    f"latency_ms={elapsed_ms}, table={query_meta.get('table')}, 反思评分={reflection_result.get('quality_score')}"
                )

                return {
                    "sql_result": sql_result,
                    "rerank_result": reranked,
                    "reflection_result": reflection_result,
                    "tool_error": None,
                    "retry_count": current_retry,
                    "current_node": "pure_sql_node",
                    "metrics": {
                        **(state.get("metrics", {}) if isinstance(state.get("metrics", {}), dict) else {}),
                        "sql_latency_ms": elapsed_ms,
                        "sql_result_count": len(sql_result),
                    },
                    "thought": thought,
                    "messages": [AIMessage(content=f"纯SQL检索完成，命中 {len(sql_result)} 条")],
                }

            except Exception as exc:
                if attempt < max_retries - current_retry - 1:
                    time.sleep(1)
                    continue
                return {
                    "sql_result": [],
                    "rerank_result": [],
                    "reflection_result": {"feedback": f"检索失败: {exc}", "quality_score": 0.0, "needs_retry": True},
                    "tool_error": f"纯SQL检索失败: {exc}",
                    "retry_count": current_retry + 1,
                    "current_node": "pure_sql_node",
                    "messages": [AIMessage(content=f"纯SQL检索失败: {exc}")],
                }

        return {
            "sql_result": [],
            "rerank_result": [],
            "reflection_result": {"feedback": "已达到最大重试次数", "quality_score": 0.0, "needs_retry": False},
            "tool_error": "纯SQL检索失败: 超过最大重试次数",
            "retry_count": current_retry + 1,
            "current_node": "pure_sql_node",
            "messages": [AIMessage(content="纯SQL检索失败: 超过最大重试次数")],
        }

    return pure_sql_node


if __name__ == "__main__":
    node = create_pure_sql_node()
    out = node({"meta_list": [], "event_list": [], "retry_count": 0}, config={}, store=None)
    print("sql result:", out["reflection_result"])
