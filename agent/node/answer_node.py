from typing import Any

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.store.base import BaseStore

from .types import AgentState


def final_answer_node(state: AgentState, config: RunnableConfig, store: BaseStore) -> dict[str, Any]:
    del config, store
    rows = state.get("rerank_result", [])
    if not rows:
        final_answer = "未检索到匹配结果。你可以补充更具体的颜色、时间或动作描述。"
        return {"final_answer": final_answer, "messages": [AIMessage(content=final_answer)]}
    parts: list[str] = []
    for idx, row in enumerate(rows[:3], start=1):
        parts.append(
            f"[{idx}] event_id={row.get('event_id')} | video={row.get('video_id')} | "
            f"time={row.get('start_time')}-{row.get('end_time')} | "
            f"distance={row.get('_distance')} | summary={row.get('event_summary_cn')}"
        )
    final_answer = "检索完成，最相关结果如下：\n" + "\n".join(parts)
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
