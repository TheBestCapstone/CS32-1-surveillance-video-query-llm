import time
from pathlib import Path
from typing import Any

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.store.base import BaseStore

from tools.db_access import LanceDBGateway
from tools.py2sql import SQLVideoSearchTool

from .reflection_tool import do_reflection
from .rerank_tool import SimpleRerankTool
from .types import AgentState, default_db_path


def create_hybrid_search_node(
    db_path: Path | None = None,
    tool: SQLVideoSearchTool | None = None,
    gateway: LanceDBGateway | None = None,
):
    actual_db_path = db_path or default_db_path()
    reranker = SimpleRerankTool()
    base_gateway = gateway or LanceDBGateway(actual_db_path)

    def _to_int(value: Any, default: int) -> int:
        try:
            return int(value)
        except Exception:
            return default

    def _to_float(value: Any, default: float | None) -> float | None:
        if value is None:
            return default
        try:
            return float(value)
        except Exception:
            return default

    def _search_single_table(table_name: str, state: AgentState, candidate_limit: int, top_k_per_event: int) -> list[dict[str, Any]]:
        if tool is not None:
            rows = tool.search(
                metadata_filters=state.get("meta_list", []),
                event_queries=state.get("event_list", []),
                candidate_limit=candidate_limit,
                top_k_per_event=top_k_per_event,
            )
        else:
            if gateway is not None and table_name == getattr(base_gateway, "table_name", table_name):
                search_gateway = base_gateway
            else:
                search_gateway = LanceDBGateway(actual_db_path, table_name=table_name)
            rows = search_gateway.search(
                metadata_filters=state.get("meta_list", []),
                event_queries=state.get("event_list", []),
                candidate_limit=candidate_limit,
                top_k_per_event=top_k_per_event,
            )
        normalized = []
        for row in rows:
            item = dict(row)
            item.setdefault("source_table", table_name)
            normalized.append(item)
        return normalized

    def _second_stage_filter(
        rows: list[dict[str, Any]],
        distance_threshold: float | None,
        state: AgentState,
    ) -> list[dict[str, Any]]:
        filtered = []
        event_terms = [str(term).strip() for term in state.get("event_list", []) if str(term).strip()]
        loose_terms = ["进入", "离开", "出现", "停止", "车辆", "车", "行人", "人", "卡车"]
        for row in rows:
            distance = row.get("_distance")
            if distance_threshold is not None:
                try:
                    if float(distance) > distance_threshold:
                        continue
                except Exception:
                    continue
            if event_terms:
                text = f"{row.get('event_text_cn', '')} {row.get('event_summary_cn', '')}"
                strict_hit = any(term in text for term in event_terms)
                loose_hit = any((token in text) and any(token in term for term in event_terms) for token in loose_terms)
                if not strict_hit and not loose_hit:
                    continue
            filtered.append(row)
        return filtered

    def hybrid_search_node(state: AgentState, config: RunnableConfig, store: BaseStore) -> dict[str, Any]:
        del config, store
        current_retry = int(state.get("retry_count", 0) or 0)
        max_retries = 3

        for attempt in range(max_retries - current_retry):
            try:
                start = time.perf_counter()
                search_cfg = state.get("search_config", {}) if isinstance(state.get("search_config", {}), dict) else {}
                candidate_limit = _to_int(search_cfg.get("candidate_limit", 80), 80)
                top_k_per_event = _to_int(search_cfg.get("top_k_per_event", 20), 20)
                rerank_top_k = _to_int(search_cfg.get("rerank_top_k", 5), 5)
                distance_threshold = _to_float(search_cfg.get("distance_threshold"), None)

                table_names = state.get("hybrid_table_names", [])
                if isinstance(table_names, list) and table_names:
                    selected_tables = [str(t).strip() for t in table_names if str(t).strip()]
                else:
                    selected_tables = [str(state.get("hybrid_table_name", "episodic_events")).strip() or "episodic_events"]

                raw_rows: list[dict[str, Any]] = []
                for table_name in selected_tables:
                    raw_rows.extend(_search_single_table(table_name, state, candidate_limit, top_k_per_event))

                dedup: dict[tuple[Any, Any], dict[str, Any]] = {}
                for row in raw_rows:
                    key = (row.get("source_table"), row.get("event_id"))
                    previous = dedup.get(key)
                    if previous is None:
                        dedup[key] = row
                        continue
                    if float(row.get("_distance", 1e9)) < float(previous.get("_distance", 1e9)):
                        dedup[key] = row
                sql_rows = list(dedup.values())
                filtered_rows = _second_stage_filter(sql_rows, distance_threshold, state)

                if not filtered_rows:
                    if attempt < max_retries - current_retry - 1:
                        time.sleep(1)
                        continue
                    filtered_rows = []

                reflection_result = do_reflection(
                    rows=filtered_rows,
                    event_list=state.get("event_list", []),
                    meta_list=state.get("meta_list", []),
                )

                reranked = reranker.rerank(
                    rows=filtered_rows,
                    event_list=state.get("event_list", []),
                    meta_list=state.get("meta_list", []),
                    top_k=rerank_top_k,
                )

                top_ids = [str(item.get("event_id")) for item in reranked[:3]]
                elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
                explain = {
                    "vector_column": "vector",
                    "metadata_columns": ["object_type", "object_color_cn", "scene_zone_cn", "start_time", "end_time"],
                    "filter_fields": [item.get("field") for item in state.get("meta_list", []) if isinstance(item, dict)],
                    "distance_metric": search_cfg.get("distance_metric", "l2/cosine(由LanceDB内部索引策略决定)"),
                    "tables": selected_tables,
                }
                thought = (
                    f"Hybrid检索完成: recall={len(sql_rows)}, filtered={len(filtered_rows)}, rerank={len(reranked)}, "
                    f"latency_ms={elapsed_ms}, quality={reflection_result.get('quality_score')}, top_ids={top_ids}"
                )

                return {
                    "hybrid_result": filtered_rows,
                    "rerank_result": reranked,
                    "reflection_result": reflection_result,
                    "tool_error": None,
                    "retry_count": current_retry,
                    "current_node": "hybrid_search_node",
                    "thought": thought,
                    "metrics": {
                        **(state.get("metrics", {}) if isinstance(state.get("metrics", {}), dict) else {}),
                        "hybrid_latency_ms": elapsed_ms,
                        "hybrid_recall_count": len(sql_rows),
                        "hybrid_filtered_count": len(filtered_rows),
                        "hybrid_rerank_count": len(reranked),
                    },
                    "search_explain": explain,
                    "messages": [AIMessage(content=f"混合检索完成，命中 {len(filtered_rows)} 条")],
                }

            except Exception as exc:
                if attempt < max_retries - current_retry - 1:
                    time.sleep(1)
                    continue
                return {
                    "hybrid_result": [],
                    "rerank_result": [],
                    "reflection_result": {"feedback": f"检索失败: {exc}", "quality_score": 0.0, "needs_retry": True},
                    "tool_error": f"混合检索失败: {exc}",
                    "retry_count": current_retry + 1,
                    "current_node": "hybrid_search_node",
                    "messages": [AIMessage(content=f"混合检索失败: {exc}")],
                }

        return {
            "hybrid_result": [],
            "rerank_result": [],
            "reflection_result": {"feedback": "已达到最大重试次数", "quality_score": 0.0, "needs_retry": False},
            "tool_error": "混合检索失败: 超过最大重试次数",
            "retry_count": current_retry + 1,
            "current_node": "hybrid_search_node",
            "messages": [AIMessage(content="混合检索失败: 超过最大重试次数")],
        }

    return hybrid_search_node


if __name__ == "__main__":
    class FakeTool:
        def search(self, metadata_filters, event_queries, candidate_limit=40, top_k_per_event=20):
            return [{"event_id": 1, "video_id": "demo.mp4", "_distance": 0.2}]

    node = create_hybrid_search_node(tool=FakeTool())
    out = node({"meta_list": [], "event_list": ["进入"], "retry_count": 0}, config={}, store=None)
    print("hybrid result:", out["reflection_result"])
    print("rerank count:", len(out["rerank_result"]))
