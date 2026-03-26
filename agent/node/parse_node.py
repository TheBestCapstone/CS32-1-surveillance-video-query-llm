from typing import Any
import json

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.store.base import BaseStore

from .types import AgentState, ParsedQuestion, content_to_text, question_to_meta_and_event


def build_system_prompt(memory_block: str) -> str:
    prompt = (
    "### Role\n"
    "你是一个面向视频监控检索系统的语义解析助手，负责将用户的自然语言查询解析为结构化检索条件。"
    "你的输出将直接用于后续检索模块，因此必须准确、克制、结构化，并尽量避免主观臆测。\n\n"

    "### Objective\n"
    "请根据用户当前输入，并结合【记忆上下文】进行增量语义解析，输出标准 JSON，作为视频检索条件。\n\n"

    "### Parsing Principles\n"
    "1. 结合当前输入和记忆上下文进行解析。\n"
    "2. 若用户本轮输入是对上一轮条件的补充、修正或细化，应在已有语义基础上增量更新。\n"
    "3. 若某字段在当前输入中未被提及，且记忆上下文中存在有效值，则保留原值。\n"
    "4. 若当前输入明确否定、替换或修正某字段，应以当前输入为准。\n"
    "5. 不得凭空补充用户未表达的信息；无法确定时输出 null。\n\n"

    "### Field Definitions\n"
    "请提取以下字段：\n"
    "1. event:\n"
    "   - 表示核心检索事件。\n"
    "   - 必须将用户问题改写为适合检索的陈述句，而不是疑问句。\n"
    "   - 应尽量保留目标对象、行为、场景关系等核心语义。\n"
    "   - 例如：\n"
    "     - 用户输入：'有没有人从门口进来？'\n"
    "       输出：'有人从门口进入'\n"
    "     - 用户输入：'找红车停在路边'\n"
    "       输出：'红色车辆停在路边'\n\n"

    "2. color:\n"
    "   - 表示目标对象颜色。\n"
    "   - 仅提取明确提到的颜色信息。\n"
    "   - 若未提及则输出 null。\n\n"

    "3. time:\n"
    "   - 表示时间范围、时间点或相对时间表达。\n"
    "   - 保留用户原始时间语义，如：'昨天下午'、'3点到5点'、'晚上'。\n"
    "   - 若未提及则输出 null。\n\n"

    "4. move:\n"
    "   - 表示目标是否处于运动状态。\n"
    "   - 若用户明确表达目标在移动、行驶、奔跑、经过、进入、离开等动态状态，则输出 true。\n"
    "   - 若用户明确表达目标静止、停留、停放、站着、不动等静态状态，则输出 false。\n"
    "   - 若无法判断，则输出 null。\n\n"

    "### Output Constraints\n"
    "1. 必须严格输出 JSON，不要输出任何解释、注释、前缀或额外文本。\n"
    "2. 所有字段都必须出现。\n"
    "3. 未知、缺失或无法确定的字段统一输出 null。\n"
    "4. JSON schema 如下：\n"
    "{\n"
    '  "event": string | null,\n'
    '  "color": string | null,\n'
    '  "time": string | null,\n'
    '  "move": boolean | null\n'
    "}\n\n"

    "### Memory Context\n"
    f"{memory_block}\n\n"

    "### User Input\n"
    "请开始解析："
    )
    return prompt


def create_parse_node(llm: Any):
    def parse_node(state: AgentState, config: RunnableConfig, store: BaseStore) -> dict[str, Any]:
        messages = state.get("messages", [])
        if not messages:
            return {"messages": [AIMessage(content="请先输入问题")]}
        last_message = messages[-1]
        if hasattr(last_message, "content"):
            raw_content = last_message.content
        elif isinstance(last_message, dict):
            raw_content = last_message.get("content", "")
        else:
            raw_content = last_message
        user_text = content_to_text(raw_content)
        thread_id = str((config or {}).get("configurable", {}).get("thread_id", "default"))
        memory_item = store.get(("capstone", "memory"), thread_id)
        memory_block = ""
        if memory_item is not None and getattr(memory_item, "value", None) is not None:
            memory_value = memory_item.value
            memory_block = memory_value if isinstance(memory_value, str) else str(memory_value)
        system_prompt = build_system_prompt(memory_block)
        structured_llm = llm.with_structured_output(ParsedQuestion)
        question = structured_llm.invoke(
            [SystemMessage(content=system_prompt), HumanMessage(content=user_text)],
            config=config,
        )
        if hasattr(question, "model_dump"):
            payload = question.model_dump()
            payload_text = question.model_dump_json(ensure_ascii=False)
        elif isinstance(question, dict):
            payload = question
            payload_text = json.dumps(payload, ensure_ascii=False)
        else:
            payload = dict(question)
            payload_text = json.dumps(payload, ensure_ascii=False)
        meta_list, event_list = question_to_meta_and_event(payload)
        store.put(("capstone", "parsed_question"), thread_id, payload)
        return {
            "messages": [AIMessage(content=f"问题解析完成: {payload_text}")],
            "parsed_question": payload,
            "meta_list": meta_list,
            "event_list": event_list,
            "tool_error": None,
            "retry_count": 0,
            "sql_result": [],
            "rerank_result": [],
            "route": "",
        }

    return parse_node


if __name__ == "__main__":
    from langchain_core.messages import HumanMessage

    class FakeStructuredLLM:
        def invoke(self, messages, config=None):
            del messages, config
            return {"event": "女人进入", "color": "红色", "time": "null", "move": True}

    class FakeLLM:
        def with_structured_output(self, schema):
            del schema
            return FakeStructuredLLM()

    class FakeStore:
        def get(self, namespace, key):
            del namespace, key
            return None

        def put(self, namespace, key, value):
            del namespace, key, value

    node = create_parse_node(FakeLLM())
    out = node({"messages": [HumanMessage(content="找红色目标")]}, {"configurable": {"thread_id": "t1"}}, FakeStore())
    print(out["parsed_question"])
    out_dict = node({"messages": [{"type": "human", "content": "找红色目标"}]}, {"configurable": {"thread_id": "t2"}}, FakeStore())
    print(out_dict["parsed_question"])
