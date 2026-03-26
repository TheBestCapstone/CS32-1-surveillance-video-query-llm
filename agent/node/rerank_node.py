from typing import Any

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.store.base import BaseStore

from retrieval.reranker import SimpleRerankTool

from .types import AgentState


def create_rerank_node(reranker: SimpleRerankTool | None = None):
    def rerank_node(state: AgentState, config: RunnableConfig, store: BaseStore) -> dict[str, Any]:
        del config, store
        if state.get("tool_error"):
            return {"rerank_result": [], "thought": ""}
        try:
            actual_reranker = reranker or SimpleRerankTool()
            ranked = actual_reranker.rerank(
                rows=state.get("sql_result", []),
                event_list=state.get("event_list", []),
                meta_list=state.get("meta_list", []),
                top_k=5,
            )
            top_ids = [str(item.get("event_id")) for item in ranked[:3]]
            thought = f"完成重排，top事件ID: {', '.join(top_ids)}" if top_ids else "没有可重排的结果"
            return {
                "rerank_result": ranked,
                "thought": thought,
                "messages": [AIMessage(content=f"重排完成，保留 {len(ranked)} 条")],
            }
        except Exception as exc:
            return {
                "rerank_result": [],
                "tool_error": f"Rerank失败: {exc}",
                "messages": [AIMessage(content=f"Rerank失败: {exc}")],
            }

    return rerank_node


if __name__ == "__main__":
    class FakeReranker:
        def rerank(self, rows, event_list, meta_list, top_k=5):
            del event_list, meta_list
            return rows[:top_k]

    node = create_rerank_node(reranker=FakeReranker())
    out = node(
        {"sql_result": [{"event_id": 1}, {"event_id": 2}], "event_list": ["进入"], "meta_list": [], "tool_error": None},
        config={},
        store=None,
    )
    print(out["thought"])
