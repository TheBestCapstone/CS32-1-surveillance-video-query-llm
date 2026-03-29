import json
import logging
import os
from typing import Any, Dict, List, Optional, TypedDict

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.store.base import BaseStore

from node.cot_engine import (
    CoTContext,
    CoTEngine,
    CoTStep,
    ConditionalStep,
    ParallelBranch,
    ParallelExecutionStep,
    SequentialCoTStep,
    StepResult,
    StepStatus,
    create_cot_engine,
    log_context,
)
from node.types import AgentState, ToolChoice, InputValidator, StateResetter

logger = logging.getLogger(__name__)


TOOL_DESCRIPTIONS = {
    "hybrid_search": {
        "name": "hybrid_search",
        "description": "结合向量检索和SQL元数据过滤的混合搜索",
        "input": "event_list(事件关键词列表), meta_list(元数据过滤条件)",
        "output": "检索结果列表，包含event_id, video_id, _distance, event_summary等字段",
        "scenarios": "用户查询包含进入、离开、移动、停止、出现等事件描述，同时可能有颜色、时间等条件",
        "keywords": ["车", "人", "目标", "物体", "进入", "离开", "移动", "停止", "出现"],
    },
    "pure_sql": {
        "name": "pure_sql",
        "description": "基于元数据条件的纯SQL结构化查询",
        "input": "meta_list(元数据过滤条件，如颜色、时间范围、运动状态等)",
        "output": "符合条件的结果列表",
        "scenarios": "用户查询主要是结构化的条件筛选，如红色车辆、上午9点到10点、静止的目标",
        "keywords": ["红色", "蓝色", "白色", "黑色", "上午", "下午", "今天", "静止"],
    },
    "video_vect": {
        "name": "video_vect",
        "description": "基于语义理解的视频内容向量检索",
        "input": "event_list(事件关键词)",
        "output": "语义相关的视频片段列表",
        "scenarios": "用户查询需要理解视频内容的语义，如车辆驶入、行人横穿、物体遗落",
        "keywords": ["视频", "画面", "镜头", "语义", "理解"],
    },
    "parallel_search": {
        "name": "parallel_search",
        "description": "同时执行多个检索工具并合并结果",
        "input": "多个子查询任务",
        "output": "合并后的去重排序结果",
        "scenarios": "复杂查询需要多种检索方式协同，如既需要向量检索又需要SQL过滤",
        "keywords": [],
    },
}


class ToolCandidate(TypedDict):
    tool_name: str
    score: float
    matched_keywords: List[str]
    confidence: float
    reasoning: str


class ToolRanking(TypedDict):
    ranked_tools: List[ToolCandidate]
    top_choice: str
    fallback_choice: str
    needs_parallel: bool
    parallel_modes: List[str]


class IntentUnderstanding(TypedDict):
    query_type: str
    intent_summary: str
    extracted_entities: Dict[str, List[str]]
    confidence: float


def _step_intent_understanding(ctx: CoTContext) -> IntentUnderstanding:
    user_query = ctx.original_input if isinstance(ctx.original_input, str) else ctx.original_input.get("user_query", "")
    query_lower = user_query.lower()

    entity_map: Dict[str, List[str]] = {
        "color": [],
        "time": [],
        "motion": [],
        "object": [],
        "event": [],
    }

    color_kws = ["红", "蓝", "白", "黑", "银", "灰", "黄", "绿", "橙", "紫", "粉"]
    for kw in color_kws:
        if kw in query_lower:
            entity_map["color"].append(kw)

    time_kws = ["今天", "昨天", "上午", "下午", "时间", "点", "时", "日"]
    for kw in time_kws:
        if kw in query_lower:
            entity_map["time"].append(kw)

    motion_kws = ["静止", "运动", "移动", "停止"]
    for kw in motion_kws:
        if kw in query_lower:
            entity_map["motion"].append(kw)

    event_kws = ["进入", "离开", "出现", "消失", "驶入", "横穿", "停止"]
    for kw in event_kws:
        if kw in query_lower:
            entity_map["event"].append(kw)

    obj_kws = ["车", "人", "行人", "车辆", "自行车", "摩托车"]
    for kw in obj_kws:
        if kw in query_lower:
            entity_map["object"].append(kw)

    query_type = "semantic"
    if entity_map["color"] or entity_map["time"] or entity_map["motion"]:
        query_type = "structured"
    if entity_map["event"] and (entity_map["color"] or entity_map["time"]):
        query_type = "hybrid"

    return IntentUnderstanding(
        query_type=query_type,
        intent_summary=f"用户查询类型={query_type}, 提取到颜色={len(entity_map['color'])}, 时间={len(entity_map['time'])}, 事件={len(entity_map['event'])}",
        extracted_entities=entity_map,
        confidence=0.85,
    )


