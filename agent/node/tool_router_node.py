import json
import logging
import os
from typing import Any, Dict, List, TypedDict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.store.base import BaseStore

from node.cot_engine import CoTContext, CoTEngine, SequentialCoTStep, StepStatus
from node.router_prompts import TOOL_ROUTER_QUADRUPLE_OUTPUT_SCHEMA, build_tool_router_quadruple_prompt
from node.types import AgentState, InputValidator, StateResetter, ToolChoice, question_to_meta_and_event

logger = logging.getLogger(__name__)

TOOL_DESCRIPTIONS = {
    "hybrid_search": {
        "name": "hybrid_search",
        "description": "地点驱动的混合检索，联合结构化过滤与向量相似度排序",
        "input": "四元组(object,color,location,event) + meta_list + event_list",
        "output": "检索结果列表，包含event_id, video_id, _distance, event_summary等字段",
        "scenarios": "当四元组中 location 非空时优先触发",
        "keywords": [],
    },
    "pure_sql": {
        "name": "pure_sql",
        "description": "无地点条件时的结构化过滤检索",
        "input": "四元组(object,color,event) + meta_list",
        "output": "符合条件的结果列表",
        "scenarios": "当四元组中 location 为空时优先触发",
        "keywords": [],
    },
    "video_vect": {
        "name": "video_vect",
        "description": "可插拔视频语义检索占位接口",
        "input": "event_list(语义事件表达)",
        "output": "语义相关的视频片段列表",
        "scenarios": "可按配置独立启用，不影响主路由",
        "keywords": [],
    },
}


class QueryQuadruple(TypedDict):
    object: List[str]
    color: List[str]
    location: List[str]
    event: str
    confidence: float
    source: str


def _router_config() -> Dict[str, Any]:
    return {
        "mode_with_location": os.getenv("TOOL_ROUTER_MODE_WITH_LOCATION", "hybrid_search"),
        "mode_without_location": os.getenv("TOOL_ROUTER_MODE_WITHOUT_LOCATION", "pure_sql"),
        "video_vect_mode": os.getenv("TOOL_ROUTER_VIDEO_VECT_MODE", "video_vect"),
        "force_parallel": os.getenv("TOOL_ROUTER_FORCE_PARALLEL", "false").lower() in {"1", "true", "yes"},
    }


def _unique_list(items: List[str]) -> List[str]:
    seen: set[str] = set()
    result: List[str] = []
    for item in items:
        text = str(item).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _fallback_quadruple(user_query: str, parsed_hint: Dict[str, Any] | None = None) -> QueryQuadruple:
    parsed_hint = parsed_hint or {}
    location_hits: List[str] = []
    location_value = parsed_hint.get("location")
    if isinstance(location_value, str) and location_value.strip():
        location_hits = [location_value.strip()]
    return QueryQuadruple(
        object=[],
        color=[],
        location=_unique_list(location_hits),
        event=str(user_query).strip().rstrip("？?吗呢") or user_query,
        confidence=0.25,
        source="fallback",
    )


def _normalize_quadruple_payload(payload: Dict[str, Any], user_query: str) -> QueryQuadruple:
    objects = payload.get("object", [])
    colors = payload.get("color", [])
    locations = payload.get("location", [])
    if isinstance(objects, str):
        objects = [objects]
    if isinstance(colors, str):
        colors = [colors]
    if isinstance(locations, str):
        locations = [locations]
    confidence_value = payload.get("confidence", 0.0)
    try:
        confidence = float(confidence_value)
    except Exception:
        confidence = 0.0
    event = str(payload.get("event", "")).strip() or str(user_query).strip().rstrip("？?吗呢")
    return QueryQuadruple(
        object=_unique_list([str(item) for item in objects if item is not None]),
        color=_unique_list([str(item) for item in colors if item is not None]),
        location=_unique_list([str(item) for item in locations if item is not None]),
        event=event,
        confidence=max(0.0, min(1.0, confidence)),
        source="llm",
    )


def _extract_quadruple_with_llm(
    llm: Any,
    user_query: str,
    parsed_hint: Dict[str, Any],
    config: RunnableConfig,
) -> QueryQuadruple:
    actual_llm = llm
    if actual_llm is None:
        from langchain_openai import ChatOpenAI

        actual_llm = ChatOpenAI(
            model_name="qwen3-max",
            temperature=0.0,
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            base_url=os.getenv("DASHSCOPE_URL"),
        )
    prompt = build_tool_router_quadruple_prompt(user_query=user_query, parsed_hint=parsed_hint)
    if hasattr(actual_llm, "with_structured_output"):
        structured_llm = actual_llm.with_structured_output(TOOL_ROUTER_QUADRUPLE_OUTPUT_SCHEMA)
        result = structured_llm.invoke(
            [SystemMessage(content="请严格输出结构化四元组JSON。"), HumanMessage(content=prompt)],
            config=config,
        )
        if hasattr(result, "model_dump"):
            payload = result.model_dump()
        elif isinstance(result, dict):
            payload = result
        else:
            payload = dict(result)
        return _normalize_quadruple_payload(payload, user_query)
    raw = actual_llm.invoke([HumanMessage(content=prompt)], config=config)
    text = raw.content if hasattr(raw, "content") else str(raw)
    payload = json.loads(text)
    return _normalize_quadruple_payload(payload, user_query)


