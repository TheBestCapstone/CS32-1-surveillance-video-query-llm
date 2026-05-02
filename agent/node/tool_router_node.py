import json
import logging
import os
from typing import Any, Dict, List, TypedDict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.store.base import BaseStore

from node.cot_engine import CoTContext, CoTEngine, SequentialCoTStep, StepStatus
from node.router_prompts import (
    TOOL_ROUTER_DECISION_OUTPUT_SCHEMA,
    TOOL_ROUTER_QUADRUPLE_OUTPUT_SCHEMA,
    build_tool_router_decision_prompt,
    build_tool_router_quadruple_prompt,
)
from node.types import AgentState, InputValidator, ToolChoice, question_to_meta_and_event

logger = logging.getLogger(__name__)

TOOL_DESCRIPTIONS = {
    "hybrid_search": {
        "name": "hybrid_search",
        "description": "Location-driven hybrid search combining structured filtering and vector similarity ranking",
        "input": "Quadruple(object, color, location, event) + meta_list + event_list",
        "output": "List of retrieval results containing event_id, video_id, _distance, event_summary_en, etc.",
        "scenarios": "Triggered preferentially when the quadruple's location is not empty",
        "keywords": [],
    },
    "pure_sql": {
        "name": "pure_sql",
        "description": "Structured filtering search when there is no location condition",
        "input": "Quadruple(object, color, event) + meta_list",
        "output": "List of results meeting the conditions",
        "scenarios": "Triggered preferentially when the quadruple's location is empty",
        "keywords": [],
    },
}


class QueryQuadruple(TypedDict):
    """
    Extracted components from the user's query: object, color, location, and event description.
    Note: Time-related queries are intentionally ignored and unsupported.
    """
    object: List[str]
    color: List[str]
    location: List[str]
    event: str
    confidence: float
    source: str


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
    init_prompt_text: str = "",
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
    if init_prompt_text:
        prompt = (
            "Initialization context (from init/agent_init_prompt.md):\n"
            f"{init_prompt_text}\n\n"
            "Now parse the user query into quadruple.\n"
            f"{prompt}"
        )
    if hasattr(actual_llm, "with_structured_output"):
        structured_llm = actual_llm.with_structured_output(TOOL_ROUTER_QUADRUPLE_OUTPUT_SCHEMA)
        result = structured_llm.invoke(
            [SystemMessage(content="Please strictly output the structured quadruple JSON. Note: Time logic is unsupported."), HumanMessage(content=prompt)],
            config=config,
        )
        if hasattr(result, "model_dump"):
            payload = result.model_dump()
        elif isinstance(result, dict):
            payload = result
        else:
            payload = dict(result)
        return _normalize_quadruple_payload(payload, user_query)
    raw = actual_llm.invoke(
        [SystemMessage(content="Please strictly output the structured quadruple JSON. Note: Time logic is unsupported."), HumanMessage(content=prompt)],
        config=config,
    )
    text = raw.content if hasattr(raw, "content") else str(raw)
    text = text.replace("```json", "").replace("```", "").strip()
    payload = json.loads(text)
    return _normalize_quadruple_payload(payload, user_query)


def _step_parse_quadruple_factory(llm: Any, run_config: RunnableConfig, init_prompt_text: str = ""):
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
                init_prompt_text=init_prompt_text,
            )
            logger.info(
                "[ToolRouter] quadruple parsing successful source=%s confidence=%.2f location=%s",
                quadruple.get("source"),
                quadruple.get("confidence", 0.0),
                quadruple.get("location", []),
            )
            return quadruple
        except Exception as exc:
            logger.warning("[ToolRouter] quadruple parsing failed, entering fallback: %s", exc)
            return _fallback_quadruple(user_query=user_query, parsed_hint=parsed_hint if isinstance(parsed_hint, dict) else {})

    return _step_parse_quadruple


