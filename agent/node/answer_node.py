from typing import Any

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.store.base import BaseStore

from .types import AgentState


def final_answer_node(state: AgentState, config: RunnableConfig, store: BaseStore) -> dict[str, Any]:
    del config, store
    rows = state.get("rerank_result") or state.get("hybrid_result") or state.get("sql_result") or []
    
    agent_summary = ""
    if state.get("sql_debug") and isinstance(state.get("sql_debug"), dict):
        agent_summary = state["sql_debug"].get("agent_summary", "")
    elif state.get("search_explain"):
        agent_summary = state.get("search_explain", "")
        
    if not rows:
        final_answer = agent_summary if agent_summary else "No matching results found. You can add more specific descriptions like colors or actions."
        return {"final_answer": final_answer, "messages": [AIMessage(content=final_answer)]}
        
    parts: list[str] = []
    if agent_summary:
        parts.append(agent_summary + "\n\nDetailed results:")
    else:
        parts.append("Retrieval complete. Most relevant results:")
        
    for idx, row in enumerate(rows[:5], start=1):
        parts.append(
            f"[{idx}] event_id={row.get('event_id')} | video={row.get('video_id')} | "
            f"distance={row.get('_distance', 'N/A')} | summary={row.get('event_summary_en', row.get('event_text_cn', 'N/A'))}"
        )
    final_answer = "\n".join(parts)
    return {"final_answer": final_answer, "messages": [AIMessage(content=final_answer)]}


def final_error_node(state: AgentState, config: RunnableConfig, store: BaseStore) -> dict[str, Any]:
    del config, store
    final_answer = f"检索流程执行失败：{state.get('tool_error')}"
    return {"final_answer": final_answer, "messages": [AIMessage(content=final_answer)]}


if __name__ == "__main__":
    rows = [
        {
            "event_id": 1,
            "video_id": "demo.mp4",
            "start_time": 10,
            "end_time": 20,
            "_distance": 0.12,
            "event_summary_cn": "红色目标进入画面",
        }
    ]
    print(final_answer_node({"rerank_result": rows}, config={}, store=None)["final_answer"])
    print(final_error_node({"tool_error": "SQL检索失败"}, config={}, store=None)["final_answer"])