def _step_candidate_recall(ctx: CoTContext) -> List[Dict[str, Any]]:
    intent: IntentUnderstanding = ctx.get_intermediate("intent_understanding")
    if not intent:
        intent = _step_intent_understanding(ctx)

    query_type = intent["query_type"]
    entities = intent["extracted_entities"]

    candidates: List[Dict[str, Any]] = []

    if query_type in ("semantic", "hybrid"):
        candidates.append({
            "tool_name": "hybrid_search",
            "matched_keywords": entities.get("event", []) + entities.get("object", []),
            "reasoning": f"查询类型={query_type}，包含事件/语义描述，适用混合搜索",
        })

    if query_type in ("structured", "hybrid"):
        candidates.append({
            "tool_name": "pure_sql",
            "matched_keywords": entities.get("color", []) + entities.get("time", []) + entities.get("motion", []),
            "reasoning": f"查询类型={query_type}，包含结构化条件，适用SQL过滤",
        })

    if query_type == "semantic" and not candidates:
        candidates.append({
            "tool_name": "video_vect",
            "matched_keywords": [],
            "reasoning": "纯语义查询，使用视频向量检索",
        })

    if not candidates:
        candidates.append({
            "tool_name": "hybrid_search",
            "matched_keywords": [],
            "reasoning": "默认使用混合搜索",
        })

    return candidates


def _step_capability_matching(ctx: CoTContext) -> List[ToolCandidate]:
    candidates: List[Dict[str, Any]] = ctx.get_intermediate("candidate_recall")
    if not candidates:
        candidates = _step_candidate_recall(ctx)

    matched: List[ToolCandidate] = []
    for candidate in candidates:
        tool_name = candidate["tool_name"]
        tool_desc = TOOL_DESCRIPTIONS.get(tool_name, {})
        keywords = tool_desc.get("keywords", [])
        matched_kws = candidate.get("matched_keywords", [])

        keyword_score = len(matched_kws) / max(len(keywords), 1) if keywords else 0.0
        base_score = 0.5

        score = min(base_score + keyword_score * 0.5, 1.0)
        confidence = score

        matched.append(ToolCandidate(
            tool_name=tool_name,
            score=score,
            matched_keywords=matched_kws,
            confidence=confidence,
            reasoning=candidate.get("reasoning", ""),
        ))

    return matched


def _step_confidence_evaluation(ctx: CoTContext) -> Dict[str, Any]:
    candidates: List[ToolCandidate] = ctx.get_intermediate("capability_matching")
    if not candidates:
        candidates = _step_capability_matching(ctx)

    sorted_candidates = sorted(candidates, key=lambda x: x["score"], reverse=True)

    needs_parallel = len(sorted_candidates) > 1 and sorted_candidates[0]["score"] < 0.8

    parallel_modes = []
    if needs_parallel:
        for c in sorted_candidates[1:3]:
            if c["score"] > 0.3:
                parallel_modes.append(c["tool_name"])

    return {
        "ranked_tools": sorted_candidates,
        "top_choice": sorted_candidates[0]["tool_name"] if sorted_candidates else "hybrid_search",
        "fallback_choice": "hybrid_search",
        "needs_parallel": needs_parallel,
        "parallel_modes": parallel_modes,
        "top_confidence": sorted_candidates[0]["confidence"] if sorted_candidates else 0.0,
    }


def _step_final_decision(ctx: CoTContext) -> ToolChoice:
    ranking: Dict[str, Any] = ctx.get_intermediate("confidence_evaluation")
    if not ranking:
        ranking = _step_confidence_evaluation(ctx)

    top_choice = ranking.get("top_choice", "hybrid_search")
    needs_parallel = ranking.get("needs_parallel", False)
    parallel_modes = ranking.get("parallel_modes", [])

    sql_needed = top_choice == "pure_sql" or "pure_sql" in parallel_modes
    hybrid_needed = top_choice == "hybrid_search" or "hybrid_search" in parallel_modes
    video_vect_needed = top_choice == "video_vect" or "video_vect" in parallel_modes

    sub_queries: Dict[str, Any] = {}
    if hybrid_needed:
        sub_queries["hybrid"] = {}
    if sql_needed:
        sub_queries["sql"] = {}
    if video_vect_needed:
        sub_queries["video_vect"] = {}

    mode = "parallel" if needs_parallel else top_choice

    return ToolChoice(
        mode=mode,
        sql_needed=sql_needed,
        hybrid_needed=hybrid_needed,
        video_vect_needed=video_vect_needed,
        sub_queries=sub_queries,
    )