def _fallback_tool_choice(mode: str = "hybrid_search", reason_codes: List[str] | None = None) -> ToolChoice:
    normalized_mode = "pure_sql" if mode in {"pure_sql", "sql"} else "hybrid_search"
    sql_needed = normalized_mode == "pure_sql"
    return ToolChoice(
        mode=normalized_mode,
        sql_needed=sql_needed,
        hybrid_needed=not sql_needed,
        sub_queries={"sql": {}} if sql_needed else {"hybrid": {}},
        route_reason_codes=reason_codes or ["FALLBACK_ROUTE"],
        route_confidence=0.3,
    )


def _normalize_route_payload(payload: Dict[str, Any]) -> ToolChoice:
    mode = str(payload.get("mode", "hybrid_search")).strip().lower()
    normalized_mode = "pure_sql" if mode in {"pure_sql", "sql"} else "hybrid_search"
    reason_codes_raw = payload.get("reason_codes", [])
    if not isinstance(reason_codes_raw, list):
        reason_codes_raw = [reason_codes_raw]
    reason_codes = [str(item).strip() for item in reason_codes_raw if str(item).strip()]
    try:
        route_confidence = float(payload.get("confidence", 0.5))
    except Exception:
        route_confidence = 0.5
    route_confidence = max(0.0, min(1.0, route_confidence))
    return _fallback_tool_choice(
        mode=normalized_mode,
        reason_codes=reason_codes or ["LLM_ROUTE"],
    ) | {"route_confidence": route_confidence}


def _decide_route_with_llm(
    llm: Any,
    user_query: str,
    quadruple: QueryQuadruple,
    parsed_hint: Dict[str, Any],
    config: RunnableConfig,
    init_prompt_text: str = "",
) -> ToolChoice:
    actual_llm = llm
    if actual_llm is None:
        from langchain_openai import ChatOpenAI

        actual_llm = ChatOpenAI(
            model_name=os.getenv("DASHSCOPE_CHAT_MODEL", "qwen3-max"),
            temperature=0.0,
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            base_url=os.getenv("DASHSCOPE_URL"),
        )
    prompt = build_tool_router_decision_prompt(user_query=user_query, quadruple=quadruple, parsed_hint=parsed_hint)
    if init_prompt_text:
        prompt = (
            "Initialization context (from init/agent_init_prompt.md):\n"
            f"{init_prompt_text}\n\n"
            "Now decide route mode.\n"
            f"{prompt}"
        )
    if hasattr(actual_llm, "with_structured_output"):
        structured_llm = actual_llm.with_structured_output(TOOL_ROUTER_DECISION_OUTPUT_SCHEMA)
        result = structured_llm.invoke(
            [SystemMessage(content="Please strictly output the route decision JSON."), HumanMessage(content=prompt)],
            config=config,
        )
        if hasattr(result, "model_dump"):
            payload = result.model_dump()
        elif isinstance(result, dict):
            payload = result
        else:
            payload = dict(result)
        return _normalize_route_payload(payload)
    raw = actual_llm.invoke(
        [SystemMessage(content="Please strictly output the route decision JSON."), HumanMessage(content=prompt)],
        config=config,
    )
    text = raw.content if hasattr(raw, "content") else str(raw)
    text = text.replace("```json", "").replace("```", "").strip()
    payload = json.loads(text)
    return _normalize_route_payload(payload)


