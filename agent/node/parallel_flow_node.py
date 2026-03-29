from typing import Any

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.store.base import BaseStore

from .types import AgentState


def create_parallel_flow_node():
    def parallel_flow_node(state: AgentState, config: RunnableConfig, store: BaseStore) -> dict[str, Any]:
        del config, store
        tool_choice = state.get("tool_choice", {})
        sub_queries = tool_choice.get("sub_queries", {})
        thought_parts = ["并行流程启动"]

        if "hybrid" in sub_queries:
            thought_parts.append("将执行hybrid_search_node")
        if "sql" in sub_queries:
            thought_parts.append("将执行pure_sql_node")
        if "video_vect" in sub_queries:
            thought_parts.append("将执行video_vect_node")

        thought = ", ".join(thought_parts)
        return {
            "thought": thought,
            "messages": [AIMessage(content=thought)],
        }

    return parallel_flow_node


def route_parallel_flow(state: AgentState) -> str:
    tool_choice = state.get("tool_choice", {})
    sub_queries = tool_choice.get("sub_queries", {})

    if "hybrid" in sub_queries:
        return "hybrid_search_node"
    elif "sql" in sub_queries:
        return "pure_sql_node"
    elif "video_vect" in sub_queries:
        return "video_vect_node"
    else:
        return "final_answer_node"


if __name__ == "__main__":
    node = create_parallel_flow_node()
    out = node({
        "tool_choice": {
            "mode": "parallel",
            "sub_queries": {"hybrid": {}, "video_vect": {}},
        },
    }, {}, None)
    print(out["thought"])