def _create_llm_based_decision_step(llm: Any) -> CoTStep:
    def llm_decision(ctx: CoTContext) -> Dict[str, Any]:
        user_query = ctx.original_input if isinstance(ctx.original_input, str) else ctx.original_input.get("user_query", "")

        prompt = f"""你是一个智能工具路由助手。根据用户查询判断需要使用的工具类型。

可用工具：hybrid_search, pure_sql, video_vect, parallel_search

用户查询：{user_query}

请输出JSON格式的决策：
{{"mode": "工具名", "reason": "理由", "confidence": 0.0-1.0}}"""

        try:
            response = llm.invoke([HumanMessage(content=prompt)])
            raw_content = response.content if hasattr(response, "content") else str(response)

            try:
                decision = json.loads(raw_content)
                return {
                    "llm_decision": decision,
                    "raw_response": raw_content,
                    "success": True,
                }
            except json.JSONDecodeError:
                return {
                    "llm_decision": {"mode": "hybrid_search", "reason": "JSON解析失败", "confidence": 0.3},
                    "raw_response": raw_content,
                    "success": False,
                }
        except Exception as e:
            logger.warning(f"[ToolRouter CoT] LLM决策失败: {e}")
            return {
                "llm_decision": {"mode": "hybrid_search", "reason": str(e), "confidence": 0.0},
                "raw_response": None,
                "success": False,
                "error": str(e),
            }

    return SequentialCoTStep("llm_decision", llm_decision, "LLM辅助决策")


def create_cot_tool_router_engine(llm: Any = None) -> CoTEngine:
    engine = CoTEngine("ToolRouter")

    intent_step = SequentialCoTStep("intent_understanding", _step_intent_understanding, "意图理解")
    recall_step = SequentialCoTStep("candidate_recall", _step_candidate_recall, "候选召回")
    match_step = SequentialCoTStep("capability_matching", _step_capability_matching, "能力匹配")
    eval_step = SequentialCoTStep("confidence_evaluation", _step_confidence_evaluation, "置信度评估")
    decision_step = SequentialCoTStep("final_decision", _step_final_decision, "最终决策")

    engine.add_step(intent_step)
    engine.add_step(recall_step)
    engine.add_step(match_step)
    engine.add_step(eval_step)
    engine.add_step(decision_step)

    if llm is not None:
        llm_step = _create_llm_based_decision_step(llm)
        engine.add_step(llm_step)

    return engine


