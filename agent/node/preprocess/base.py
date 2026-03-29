import os
import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypedDict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.store.base import BaseStore

from node.types import AgentState, content_to_text, question_to_meta_and_event


class PreprocessInput(TypedDict):
    user_query: str
    tool_mode: str
    memory_context: Optional[str]
    config: Optional[RunnableConfig]
    store: Optional[BaseStore]


class PreprocessOutput(TypedDict):
    parsed_question: Dict[str, Any]
    meta_list: List[Dict[str, Any]]
    event_list: List[str]
    normalized_query: str
    tool_mode: str
    preprocessing_applied: bool


class BasePreprocessor(ABC):
    def __init__(self, name: str, llm: Any = None):
        self.name = name
        self.llm = llm

    @abstractmethod
    def get_system_prompt(self, memory_context: str) -> str:
        pass

    @abstractmethod
    def get_user_prompt_template(self) -> str:
        pass

    @abstractmethod
    def get_output_schema(self) -> Dict[str, Any]:
        pass

    def get_default_output(self, user_query: str, tool_mode: str) -> PreprocessOutput:
        payload = {"event": user_query, "color": None, "time": None, "move": None}
        meta_list, event_list = question_to_meta_and_event(payload)
        return PreprocessOutput(
            parsed_question=payload,
            meta_list=meta_list,
            event_list=event_list,
            normalized_query=user_query,
            tool_mode=tool_mode,
            preprocessing_applied=False,
        )

    def preprocess(self, state: AgentState, config: RunnableConfig, store: BaseStore) -> dict[str, Any]:
        user_query = state.get("user_query", "")
        tool_mode = state.get("tool_choice", {}).get("mode", "hybrid")
        thread_id = str((config or {}).get("configurable", {}).get("thread_id", "default"))

        memory_block = ""
        if store is not None:
            memory_item = store.get(("capstone", "memory"), thread_id)
            if memory_item is not None and getattr(memory_item, "value", None) is not None:
                memory_value = memory_item.value
                memory_block = memory_value if isinstance(memory_value, str) else str(memory_value)

        try:
            actual_llm = self.llm
            if actual_llm is None:
                from langchain_openai import ChatOpenAI
                actual_llm = ChatOpenAI(
                    model_name="qwen3-max",
                    temperature=0.0,
                    api_key=os.getenv("DASHSCOPE_API_KEY"),
                    base_url=os.getenv("DASHSCOPE_URL"),
                )

            system_prompt = self.get_system_prompt(memory_block)
            user_prompt = self.get_user_prompt_template().format(user_query=user_query, tool_mode=tool_mode)

            structured_llm = actual_llm.with_structured_output(self.get_output_schema())
            result = structured_llm.invoke(
                [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)],
                config=config,
            )

            if hasattr(result, "model_dump"):
                payload = result.model_dump()
            elif isinstance(result, dict):
                payload = result
            else:
                payload = dict(result)

        except Exception as exc:
            payload = {"event": user_query, "color": None, "time": None, "move": None}

        meta_list, event_list = question_to_meta_and_event(payload)

        if store is not None:
            store.put(("capstone", "memory"), thread_id, f"用户: {user_query}\n解析: {payload}")

        normalized_query = user_query.strip()
        output = PreprocessOutput(
            parsed_question=payload,
            meta_list=meta_list,
            event_list=event_list,
            normalized_query=normalized_query,
            tool_mode=tool_mode,
            preprocessing_applied=True,
        )

        return {
            "parsed_question": output["parsed_question"],
            "meta_list": output["meta_list"],
            "event_list": output["event_list"],
            "user_query": output["normalized_query"],
            "thought": f"{self.name}完成: event={event_list}, meta={len(meta_list)}",
            "messages": [AIMessage(content=f"[{self.name}] 预处理完成: 提取到{len(event_list)}个事件关键词")],
        }


