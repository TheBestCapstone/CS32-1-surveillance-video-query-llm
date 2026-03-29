import logging
import os
import time
from typing import Any, Dict, List

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.store.base import BaseStore

from node.preprocess.base import BasePreprocessor, SearchMode
from node.preprocess.prompts import VIDEO_VECT_OUTPUT_SCHEMA, VIDEO_VECT_PROMPT
from node.types import AgentState, InputValidator

logger = logging.getLogger(__name__)


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
        start_time = time.time()
        
        user_query = InputValidator.extract_latest_query(state)
        thread_id = str((config or {}).get("configurable", {}).get("thread_id", "default"))

        logger.info(f"[{self.name}] 开始预处理, query={user_query[:50]}")

        memory_block = self._get_memory_context(store, thread_id)
        payload, llm_time = self._call_llm(user_query, memory_block, config)

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

        elapsed_time = time.time() - start_time
        performance_metrics = {
            "total_time": elapsed_time,
            "llm_time": llm_time,
            "postprocess_time": elapsed_time - llm_time,
        }

        logger.info(f"[{self.name}] 完成, event_count={len(event_list)}, elapsed={elapsed_time:.3f}s")

        return {
            "parsed_question": payload,
            "meta_list": [],
            "event_list": event_list,
            "user_query": normalized_query or user_query,
            "search_mode": SearchMode.DIRECT_SEMANTIC.value,
            "sql_filter_applied": False,
            "thought": f"{self.name}完成: event={event_list}",
            "messages": [AIMessage(content=f"[{self.name}] 预处理完成: 提取到{len(event_list)}个语义关键词")],
            "performance_metrics": performance_metrics,
        }

    def _get_memory_context(self, store: BaseStore, thread_id: str) -> str:
        if store is None:
            return ""
        memory_item = store.get(("capstone", "memory"), thread_id)
        if memory_item is not None and getattr(memory_item, "value", None) is not None:
            memory_value = memory_item.value
            return memory_value if isinstance(memory_value, str) else str(memory_value)
        return ""

    def _call_llm(self, user_query: str, memory_block: str, config: RunnableConfig) -> tuple[Dict[str, Any], float]:
        start_time = time.time()
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
            user_prompt = self.get_user_prompt_template().format(user_query=user_query)

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
            logger.warning(f"[{self.name}] LLM调用失败: {exc}")
            payload = {"event": user_query, "scene": None, "behavior": None, "object": None}

        llm_time = time.time() - start_time
        return payload, llm_time