def _step_route_decision_factory(llm: Any, run_config: RunnableConfig, init_prompt_text: str = ""):
    def _step_route_decision(ctx: CoTContext) -> ToolChoice:
        quadruple: QueryQuadruple = ctx.get_intermediate("query_quadruple") or _fallback_quadruple("")
        input_data = ctx.original_input if isinstance(ctx.original_input, dict) else {}
        user_query = str(input_data.get("user_query", ""))
        parsed_hint = input_data.get("parsed_question", {})
        try:
            return _decide_route_with_llm(
                llm=llm,
                user_query=user_query,
                quadruple=quadruple,
                parsed_hint=parsed_hint if isinstance(parsed_hint, dict) else {},
                config=run_config,
                init_prompt_text=init_prompt_text,
            )
        except Exception as exc:
            logger.warning("[ToolRouter] route decision failed, entering fallback: %s", exc)
            fallback_mode = os.getenv("TOOL_ROUTER_FALLBACK_MODE", "hybrid_search")
            return _fallback_tool_choice(mode=fallback_mode, reason_codes=["ROUTE_LLM_FAILED"])

    return _step_route_decision


def create_cot_tool_router_engine(
    llm: Any = None,
    run_config: RunnableConfig | None = None,
    init_prompt_text: str = "",
) -> CoTEngine:
    engine = CoTEngine("ToolRouterV2")
    engine.add_step(
        SequentialCoTStep(
            "query_quadruple",
            _step_parse_quadruple_factory(llm, run_config or {}, init_prompt_text=init_prompt_text),
            "Quadruple Parsing",
        )
    )
    engine.add_step(
        SequentialCoTStep(
            "final_decision",
            _step_route_decision_factory(llm, run_config or {}, init_prompt_text=init_prompt_text),
            "Route Decision",
        )
    )
    return engine