HYBRID_SEARCH_PROMPT = """你是一个视频监控检索系统的语义解析助手。

## 任务
将用户的自然语言查询解析为结构化检索条件，用于混合向量检索和SQL元数据过滤。

## 输入字段
1. event: 核心检索事件（进入、离开、移动、停止等）
2. color: 目标颜色（红色、蓝色、白色、黑色等）
3. time: 时间条件（今天、上午、具体时间段等）
4. move: 运动状态（true运动中，false静止）

## 解析原则
1. 将用户问题改写为适合检索的陈述句
2. 保留目标对象、行为、场景关系等核心语义
3. 不得凭空补充用户未表达的信息

## 输出
直接输出JSON，不要额外解释。"""


PURE_SQL_PROMPT = """你是一个视频监控元数据查询优化助手。

## 任务
将用户的自然语言查询转换为精确的SQL元数据过滤条件。

## 重点字段
1. color: 精确颜色值（红色、蓝色、白色、黑色、银色等）
2. time: 精确时间范围（今天、上午9点到12点、2024-01-01等）
3. move: 运动状态（true=运动中，false=静止）
4. object_type: 目标类型（车辆、行人、自行车、摩托车等）

## 解析原则
1. 颜色必须精确匹配数据库中的标准颜色值
2. 时间范围需要转换为具体的起止时间戳
3. 运动状态只提取用户明确表达的

## 输出
直接输出JSON，不要额外解释。"""


VIDEO_VECT_PROMPT = """你是一个视频语义理解助手。

## 任务
将用户的自然语言查询转换为适合语义向量检索的表述。

## 重点字段
1. event: 核心语义事件（车辆驶入、行人横穿、物体遗落、人物徘徊等）
2. scene: 场景描述（道路、停车场、门口、斑马线等）
3. behavior: 行为描述（缓慢、快速、突然、持续等）
4. object: 目标描述（小型车、大型车、行人、骑行者等）

## 解析原则
1. 事件描述应具有良好的语义区分度
2. 使用标准化的视频监控领域词汇
3. 保持原始语义不过度简化

## 输出
直接输出JSON，不要额外解释。"""


HYBRID_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "event": {"type": "string"},
        "color": {"type": "string"},
        "time": {"type": "string"},
        "move": {"type": "boolean"},
    },
    "required": ["event", "color", "time", "move"],
}

PURE_SQL_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "color": {"type": "string"},
        "time": {"type": "string"},
        "move": {"type": "boolean"},
        "object_type": {"type": "string"},
    },
    "required": ["color", "time", "move", "object_type"],
}

VIDEO_VECT_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "event": {"type": "string"},
        "scene": {"type": "string"},
        "behavior": {"type": "string"},
        "object": {"type": "string"},
    },
    "required": ["event", "scene", "behavior", "object"],
}


class HybridSearchPreprocessor(BasePreprocessor):
    def __init__(self, llm: Any = None):
        super().__init__("HybridSearchPreprocess", llm)

    def get_system_prompt(self, memory_context: str) -> str:
        prompt = HYBRID_SEARCH_PROMPT
        if memory_context:
            prompt += f"\n\n## 记忆上下文\n{memory_context}"
        return prompt

    def get_user_prompt_template(self) -> str:
        return "用户查询: {user_query}\n\n请输出JSON格式的解析结果。"

    def get_output_schema(self) -> Dict[str, Any]:
        return HYBRID_OUTPUT_SCHEMA


