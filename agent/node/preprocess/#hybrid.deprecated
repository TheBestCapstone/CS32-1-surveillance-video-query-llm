import logging
import os
import time
from typing import Any, Dict, List, Optional

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.store.base import BaseStore

from node.preprocess.analyzer import QueryAnalyzer, SQLSanitizer
from node.preprocess.base import BasePreprocessor, SearchMode
from node.preprocess.prompts import (
    HYBRID_OUTPUT_SCHEMA,
    HYBRID_SEARCH_PROMPT,
    REWRITE_OUTPUT_SCHEMA,
    REWRITE_PROMPT,
)
from node.preprocess.schema import get_schema_registry
from node.types import AgentState, InputValidator

logger = logging.getLogger(__name__)


class HybridSearchPreprocessor(BasePreprocessor):
    def __init__(self, llm: Any = None):
        super().__init__("HybridSearchPreprocess", llm)
        self.query_analyzer = QueryAnalyzer()
        self.schema_registry = get_schema_registry()

    def get_system_prompt(self, memory_context: str, table_name: str = "video_events") -> str:
        filterable_fields_prompt = self._get_filterable_fields_prompt(table_name)
        prompt = HYBRID_SEARCH_PROMPT
        if filterable_fields_prompt:
            prompt += f"\n\n## 数据库表结构\n{filterable_fields_prompt}"
        if memory_context:
            prompt += f"\n\n## 记忆上下文\n{memory_context}"
        return prompt

    def _get_filterable_fields_prompt(self, table_name: str) -> str:
        schema = self.schema_registry.get_schema(table_name)
        if schema is None:
            return ""
        lines = [f"表名: {table_name}", "可过滤字段:"]
        for field in schema.get_filterable_fields():
            lines.append(f"  - {field['name']}: {field['description']} (类型: {field['type']})")
        lines.append("\n可搜索字段(语义向量):")
        for field in schema.get_searchable_fields():
            lines.append(f"  - {field['name']}: {field['description']}")
        return "\n".join(lines)

    def get_user_prompt_template(self) -> str:
        return "用户查询: {user_query}\n\n请输出JSON格式的解析结果。"

    def get_output_schema(self) -> Dict[str, Any]:
        return HYBRID_OUTPUT_SCHEMA

    def preprocess(self, state: AgentState, config: RunnableConfig, store: BaseStore) -> dict[str, Any]:
        start_time = time.time()
        
        user_query = InputValidator.extract_latest_query(state)
        thread_id = str((config or {}).get("configurable", {}).get("thread_id", "default"))

        logger.info(f"[{self.name}] 开始预处理, query={user_query[:50]}")

        query_analysis = self.query_analyzer.analyze_query(user_query)
        recommended_mode = query_analysis["recommended_mode"]

        memory_block = self._get_memory_context(store, thread_id)
        payload, llm_time = self._call_llm(user_query, memory_block, config, recommended_mode)

        if recommended_mode == SearchMode.DIRECT_SEMANTIC:
            rewritten = payload.get("rewritten_query")
            if not rewritten:
                rewritten = user_query if user_query else "未知查询"
            meta_list = []
            event_list = [rewritten]
            payload = {"event": rewritten}
        else:
            payload = self._post_process_payload(payload, user_query if user_query else "未知查询")
            meta_list, event_list = self._build_meta_list(payload, user_query if user_query else "未知查询")

        sql_filter_applied = recommended_mode == SearchMode.SQL_FILTER_SEMANTIC
        search_mode = recommended_mode

        if store is not None:
            store.put(("capstone", "memory"), thread_id, f"用户: {user_query}\n解析: {payload}")

        elapsed_time = time.time() - start_time
        performance_metrics = {
            "total_time": elapsed_time,
            "llm_time": llm_time,
            "postprocess_time": elapsed_time - llm_time,
        }

        logger.info(f"[{self.name}] 完成, mode={search_mode}, event_count={len(event_list)}, meta_count={len(meta_list)}, elapsed={elapsed_time:.3f}s")

        return {
            "parsed_question": payload,
            "meta_list": meta_list,
            "event_list": event_list,
            "user_query": user_query,
            "search_mode": search_mode.value,
            "sql_filter_applied": sql_filter_applied,
            "thought": f"{self.name}完成: mode={search_mode.value}, event={event_list}, meta={len(meta_list)}",
            "messages": [AIMessage(content=f"[{self.name}] 预处理完成: 模式={search_mode.value}, 提取到{len(event_list)}个事件关键词")],
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

    def _call_llm(self, user_query: str, memory_block: str, config: RunnableConfig, mode: SearchMode) -> tuple[Dict[str, Any], float]:
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

            if mode == SearchMode.DIRECT_SEMANTIC:
                system_prompt = REWRITE_PROMPT
                if memory_block:
                    system_prompt += f"\n\n## 记忆上下文\n{memory_block}"
                schema = REWRITE_OUTPUT_SCHEMA
                user_prompt = f"用户查询: {user_query}\n\n请输出JSON格式的解析结果。"
            else:
                system_prompt = self.get_system_prompt(memory_block)
                schema = self.get_output_schema()
                user_prompt = self.get_user_prompt_template().format(user_query=user_query)

            structured_llm = actual_llm.with_structured_output(schema)
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
            logger.warning(f"[{self.name}] LLM调用失败, 使用默认输出: {exc}")
            safe_query = user_query if user_query else "未知查询"
            if mode == SearchMode.DIRECT_SEMANTIC:
                payload = {"rewritten_query": safe_query}
            else:
                payload = {"event": safe_query, "color": None, "time": None, "move": None, "object": None}

        llm_time = time.time() - start_time
        return payload, llm_time

    def _post_process_payload(self, payload: Dict[str, Any], original_query: str) -> Dict[str, Any]:
        if payload.get("event") is None or payload.get("event") == "":
            payload["event"] = original_query
        if payload.get("color"):
            payload["color"] = SQLSanitizer.sanitize_color(payload["color"])
        if payload.get("object"):
            payload["object"] = SQLSanitizer.sanitize_string(payload["object"], max_length=50)
        return payload

    def _build_meta_list(self, payload: Dict[str, Any], original_query: str) -> tuple[List[Dict[str, Any]], List[str]]:
        meta_list: List[Dict[str, Any]] = []
        event_list: List[str] = []

        event = payload.get("event")
        if event and event.strip():
            event_list.append(event.strip())

        color = payload.get("color")
        if color:
            meta_list.append({"field": "object_color_cn", "op": "contains", "value": color, "type": "string"})

        time_text = payload.get("time")
        if time_text:
            time_filters = self._parse_time_condition(time_text)
            meta_list.extend(time_filters)

        move = payload.get("move")
        if move is not None:
            move_value = "静止" if not move else "运动"
            meta_list.append({"field": "appearance_notes_cn", "op": "contains", "value": move_value, "type": "string"})

        obj = payload.get("object")
        if obj:
            meta_list.append({"field": "object_type_cn", "op": "contains", "value": obj, "type": "string"})

        if not meta_list and not event_list:
            event_list.append(original_query)

        return meta_list, event_list

    def _parse_time_condition(self, time_text: str) -> List[Dict[str, Any]]:
        import re
        filters: List[Dict[str, Any]] = []
        range_match = re.match(r"^\s*(\d+(?:\.\d+)?)\s*[-~到至]\s*(\d+(?:\.\d+)?)\s*$", time_text)
        if range_match:
            filters.append({"field": "start_time", "op": ">=", "value": float(range_match.group(1)), "type": "float"})
            filters.append({"field": "end_time", "op": "<=", "value": float(range_match.group(2)), "type": "float"})
            return filters

        time_keywords = {
            "今天": (0.0, 86400.0),
            "今日": (0.0, 86400.0),
            "当天": (0.0, 86400.0),
            "上午": (0.0, 43200.0),
            "中午": (36000.0, 50400.0),
            "下午": (43200.0, 86400.0),
            "晚上": (54000.0, 86400.0),
        }

        for keyword, (start, end) in time_keywords.items():
            if keyword in time_text:
                filters.append({"field": "start_time", "op": ">=", "value": start, "type": "float"})
                filters.append({"field": "end_time", "op": "<=", "value": end, "type": "float"})
                break

        return filters
