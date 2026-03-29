import time
from pathlib import Path
from typing import Any

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.store.base import BaseStore

from tools.py2sql import SQLVideoSearchTool

from .reflection_tool import do_reflection
from .rerank_tool import SimpleRerankTool
from .types import AgentState, default_db_path


def create_hybrid_search_node(db_path: Path | None = None, tool: SQLVideoSearchTool | None = None):
    actual_db_path = db_path or default_db_path()
    reranker = SimpleRerankTool()

    def hybrid_search_node(state: AgentState, config: RunnableConfig, store: BaseStore) -> dict[str, Any]:
        current_retry = int(state.get("retry_count", 0) or 0)
        max_retries = 3

        for attempt in range(max_retries - current_retry):
            try:
                search_tool = tool or SQLVideoSearchTool(db_path=actual_db_path)
                sql_rows = search_tool.search(
                    metadata_filters=state.get("meta_list", []),
                    event_queries=state.get("event_list", []),
                    candidate_limit=40,
                    top_k_per_event=20,
                )
                if not sql_rows:
                    if attempt < max_retries - current_retry - 1:
                        time.sleep(1)
                        continue
                    sql_rows = []

                reflection_result = do_reflection(
                    rows=sql_rows,
                    event_list=state.get("event_list", []),
                    meta_list=state.get("meta_list", []),
                )

                reranked = reranker.rerank(
                    rows=sql_rows,
                    event_list=state.get("event_list", []),
                    meta_list=state.get("meta_list", []),
                    top_k=5,
                )

                top_ids = [str(item.get("event_id")) for item in reranked[:3]]
                thought = f"Hybrid检索完成: {len(sql_rows)}条结果, 反思评分={reflection_result.get('quality_score')}, top_ids={top_ids}"

                return {
                    "hybrid_result": sql_rows,
                    "rerank_result": reranked,
                    "reflection_result": reflection_result,
                    "tool_error": None,
                    "retry_count": current_retry,
                    "current_node": "hybrid_search_node",
                    "thought": thought,
                    "messages": [AIMessage(content=f"混合检索完成，命中 {len(sql_rows)} 条")],
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