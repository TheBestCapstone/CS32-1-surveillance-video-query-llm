import time
from dataclasses import dataclass
from typing import Any

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.store.base import BaseStore

from .reflection_tool import do_reflection
from .rerank_tool import SimpleRerankTool
from .types import AgentState


@dataclass
class ParallelSearchResult:
    rows: list[dict[str, Any]]
    provider: str


class ParallelSearchPlaceholderProvider:
    def search(self, state: AgentState) -> ParallelSearchResult:
        del state
        return ParallelSearchResult(rows=[], provider="parallel_placeholder")


def create_parallel_search_node(provider: Any | None = None):
    reranker = SimpleRerankTool()
    actual_provider = provider or ParallelSearchPlaceholderProvider()

    def parallel_search_node(state: AgentState, config: RunnableConfig, store: BaseStore) -> dict[str, Any]:
        current_retry = int(state.get("retry_count", 0) or 0)
        max_retries = 3

        for attempt in range(max_retries - current_retry):
            try:
                search_result = actual_provider.search(state)
                parallel_result = search_result.rows if hasattr(search_result, "rows") else []

                reflection_result = do_reflection(
                    rows=parallel_result,
                    event_list=state.get("event_list", []),
                    meta_list=state.get("meta_list", []),
                )

                reranked = reranker.rerank(
                    rows=parallel_result,
                    event_list=state.get("event_list", []),
                    meta_list=state.get("meta_list", []),
                    top_k=5,
                )

                provider_name = getattr(search_result, "provider", "unknown")
                thought = f"Parallel检索完成: {len(parallel_result)}条结果, provider={provider_name}, 反思评分={reflection_result.get('quality_score')}"

                return {
                    "merged_result": parallel_result,
                    "rerank_result": reranked,
                    "reflection_result": reflection_result,
                    "tool_error": None,
                    "retry_count": current_retry,
                    "current_node": "parallel_search_node",
                    "thought": thought,
                    "messages": [AIMessage(content=f"并行检索完成，命中 {len(parallel_result)} 条")],
                }

            except Exception as exc:
                if attempt < max_retries - current_retry - 1:
                    time.sleep(1)
                    continue
                return {
                    "merged_result": [],
                    "rerank_result": [],
                    "reflection_result": {"feedback": f"检索失败: {exc}", "quality_score": 0.0, "needs_retry": True},
                    "tool_error": f"并行检索失败: {exc}",
                    "retry_count": current_retry + 1,
                    "current_node": "parallel_search_node",
                    "messages": [AIMessage(content=f"并行检索失败: {exc}")],
                }

        return {
            "merged_result": [],
            "rerank_result": [],
            "reflection_result": {"feedback": "已达到最大重试次数", "quality_score": 0.0, "needs_retry": False},
            "tool_error": "并行检索失败: 超过最大重试次数",
            "retry_count": current_retry + 1,
            "current_node": "parallel_search_node",
            "messages": [AIMessage(content="并行检索失败: 超过最大重试次数")],
        }

    return parallel_search_node