def _step_parse_quadruple_factory(llm: Any, run_config: RunnableConfig):
    def _step_parse_quadruple(ctx: CoTContext) -> QueryQuadruple:
        input_data = ctx.original_input if isinstance(ctx.original_input, dict) else {}
        user_query = str(input_data.get("user_query", ""))
        parsed_hint = input_data.get("parsed_question", {})
        try:
            quadruple = _extract_quadruple_with_llm(
                llm=llm,
                user_query=user_query,
                parsed_hint=parsed_hint if isinstance(parsed_hint, dict) else {},
                config=run_config,
            )
            logger.info(
                "[ToolRouter] quadruple解析成功 source=%s confidence=%.2f location=%s",
                quadruple.get("source"),
                quadruple.get("confidence", 0.0),
                quadruple.get("location", []),
            )
            return quadruple
        except Exception as exc:
            logger.warning("[ToolRouter] quadruple解析失败，进入降级: %s", exc)
            return _fallback_quadruple(user_query=user_query, parsed_hint=parsed_hint if isinstance(parsed_hint, dict) else {})

    return _step_parse_quadruple


def _step_route_decision_factory(router_cfg: Dict[str, Any]):
    def _step_route_decision(ctx: CoTContext) -> ToolChoice:
        quadruple: QueryQuadruple = ctx.get_intermediate("query_quadruple") or _fallback_quadruple("")
        has_location = bool(quadruple.get("location"))
        mode = router_cfg["mode_with_location"] if has_location else router_cfg["mode_without_location"]
        if mode not in {"hybrid_search", "pure_sql", "video_vect", "parallel", "hybrid", "sql"}:
            mode = "hybrid_search"
        sql_needed = mode in {"pure_sql", "sql", "parallel"}
        hybrid_needed = mode in {"hybrid_search", "hybrid", "parallel"}
        video_vect_needed = mode in {router_cfg["video_vect_mode"], "video_vect"}
        sub_queries: Dict[str, Any] = {}
        if hybrid_needed:
            sub_queries["hybrid"] = {}
        if sql_needed:
            sub_queries["sql"] = {}
        if video_vect_needed:
            sub_queries["video_vect"] = {}
        return ToolChoice(
            mode="parallel" if router_cfg["force_parallel"] else mode,
            sql_needed=sql_needed,
            hybrid_needed=hybrid_needed,
            video_vect_needed=video_vect_needed,
            sub_queries=sub_queries,
        )

    return _step_route_decision


def create_cot_tool_router_engine(llm: Any = None, run_config: RunnableConfig | None = None) -> CoTEngine:
    cfg = _router_config()
    engine = CoTEngine("ToolRouterV2")
    engine.add_step(SequentialCoTStep("query_quadruple", _step_parse_quadruple_factory(llm, run_config or {}), "四元组解析"))
    engine.add_step(SequentialCoTStep("final_decision", _step_route_decision_factory(cfg), "路由决策"))
    return engine


