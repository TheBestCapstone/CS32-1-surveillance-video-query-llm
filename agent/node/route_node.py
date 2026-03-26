from langchain_core.runnables import RunnableConfig
from langgraph.store.base import BaseStore

from .types import AgentState


def error_router_node(state: AgentState, config: RunnableConfig, store: BaseStore) -> dict[str, str]:
    del config, store
    retry_count = int(state.get("retry_count", 0) or 0)
    max_retry = 2
    if state.get("tool_error") and retry_count < max_retry:
        route = "retry_sql"
    elif state.get("tool_error"):
        route = "final_error"
    else:
        route = "to_rerank"
    return {"route": route}


def route_by_error(state: AgentState) -> str:
    route = state.get("route")
    if route == "retry_sql":
        return "sql_search_node"
    if route == "final_error":
        return "final_error_node"
    return "rerank_retrieve_node"


if __name__ == "__main__":
    ok = error_router_node({"tool_error": None}, config={}, store=None)
    err_retry = error_router_node({"tool_error": "x", "retry_count": 1}, config={}, store=None)
    err_final = error_router_node({"tool_error": "x", "retry_count": 2}, config={}, store=None)
    print("ok_route:", ok, route_by_error(ok))
    print("err_retry_route:", err_retry, route_by_error(err_retry))
    print("err_final_route:", err_final, route_by_error(err_final))
