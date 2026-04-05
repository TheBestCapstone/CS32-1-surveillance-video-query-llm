import logging
import os
import re
import time
from typing import Any, Dict, List

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.store.base import BaseStore

from node.preprocess.analyzer import SQLSanitizer
from node.preprocess.base import BasePreprocessor, SearchMode
from node.preprocess.prompts import PURE_SQL_OUTPUT_SCHEMA, PURE_SQL_PROMPT
from node.types import AgentState, InputValidator

logger = logging.getLogger(__name__)


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
        start_time = time.time()
        
        user_query = InputValidator.extract_latest_query(state)
        thread_id = str((config or {}).get("configurable", {}).get("thread_id", "default"))

        logger.info(f"[{self.name}] 开始预处理, query={user_query[:50]}")

        memory_block = self._get_memory_context(store, thread_id)
        payload, llm_time = self._call_llm(user_query, memory_block, config)
        payload = self._post_process_payload(payload)

        event_list: List[str] = []
        if payload.get("object_type"):
            event_list.append(payload["object_type"])

        meta_list = self._build_meta_list(payload)

        if store is not None:
            store.put(("capstone", "memory"), thread_id, f"用户: {user_query}\n解析: {payload}")

        normalized_query = user_query.strip()
        elapsed_time = time.time() - start_time
        performance_metrics = {
            "total_time": elapsed_time,
            "llm_time": llm_time,
            "postprocess_time": elapsed_time - llm_time,
        }

        logger.info(f"[{self.name}] 完成, meta_count={len(meta_list)}, elapsed={elapsed_time:.3f}s")

        return {
            "parsed_question": payload,
            "meta_list": meta_list,
            "event_list": event_list,
            "user_query": normalized_query,
            "search_mode": SearchMode.SQL_FILTER_SEMANTIC.value,
            "sql_filter_applied": True,
            "thought": f"{self.name}完成: meta={len(meta_list)}, event={event_list}",
            "messages": [AIMessage(content=f"[{self.name}] 预处理完成: 生成{len(meta_list)}个元数据过滤条件")],
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
            payload = {"color": None, "time": None, "move": None, "object_type": None}

        llm_time = time.time() - start_time
        return payload, llm_time

    def _post_process_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if payload.get("color"):
            payload["color"] = SQLSanitizer.sanitize_color(payload["color"])
        if payload.get("object_type"):
            payload["object_type"] = SQLSanitizer.sanitize_string(payload["object_type"], max_length=50)
        return payload

    def _build_meta_list(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        meta_list: List[Dict[str, Any]] = []

        if payload.get("color"):
            meta_list.append({"field": "object_color_cn", "op": "contains", "value": payload["color"], "type": "string"})

        if payload.get("time"):
            time_text = payload["time"]
            range_match = re.match(r"^\s*(\d+(?:\.\d+)?)\s*[-~到至]\s*(\d+(?:\.\d+)?)\s*$", time_text)
            if range_match:
                meta_list.append({"field": "start_time", "op": ">=", "value": float(range_match.group(1)), "type": "float"})
                meta_list.append({"field": "end_time", "op": "<=", "value": float(range_match.group(2)), "type": "float"})
            elif time_text in {"今天", "今日", "当天"}:
                meta_list.append({"field": "start_time", "op": ">=", "value": 0.0, "type": "float"})
                meta_list.append({"field": "end_time", "op": "<=", "value": 86400.0, "type": "float"})
            elif time_text in {"上午"}:
                meta_list.append({"field": "start_time", "op": ">=", "value": 0.0, "type": "float"})
                meta_list.append({"field": "end_time", "op": "<=", "value": 43200.0, "type": "float"})
            elif time_text in {"下午"}:
                meta_list.append({"field": "start_time", "op": ">=", "value": 43200.0, "type": "float"})
                meta_list.append({"field": "end_time", "op": "<=", "value": 86400.0, "type": "float"})

        if payload.get("move") is not None:
            move_value = "静止" if not payload["move"] else "运动"
            meta_list.append({"field": "appearance_notes_cn", "op": "contains", "value": move_value, "type": "string"})

        if payload.get("object_type"):
            meta_list.append({"field": "object_type_cn", "op": "contains", "value": payload["object_type"], "type": "string"})

        return meta_list