def create_tool_router_node(llm: Any = None, init_prompt_text: str = ""):
    def tool_router_node(state: AgentState, config: RunnableConfig, store: BaseStore) -> dict[str, Any]:
        del store
        user_query = InputValidator.resolve_active_query(state)
        
        # Check if returning from reflection retry
        reflection_result = state.get("reflection_result", {})
        is_retry_from_reflection = reflection_result.get("needs_retry", False) and state.get("retry_count", 0) > 0

        if not user_query:
            user_query = "Unknown Query"
            
        cot_engine = create_cot_tool_router_engine(llm=llm, run_config=config, init_prompt_text=init_prompt_text)
        
        # If it is a reflection retry, directly use the optimized conditions, skip quadruple extraction
        if is_retry_from_reflection:
            logger.info("[ToolRouter] Detected reflection retry, skipping quadruple extraction and using optimized conditions")
            parsed_hint = state.get("parsed_question", {})
            quadruple = QueryQuadruple(
                object=[parsed_hint.get("object")] if parsed_hint.get("object") else [],
                color=[parsed_hint.get("color")] if parsed_hint.get("color") else [],
                location=[parsed_hint.get("location")] if parsed_hint.get("location") else [],
                event=parsed_hint.get("event", user_query),
                confidence=0.9,
                source="reflection_optimized"
            )
            # Inject into ctx manually
            ctx = CoTContext(original_input={"user_query": user_query, "parsed_question": parsed_hint})
            if hasattr(ctx, "set_intermediate"):
                ctx.set_intermediate("query_quadruple", quadruple)
            else:
                ctx._intermediates["query_quadruple"] = quadruple
                
            # Execute routing decision only
            decision_step = _step_route_decision_factory(llm, config, init_prompt_text=init_prompt_text)
            tool_choice = decision_step(ctx)
            
            if hasattr(ctx, "set_intermediate"):
                ctx.set_intermediate("final_decision", tool_choice)
            else:
                ctx.intermediates["final_decision"] = tool_choice
                
            ctx.status = getattr(StepStatus, "SUCCESS", "success")
        else:
            ctx = cot_engine.execute({"user_query": user_query, "parsed_question": state.get("parsed_question", {})})
            if ctx.status == StepStatus.FAILED:
                quadruple = _fallback_quadruple(user_query, state.get("parsed_question", {}))
                fallback_mode = os.getenv("TOOL_ROUTER_FALLBACK_MODE", "hybrid_search")
                tool_choice = _fallback_tool_choice(mode=fallback_mode, reason_codes=["ROUTER_COT_FAILED"])
            else:
                quadruple = ctx.get_intermediate("query_quadruple") or _fallback_quadruple(user_query, state.get("parsed_question", {}))
                tool_choice = ctx.get_intermediate("final_decision") or _fallback_tool_choice(mode="hybrid_search")
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
        routing_metrics = {
            "quadruple_confidence": quadruple.get("confidence", 0.0),
            "location_detected": bool(quadruple.get("location")),
            "route_mode": tool_choice.get("mode", "hybrid_search"),
            "quadruple_source": quadruple.get("source", "unknown"),
            "route_reason_codes": tool_choice.get("route_reason_codes", []),
            "route_confidence": tool_choice.get("route_confidence", 0.0),
        }
        existing_search_config = state.get("search_config", {}) if isinstance(state.get("search_config", {}), dict) else {}
        existing_sql_plan = state.get("sql_plan", {}) if isinstance(state.get("sql_plan", {}), dict) else {}
        search_config = {
            "candidate_limit": existing_search_config.get("candidate_limit", 80),
            "top_k_per_event": existing_search_config.get("top_k_per_event", 20),
            "rerank_top_k": existing_search_config.get("rerank_top_k", 5),
            "rerank_candidate_limit": existing_search_config.get("rerank_candidate_limit", 20),
            "distance_threshold": existing_search_config.get("distance_threshold"),
        }
        sql_plan = {
            "table": existing_sql_plan.get("table", "episodic_events"),
            "fields": existing_sql_plan.get(
                "fields",
                ["event_id", "video_id", "camera_id", "track_id", "object_type", "object_color_en", "scene_zone_en", "appearance_notes_en", "event_summary_en"],
            ),
            "where": existing_sql_plan.get("where", []),
            "order_by": existing_sql_plan.get("order_by", "event_id ASC"),
            "limit": existing_sql_plan.get("limit", 80),
        }
        thought = (
            f"ToolRouterV2: mode={tool_choice.get('mode')}, "
            f"location={quadruple.get('location', [])}, confidence={quadruple.get('confidence', 0.0):.2f}"
        )
        logger.info("[ToolRouter] %s", thought)
        return {
            "tool_choice": tool_choice,
            "parsed_question": parsed_question,
            "meta_list": meta_list,
            "event_list": event_list if event_list else [quadruple.get("event", user_query)],
            "query_quadruple": quadruple,
            "routing_metrics": routing_metrics,
            "search_config": search_config,
            "sql_plan": sql_plan,
            "thought": thought,
            "messages": [AIMessage(content=f"Tool routing complete (V2): {tool_choice.get('mode', 'hybrid_search')}")],
            "cot_context": ctx.get_full_chain(),
        }

    return tool_router_node


_LEGACY_DISABLE_PURE_SQL_FLAG = "AGENT_LEGACY_DISABLE_PURE_SQL_TERMINAL"


def _legacy_disable_pure_sql_terminal() -> bool:
    # P1-6: opt-in switch that redirects the legacy router's `pure_sql` terminal
    # branch to `hybrid_search_node`. Default path (`parallel_fusion`) already
    # treats SQL as a fusion channel; this flag lets legacy setups converge
    # without touching the terminal graph topology.
    raw = os.getenv(_LEGACY_DISABLE_PURE_SQL_FLAG, "").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def route_by_tool_choice(state: AgentState) -> str:
    tool_choice = state.get("tool_choice", {})
    mode = tool_choice.get("mode", "none")
    if mode in {"hybrid_search", "hybrid"}:
        return "hybrid_search_node"
    if mode in {"pure_sql", "sql"}:
        if _legacy_disable_pure_sql_terminal():
            return "hybrid_search_node"
        return "pure_sql_node"
    return "hybrid_search_node"


def deprecated_route_from_preprocess(state: AgentState) -> str:
    return route_by_tool_choice(state)


route_from_preprocess = deprecated_route_from_preprocess
