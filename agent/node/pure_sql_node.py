import time
from typing import Any

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.store.base import BaseStore

from .reflection_tool import do_reflection
from .rerank_tool import SimpleRerankTool
from .types import AgentState


def create_pure_sql_node():
    reranker = SimpleRerankTool()

    def pure_sql_node(state: AgentState, config: RunnableConfig, store: BaseStore) -> dict[str, Any]:
        current_retry = int(state.get("retry_count", 0) or 0)
        max_retries = 3

        for attempt in range(max_retries - current_retry):
            try:
                sql_result = []

                reflection_result = do_reflection(
                    rows=sql_result,
                    event_list=state.get("event_list", []),
                    meta_list=state.get("meta_list", []),
                )

                reranked = reranker.rerank(
                    rows=sql_result,
                    event_list=state.get("event_list", []),
                    meta_list=state.get("meta_list", []),
                    top_k=5,
                )

                thought = f"Pure SQL检索完成: {len(sql_result)}条结果, 反思评分={reflection_result.get('quality_score')}"

                return {
                    "sql_result": sql_result,
                    "rerank_result": reranked,
                    "reflection_result": reflection_result,
                    "tool_error": None,
                    "retry_count": current_retry,
                    "current_node": "pure_sql_node",
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