def create_tool_router_node(llm: Any = None):
    def tool_router_node(state: AgentState, config: RunnableConfig, store: BaseStore) -> dict[str, Any]:
        del store
        is_new = StateResetter.is_new_query(state)
        user_query = InputValidator.extract_latest_query(state)
        reset_updates: Dict[str, Any] = {}
        if is_new:
            reset_updates = StateResetter.reset_ephemeral_state(state, user_query)
        if not user_query:
            user_query = "未知查询"
        cot_engine = create_cot_tool_router_engine(llm=llm, run_config=config)
        ctx = cot_engine.execute({"user_query": user_query, "parsed_question": state.get("parsed_question", {})})
        if ctx.status == StepStatus.FAILED:
            quadruple = _fallback_quadruple(user_query, state.get("parsed_question", {}))
            fallback_mode = _router_config()["mode_without_location"]
            tool_choice = ToolChoice(
                mode=fallback_mode,
                sql_needed=fallback_mode in {"pure_sql", "sql"},
                hybrid_needed=fallback_mode in {"hybrid_search", "hybrid"},
                video_vect_needed=fallback_mode == "video_vect",
                sub_queries={"sql": {}} if fallback_mode in {"pure_sql", "sql"} else {"hybrid": {}},
            )
        else:
            quadruple = ctx.get_intermediate("query_quadruple") or _fallback_quadruple(user_query, state.get("parsed_question", {}))
            tool_choice = ctx.get_intermediate("final_decision") or ToolChoice(
                mode="hybrid_search",
                sql_needed=False,
                hybrid_needed=True,
                video_vect_needed=False,
                sub_queries={"hybrid": {}},
            )
        parsed_hint = state.get("parsed_question", {})
        first_object = quadruple.get("object", [""])[0] if quadruple.get("object") else ""
        first_color = quadruple.get("color", [""])[0] if quadruple.get("color") else ""
        first_location = quadruple.get("location", [""])[0] if quadruple.get("location") else ""
        parsed_question = {
            "event": quadruple.get("event", user_query),
            "color": first_color,
            "location": first_location,
            "object": first_object,
            "time": parsed_hint.get("time") if isinstance(parsed_hint, dict) else None,
            "move": parsed_hint.get("move") if isinstance(parsed_hint, dict) else None,
        }
        meta_list, event_list = question_to_meta_and_event(parsed_question)
        parallel_needed = tool_choice.get("mode") == "parallel"
        routing_metrics = {
            "quadruple_confidence": quadruple.get("confidence", 0.0),
            "location_detected": bool(quadruple.get("location")),
            "route_mode": tool_choice.get("mode", "hybrid_search"),
            "quadruple_source": quadruple.get("source", "unknown"),
        }
        existing_search_config = state.get("search_config", {}) if isinstance(state.get("search_config", {}), dict) else {}
        existing_sql_plan = state.get("sql_plan", {}) if isinstance(state.get("sql_plan", {}), dict) else {}
        search_config = {
            "candidate_limit": existing_search_config.get("candidate_limit", 80),
            "top_k_per_event": existing_search_config.get("top_k_per_event", 20),
            "rerank_top_k": existing_search_config.get("rerank_top_k", 5),
            "distance_threshold": existing_search_config.get("distance_threshold"),
        }
        sql_plan = {
            "table": existing_sql_plan.get("table", "episodic_events"),
            "fields": existing_sql_plan.get(
                "fields",
                ["event_id", "video_id", "camera_id", "track_id", "start_time", "end_time", "object_type", "object_color_cn"],
            ),
            "where": existing_sql_plan.get("where", []),
            "order_by": existing_sql_plan.get("order_by", "start_time ASC"),
            "limit": existing_sql_plan.get("limit", 80),
        }
        thought = (
            f"ToolRouterV2: mode={tool_choice.get('mode')}, "
            f"location={quadruple.get('location', [])}, confidence={quadruple.get('confidence', 0.0):.2f}"
        )
        logger.info("[ToolRouter] %s", thought)
        return {
            **reset_updates,
            "tool_choice": tool_choice,
            "user_query": user_query,
            "parsed_question": parsed_question,
            "meta_list": meta_list,
            "event_list": event_list if event_list else [quadruple.get("event", user_query)],
            "query_quadruple": quadruple,
            "routing_metrics": routing_metrics,
            "search_config": search_config,
            "sql_plan": sql_plan,
            "is_parallel": parallel_needed,
            "parallel_queries": list(tool_choice.get("sub_queries", {}).keys()) if parallel_needed else [],
            "thought": thought,
            "messages": [AIMessage(content=f"工具路由完成(V2): {tool_choice.get('mode', 'hybrid_search')}")],
            "cot_context": ctx.get_full_chain(),
        }

    return tool_router_node


def route_by_tool_choice(state: AgentState) -> str:
    tool_choice = state.get("tool_choice", {})
    mode = tool_choice.get("mode", "none")
    if mode == "parallel":
        return "parallel_search_node"
    if mode in {"hybrid_search", "hybrid"}:
        return "hybrid_search_node"
    if mode in {"pure_sql", "sql"}:
        return "pure_sql_node"
    if mode == "video_vect":
        return "video_vect_node"
    return "hybrid_search_node"


def deprecated_route_from_preprocess(state: AgentState) -> str:
    tool_choice = state.get("tool_choice", {})
    mode = tool_choice.get("mode", "none")
    if mode == "parallel":
        return "parallel_search_node"
    if mode in {"hybrid_search", "hybrid"}:
        return "hybrid_search_node"
    if mode in {"pure_sql", "sql"}:
        return "pure_sql_node"
    if mode == "video_vect":
        return "video_vect_node"
    return "hybrid_search_node"


route_from_preprocess = deprecated_route_from_preprocess