def create_tool_router_node(llm: Any = None):
    cot_engine = create_cot_tool_router_engine(llm)

    def tool_router_node(state: AgentState, config: RunnableConfig, store: BaseStore) -> dict[str, Any]:
        del store

        # 检测并重置状态 (如果是新查询)
        is_new = StateResetter.is_new_query(state)
        user_query = InputValidator.extract_latest_query(state)
        
        reset_updates = {}
        if is_new:
            logger.info(f"[ToolRouter CoT] 检测到新查询，重置历史临时状态。新查询: {user_query[:30]}")
            reset_updates = StateResetter.reset_ephemeral_state(state, user_query)
        
        if not user_query:
            logger.warning("[ToolRouter CoT] 获取到的查询为空，使用防御性回退。")
            user_query = "未知查询"

        logger.info(f"[ToolRouter CoT] 开始推理, query={user_query[:50]}")

        try:
            ctx = cot_engine.execute({"user_query": user_query})

            if ctx.status == StepStatus.FAILED:
                logger.warning(f"[ToolRouter CoT] 推理失败，使用默认路由: {ctx.metadata.get('error')}")
                final_choice = _fallback_routing(user_query)
            else:
                final_choice = ctx.get_intermediate("final_decision")
                if not final_choice:
                    final_choice = _fallback_routing(user_query)

            mode = final_choice.get("mode", "hybrid") if isinstance(final_choice, dict) else final_choice.get("mode", "hybrid")
            if isinstance(final_choice, dict) and "mode" not in final_choice:
                mode = "hybrid"

        except Exception as exc:
            logger.error(f"[ToolRouter CoT] 异常: {exc}", exc_info=True)
            mode = "hybrid"
            final_choice = _fallback_routing(user_query)

        if not mode or mode == "none":
            mode = "hybrid"

        sql_needed = mode in ("pure_sql", "parallel")
        hybrid_needed = mode in ("hybrid_search", "hybrid", "parallel")
        video_vect_needed = mode == "video_vect"

        sub_queries: dict[str, Any] = {}
        if hybrid_needed:
            sub_queries["hybrid"] = {}
        if sql_needed:
            sub_queries["sql"] = {}
        if video_vect_needed:
            sub_queries["video_vect"] = {}

        parallel_needed = mode == "parallel"

        tool_choice: ToolChoice = {
            "mode": mode if mode != "hybrid" else "hybrid_search",
            "sql_needed": sql_needed,
            "hybrid_needed": hybrid_needed,
            "video_vect_needed": video_vect_needed,
            "sub_queries": sub_queries,
        }

        thought = f"工具路由决策(CoT): mode={tool_choice['mode']}, sql={sql_needed}, hybrid={hybrid_needed}, video={video_vect_needed}"
        if ctx.metadata.get("chain"):
            thought += f", 推理链={ctx.metadata['chain']}"

        logger.info(f"[ToolRouter CoT] 决策完成: {thought}")

        return {
            **reset_updates,
            "tool_choice": tool_choice,
            "user_query": user_query,
            "is_parallel": parallel_needed,
            "parallel_queries": list(sub_queries.keys()) if parallel_needed else [],
            "thought": thought,
            "messages": [AIMessage(content=f"工具路由完成(CoT): {tool_choice['mode']}")],
            "cot_context": ctx.get_full_chain() if "ctx" in dir() else [],
        }

    return tool_router_node


def _fallback_routing(user_query: str) -> Dict[str, Any]:
    query_lower = user_query.lower()

    if any(kw in query_lower for kw in ["车", "人", "进入", "离开", "移动"]):
        return {"mode": "hybrid_search", "reason": "fallback: 包含事件关键词", "confidence": 0.5}
    elif any(kw in query_lower for kw in ["红色", "蓝色", "白色", "黑色", "上午", "今天"]):
        return {"mode": "pure_sql", "reason": "fallback: 包含结构化条件", "confidence": 0.5}
    elif any(kw in query_lower for kw in ["视频", "画面"]):
        return {"mode": "video_vect", "reason": "fallback: 包含视频语义关键词", "confidence": 0.5}
    else:
        return {"mode": "hybrid_search", "reason": "fallback: 默认混合搜索", "confidence": 0.5}


def route_by_tool_choice(state: AgentState) -> str:
    tool_choice = state.get("tool_choice", {})
    mode = tool_choice.get("mode", "none")

    if mode == "hybrid_search":
        return "hybrid_preprocess"
    elif mode == "parallel":
        return "hybrid_preprocess"
    elif mode in ("pure_sql", "sql"):
        return "pure_sql_preprocess"
    elif mode == "video_vect":
        return "video_vect_preprocess"
    else:
        return "hybrid_preprocess"


def route_from_preprocess(state: AgentState) -> str:
    tool_choice = state.get("tool_choice", {})
    mode = tool_choice.get("mode", "none")

    if mode == "parallel":
        return "hybrid_search_node"
    elif mode == "hybrid_search":
        return "hybrid_search_node"
    elif mode in ("pure_sql", "sql"):
        return "pure_sql_node"
    elif mode == "video_vect":
        return "video_vect_node"
    else:
        return "hybrid_search_node"


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')

    print("\n=== Test: CoT Tool Router ===")
    router = create_tool_router_node()
    out = router({"user_query": "车进入镜头", "parsed_question": {}}, {}, None)
    print(f"mode: {out['tool_choice']['mode']}")
    print(f"thought: {out['thought']}")
    assert out["tool_choice"]["mode"] == "hybrid_search"

    print("\n=== Test: CoT Tool Router with color/time ===")
    out2 = router({"user_query": "红色车辆今天上午进入镜头", "parsed_question": {}}, {}, None)
    print(f"mode: {out2['tool_choice']['mode']}")
    print(f"is_parallel: {out2['is_parallel']}")
