import os
from pathlib import Path
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.store.base import BaseStore

from .types import AgentState, question_to_meta_and_event

SYSTEM_PROMPT = """你是一个视频监控查询优化助手。你的任务是将用户的自然语言查询转换为结构化的检索条件。

请分析用户查询，提取以下信息：
1. event: 事件类型（如进入、离开、停止、移动等）
2. color: 目标颜色（如红色、蓝色、白色、黑色等）
3. time: 时间条件（如今天、上午、具体时间段等）
4. move: 运动状态（true表示运动中，false表示静止）

请直接输出JSON格式的结构化结果，不要有多余的解释。"""

USER_PROMPT = """分析以下用户查询，提取结构化信息：

用户查询: {user_query}
工具类型: {tool_mode}

请输出JSON格式，例如：
{{"event": "进入", "color": "红色", "time": "今天", "move": true}}"""


def create_preprocess_node(llm: Any = None):
    def preprocess_node(state: AgentState, config: RunnableConfig, store: BaseStore) -> dict[str, Any]:
        user_query = state.get("user_query", "")
        tool_choice = state.get("tool_choice", {})
        tool_mode = tool_choice.get("mode", "hybrid")

        thread_id = str((config or {}).get("configurable", {}).get("thread_id", "default"))
        memory_block = ""
        if store is not None:
            memory_item = store.get(("capstone", "memory"), thread_id)
            if memory_item is not None and getattr(memory_item, "value", None) is not None:
                memory_value = memory_item.value
                memory_block = memory_value if isinstance(memory_value, str) else str(memory_value)

        system_prompt = SYSTEM_PROMPT
        if memory_block:
            system_prompt = f"{SYSTEM_PROMPT}\n\n历史上下文:\n{memory_block}"

        try:
            actual_llm = llm
            if actual_llm is None:
                from langchain_openai import ChatOpenAI
                actual_llm = ChatOpenAI(
                    model_name="qwen3-max",
                    temperature=1.0,
                    api_key=os.getenv("DASHSCOPE_API_KEY"),
                    base_url=os.getenv("DASHSCOPE_URL"),
                )

            messages = [
                HumanMessage(content=system_prompt),
                HumanMessage(content=USER_PROMPT.format(user_query=user_query, tool_mode=tool_mode)),
            ]
            response = actual_llm.invoke(messages)
            raw_content = response.content if hasattr(response, "content") else str(response)

            import json
            try:
                parsed = json.loads(raw_content)
            except json.JSONDecodeError:
                raw_content = raw_content.strip()
                if raw_content.startswith("```"):
                    lines = raw_content.split("\n")
                    raw_content = "\n".join(lines[1:-1])
                try:
                    parsed = json.loads(raw_content)
                except json.JSONDecodeError:
                    parsed = {"event": user_query, "color": None, "time": None, "move": None}

        except Exception:
            parsed = {"event": user_query, "color": None, "time": None, "move": None}

        meta_list, event_list = question_to_meta_and_event(parsed)

        if store is not None:
            store.put(("capstone", "memory"), thread_id, f"用户: {user_query}\n解析: {parsed}")

        thought = f"预处理完成: tool={tool_mode}, event={event_list}, meta_count={len(meta_list)}"

        return {
            "parsed_question": parsed,
            "meta_list": meta_list,
            "event_list": event_list,
            "thought": thought,
            "messages": [AIMessage(content=f"预处理完成({tool_mode}): 提取到{len(event_list)}个事件关键词")],
        }

    return preprocess_node


if __name__ == "__main__":
    node = create_preprocess_node()
    out = node({
        "user_query": "红色车辆进入镜头",
        "tool_choice": {"mode": "hybrid"},
    }, config={}, store=None)
    print("event_list:", out.get("event_list"))
    print("meta_list:", out.get("meta_list"))