class PureSQLPreprocessor(BasePreprocessor):
    def __init__(self, llm: Any = None):
        super().__init__("PureSQLPreprocess", llm)

    def get_system_prompt(self, memory_context: str) -> str:
        prompt = PURE_SQL_PROMPT
        if memory_context:
            prompt += f"\n\n## 记忆上下文\n{memory_context}"
        return prompt

    def get_user_prompt_template(self) -> str:
        return "用户查询: {user_query}\n\n请输出JSON格式的元数据过滤条件。"

    def get_output_schema(self) -> Dict[str, Any]:
        return PURE_SQL_OUTPUT_SCHEMA

    def preprocess(self, state: AgentState, config: RunnableConfig, store: BaseStore) -> dict[str, Any]:
        user_query = state.get("user_query", "")
        tool_mode = "pure_sql"
        thread_id = str((config or {}).get("configurable", {}).get("thread_id", "default"))

        memory_block = ""
        if store is not None:
            memory_item = store.get(("capstone", "memory"), thread_id)
            if memory_item is not None and getattr(memory_item, "value", None) is not None:
                memory_value = memory_item.value
                memory_block = memory_value if isinstance(memory_value, str) else str(memory_value)

        try:
            actual_llm = self.llm
            if actual_llm is None:
                from langchain_openai import ChatOpenAI
                actual_llm = ChatOpenAI(
                    model_name="qwen3-max",
                    temperature=0.0,
                    api_key=os.getenv("DASHSCOPE_API_KEY"),
                    base_url=os.getenv("DASHSCOPE_URL"),
                )

            system_prompt = self.get_system_prompt(memory_block)
            user_prompt = self.get_user_prompt_template().format(user_query=user_query, tool_mode=tool_mode)

            structured_llm = actual_llm.with_structured_output(self.get_output_schema())
            result = structured_llm.invoke(
                [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)],
                config=config,
            )

            if hasattr(result, "model_dump"):
                payload = result.model_dump()
            elif isinstance(result, dict):
                payload = result
            else:
                payload = dict(result)

        except Exception:
            payload = {"color": None, "time": None, "move": None, "object_type": None}

        event_list: List[str] = []
        if payload.get("object_type"):
            event_list.append(payload["object_type"])

        meta_list = self._build_meta_list(payload)

        if store is not None:
            store.put(("capstone", "memory"), thread_id, f"用户: {user_query}\n解析: {payload}")

        normalized_query = user_query.strip()
        return {
            "parsed_question": payload,
            "meta_list": meta_list,
            "event_list": event_list,
            "user_query": normalized_query,
            "thought": f"{self.name}完成: meta={len(meta_list)}, event={event_list}",
            "messages": [AIMessage(content=f"[{self.name}] 预处理完成: 生成{len(meta_list)}个元数据过滤条件")],
        }

    def _build_meta_list(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        meta_list: List[Dict[str, Any]] = []

        if payload.get("color"):
            meta_list.append({"field": "object_color_cn", "op": "contains", "value": payload["color"]})

        if payload.get("time"):
            time_text = payload["time"]
            import re
            range_match = re.match(r"^\s*(\d+(?:\.\d+)?)\s*[-~到至]\s*(\d+(?:\.\d+)?)\s*$", time_text)
            if range_match:
                meta_list.append({"field": "start_time", "op": ">=", "value": float(range_match.group(1))})
                meta_list.append({"field": "end_time", "op": "<=", "value": float(range_match.group(2))})
            elif time_text in {"今天", "今日", "当天"}:
                meta_list.append({"field": "start_time", "op": ">=", "value": 0.0})
                meta_list.append({"field": "end_time", "op": "<=", "value": 86400.0})
            elif time_text in {"上午"}:
                meta_list.append({"field": "start_time", "op": ">=", "value": 0.0})
                meta_list.append({"field": "end_time", "op": "<=", "value": 43200.0})
            elif time_text in {"下午"}:
                meta_list.append({"field": "start_time", "op": ">=", "value": 43200.0})
                meta_list.append({"field": "end_time", "op": "<=", "value": 86400.0})

        if payload.get("move") is not None:
            move_value = "静止" if not payload["move"] else "运动"
            meta_list.append({"field": "appearance_notes_cn", "op": "contains", "value": move_value})

        if payload.get("object_type"):
            meta_list.append({"field": "object_type_cn", "op": "contains", "value": payload["object_type"]})

        return meta_list


class VideoVectPreprocessor(BasePreprocessor):
    def __init__(self, llm: Any = None):
        super().__init__("VideoVectPreprocess", llm)

    def get_system_prompt(self, memory_context: str) -> str:
        prompt = VIDEO_VECT_PROMPT
        if memory_context:
            prompt += f"\n\n## 记忆上下文\n{memory_context}"
        return prompt

    def get_user_prompt_template(self) -> str:
        return "用户查询: {user_query}\n\n请输出JSON格式的语义解析结果。"

    def get_output_schema(self) -> Dict[str, Any]:
        return VIDEO_VECT_OUTPUT_SCHEMA

    def preprocess(self, state: AgentState, config: RunnableConfig, store: BaseStore) -> dict[str, Any]:
        user_query = state.get("user_query", "")
        tool_mode = "video_vect"
        thread_id = str((config or {}).get("configurable", {}).get("thread_id", "default"))

        memory_block = ""
        if store is not None:
            memory_item = store.get(("capstone", "memory"), thread_id)
            if memory_item is not None and getattr(memory_item, "value", None) is not None:
                memory_value = memory_item.value
                memory_block = memory_value if isinstance(memory_value, str) else str(memory_value)

        try:
            actual_llm = self.llm
            if actual_llm is None:
                from langchain_openai import ChatOpenAI
                actual_llm = ChatOpenAI(
                    model_name="qwen3-max",
                    temperature=0.0,
                    api_key=os.getenv("DASHSCOPE_API_KEY"),
                    base_url=os.getenv("DASHSCOPE_URL"),
                )

            system_prompt = self.get_system_prompt(memory_block)
            user_prompt = self.get_user_prompt_template().format(user_query=user_query, tool_mode=tool_mode)

            structured_llm = actual_llm.with_structured_output(self.get_output_schema())
            result = structured_llm.invoke(
                [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)],
                config=config,
            )

            if hasattr(result, "model_dump"):
                payload = result.model_dump()
            elif isinstance(result, dict):
                payload = result
            else:
                payload = dict(result)

        except Exception:
            payload = {"event": user_query, "scene": None, "behavior": None, "object": None}

        event_list: List[str] = []
        if payload.get("event"):
            event_list.append(payload["event"])
        if payload.get("scene"):
            event_list.append(payload["scene"])
        if payload.get("behavior"):
            event_list.append(payload["behavior"])
        if payload.get("object"):
            event_list.append(payload["object"])

        normalized_query = " ".join(filter(None, [payload.get("event", ""), payload.get("scene", "")]))

        if store is not None:
            store.put(("capstone", "memory"), thread_id, f"用户: {user_query}\n解析: {payload}")

        return {
            "parsed_question": payload,
            "meta_list": [],
            "event_list": event_list,
            "user_query": normalized_query or user_query,
            "thought": f"{self.name}完成: event={event_list}",
            "messages": [AIMessage(content=f"[{self.name}] 预处理完成: 提取到{len(event_list)}个语义关键词")],
        }


def create_hybrid_preprocess_node(llm: Any = None):
    preprocessor = HybridSearchPreprocessor(llm)
    def hybrid_preprocess(state: AgentState, config: RunnableConfig, store: BaseStore) -> dict[str, Any]:
        return preprocessor.preprocess(state, config, store)
    return hybrid_preprocess


def create_pure_sql_preprocess_node(llm: Any = None):
    preprocessor = PureSQLPreprocessor(llm)
    def pure_sql_preprocess(state: AgentState, config: RunnableConfig, store: BaseStore) -> dict[str, Any]:
        return preprocessor.preprocess(state, config, store)
    return pure_sql_preprocess


def create_video_vect_preprocess_node(llm: Any = None):
    preprocessor = VideoVectPreprocessor(llm)
    def video_vect_preprocess(state: AgentState, config: RunnableConfig, store: BaseStore) -> dict[str, Any]:
        return preprocessor.preprocess(state, config, store)
    return video_vect_preprocess


if __name__ == "__main__":
    class FakeStructuredLLM:
        def invoke(self, messages, config=None):
            return {"event": "进入", "color": "红色", "time": "今天", "move": True}

    class FakeLLM:
        def with_structured_output(self, schema):
            return FakeStructuredLLM()

    hybrid = create_hybrid_preprocess_node(FakeLLM())
    out = hybrid({"user_query": "红色车辆进入", "tool_choice": {"mode": "hybrid"}}, {}, None)
    print("hybrid:", out["event_list"])