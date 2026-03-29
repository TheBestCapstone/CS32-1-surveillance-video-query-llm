import json
import logging
import time
from typing import Any, Callable, Dict, List, Optional, TypedDict

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.store.base import BaseStore

from node.cot_engine import (
    CoTContext,
    CoTEngine,
    CoTCondition,
    CoTStep,
    SequentialCoTStep,
    StepResult,
    StepStatus,
)
from node.types import AgentState

logger = logging.getLogger(__name__)

DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 1.0


class ReflectionCallback:
    def __init__(
        self,
        on_retry: Optional[Callable[[Dict[str, Any], int], None]] = None,
        on_max_retries: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_error: Optional[Callable[[Exception, Dict[str, Any]], None]] = None,
        on_success: Optional[Callable[[Dict[str, Any]], None]] = None,
    ):
        self.on_retry = on_retry
        self.on_max_retries = on_max_retries
        self.on_error = on_error
        self.on_success = on_success

    def handle_retry(self, state: Dict[str, Any], retry_count: int) -> None:
        if self.on_retry:
            self.on_retry(state, retry_count)

    def handle_max_retries(self, state: Dict[str, Any]) -> None:
        if self.on_max_retries:
            self.on_max_retries(state)

    def handle_error(self, exc: Exception, state: Dict[str, Any]) -> None:
        if self.on_error:
            self.on_error(exc, state)

    def handle_success(self, state: Dict[str, Any]) -> None:
        if self.on_success:
            self.on_success(state)


class QualityScore(TypedDict):
    completeness: float
    clarity: float
    overall: float
    issues: List[str]


class ErrorType(TypedDict):
    category: str
    sub_category: str
    description: str
    severity: str


class RootCauseAnalysis(TypedDict):
    root_cause: str
    affected_fields: List[str]
    severity: str
    recommendation: str


class OptimizationStrategy(TypedDict):
    strategy_name: str
    changes: Dict[str, Any]
    expected_improvement: str
    risk_level: str


class StrategyValidation(TypedDict):
    is_valid: bool
    validated_changes: Dict[str, Any]
    warnings: List[str]


def _step_result_review(ctx: CoTContext) -> Dict[str, Any]:
    state = ctx.original_input if isinstance(ctx.original_input, dict) else {}
    user_query = state.get("user_query", "")
    parsed_question = state.get("parsed_question", {})

    search_result = (
        state.get("hybrid_result")
        or state.get("sql_result")
        or state.get("video_vect_result")
        or state.get("merged_result")
        or []
    )

    return {
        "user_query": user_query,
        "parsed_question": parsed_question,
        "search_result": search_result,
        "result_count": len(search_result),
        "has_results": len(search_result) > 0,
    }


def _step_error_location(ctx: CoTContext) -> List[ErrorType]:
    review: Dict[str, Any] = ctx.get_intermediate("result_review")
    if not review:
        review = _step_result_review(ctx)

    errors: List[ErrorType] = []
    parsed_question = review.get("parsed_question", {})
    result_count = review.get("result_count", 0)

    if result_count == 0:
        errors.append(ErrorType(
            category="empty_result",
            sub_category="no_data",
            description="检索结果为空",
            severity="high",
        ))

    if not parsed_question.get("event") or (isinstance(parsed_question.get("event"), str) and parsed_question.get("event", "").lower() in ("null", "none", "")):
        errors.append(ErrorType(
            category="missing_event",
            sub_category="field_missing",
            description="缺少事件类型描述",
            severity="high",
        ))

    if result_count > 0 and result_count < 3:
        errors.append(ErrorType(
            category="too_few_results",
            sub_category="insufficient",
            description=f"检索结果过少({result_count}条)，可能查询条件过于严格",
            severity="medium",
        ))

    if result_count > 100:
        errors.append(ErrorType(
            category="too_many_results",
            sub_category="excessive",
            description=f"检索结果过多({result_count}条)，可能查询条件过于宽松",
            severity="medium",
        ))

    return errors


def _step_root_cause_analysis(ctx: CoTContext) -> List[RootCauseAnalysis]:
    errors: List[ErrorType] = ctx.get_intermediate("error_location")
    if not errors:
        errors = _step_error_location(ctx)

    root_causes: List[RootCauseAnalysis] = []

    for error in errors:
        category = error.get("category", "")
        severity = error.get("severity", "medium")

        if category == "empty_result":
            root_causes.append(RootCauseAnalysis(
                root_cause="查询条件无法匹配任何结果",
                affected_fields=["event", "meta_list"],
                severity=severity,
                recommendation="放宽查询条件或补充更多关键词",
            ))
        elif category == "missing_event":
            root_causes.append(RootCauseAnalysis(
                root_cause="缺少核心事件描述，检索无明确目标",
                affected_fields=["event"],
                severity=severity,
                recommendation="补充事件类型，如进入、离开、出现等",
            ))
        elif category == "too_few_results":
            root_causes.append(RootCauseAnalysis(
                root_cause="查询条件过于严格",
                affected_fields=["meta_list"],
                severity=severity,
                recommendation="放宽时间、颜色等过滤条件",
            ))
        elif category == "too_many_results":
            root_causes.append(RootCauseAnalysis(
                root_cause="查询条件过于宽松",
                affected_fields=["meta_list"],
                severity=severity,
                recommendation="添加更精确的过滤条件",
            ))

    if not root_causes:
        root_causes.append(RootCauseAnalysis(
            root_cause="无明显问题",
            affected_fields=[],
            severity="low",
            recommendation="保持当前查询",
        ))

    return root_causes


def _step_quality_scoring(ctx: CoTContext) -> QualityScore:
    review: Dict[str, Any] = ctx.get_intermediate("result_review")
    if not review:
        review = _step_result_review(ctx)

    errors: List[ErrorType] = ctx.get_intermediate("error_location")
    if not errors:
        errors = _step_error_location(ctx)

    issues: List[str] = [e.get("description", "") for e in errors]

    completeness = 1.0
    clarity = 1.0

    if not review.get("user_query") or not review.get("user_query", "").strip():
        issues.append("用户查询为空")
        completeness = 0.0
        clarity = 0.0

    if not review.get("parsed_question", {}).get("event"):
        completeness -= 0.3

    result_count = review.get("result_count", 0)
    if result_count == 0:
        issues.append("检索结果为空")
        completeness = 0.3
    elif result_count < 3:
        completeness = 0.5
    elif result_count > 100:
        completeness = 0.7

    if completeness < 0.5:
        issues.append("查询完整性不足，需要优化")

    overall = (completeness + clarity) / 2.0

    return QualityScore(
        completeness=round(completeness, 3),
        clarity=round(clarity, 3),
        overall=round(overall, 3),
        issues=issues,
    )


def _step_strategy_generation(ctx: CoTContext) -> List[OptimizationStrategy]:
    errors: List[ErrorType] = ctx.get_intermediate("error_location")
    if not errors:
        errors = _step_error_location(ctx)

    root_causes: List[RootCauseAnalysis] = ctx.get_intermediate("root_cause_analysis")
    if not root_causes:
        root_causes = _step_root_cause_analysis(ctx)

    strategies: List[OptimizationStrategy] = []

    for error in errors:
        category = error.get("category", "")

        if category == "missing_event":
            strategies.append(OptimizationStrategy(
                strategy_name="supplement_event",
                changes={"event": "出现"},
                expected_improvement="补充事件描述后能更准确检索",
                risk_level="low",
            ))
        elif category == "too_few_results":
            strategies.append(OptimizationStrategy(
                strategy_name="relax_conditions",
                changes={"remove_time_filter": True},
                expected_improvement="放宽条件后结果数量增加",
                risk_level="medium",
            ))
        elif category == "too_many_results":
            strategies.append(OptimizationStrategy(
                strategy_name="tighten_conditions",
                changes={"add_color_filter": True},
                expected_improvement="精确条件后结果更相关",
                risk_level="medium",
            ))
        elif category == "empty_result":
            strategies.append(OptimizationStrategy(
                strategy_name="generalize_query",
                changes={"event": "出现", "remove_strict_filters": True},
                expected_improvement="泛化查询以获得结果",
                risk_level="high",
            ))

    if not strategies:
        strategies.append(OptimizationStrategy(
            strategy_name="no_change",
            changes={},
            expected_improvement="无需优化",
            risk_level="none",
        ))

    return strategies


def _step_strategy_validation(ctx: CoTContext) -> StrategyValidation:
    strategies: List[OptimizationStrategy] = ctx.get_intermediate("strategy_generation")
    if not strategies:
        strategies = _step_strategy_generation(ctx)

    warnings: List[str] = []
    validated_changes: Dict[str, Any] = {}

    for strategy in strategies:
        if strategy.get("risk_level") == "high":
            warnings.append(f"策略 {strategy['strategy_name']} 风险较高")
        validated_changes.update(strategy.get("changes", {}))

    return StrategyValidation(
        is_valid=len(warnings) == 0 or any(s.get("risk_level") != "high" for s in strategies),
        validated_changes=validated_changes,
        warnings=warnings,
    )


def _step_quality_evaluation(ctx: CoTContext) -> bool:
    score: QualityScore = ctx.get_intermediate("quality_scoring")
    if not score:
        score = _step_quality_scoring(ctx)

    needs_optimization = score.get("overall", 0.0) < 0.6 or len(score.get("issues", [])) > 0
    return needs_optimization


def _step_final_decision(ctx: CoTContext) -> Dict[str, Any]:
    needs_optimization: bool = ctx.get_intermediate("quality_evaluation")
    if not isinstance(needs_optimization, bool):
        needs_optimization = _step_quality_evaluation(ctx)

    errors: List[ErrorType] = ctx.get_intermediate("error_location")
    score: QualityScore = ctx.get_intermediate("quality_scoring")
    strategies: List[OptimizationStrategy] = ctx.get_intermediate("strategy_generation")

    current_retry = ctx.original_input.get("retry_count", 0) if isinstance(ctx.original_input, dict) else 0
    max_retries = ctx.metadata.get("max_retries", DEFAULT_MAX_RETRIES)

    if current_retry >= max_retries:
        return {
            "decision": "max_retries_reached",
            "feedback": f"已达到最大优化次数({max_retries})，停止迭代",
            "needs_retry": False,
            "can_continue": False,
            "quality_score": score.get("overall", 0.0) if score else 0.0,
            "errors": errors or [],
            "strategies": strategies or [],
        }

    if not needs_optimization:
        return {
            "decision": "satisfactory",
            "feedback": "查询质量满意",
            "needs_retry": False,
            "can_continue": False,
            "quality_score": score.get("overall", 0.0) if score else 0.0,
            "errors": errors or [],
            "strategies": [],
        }

    validated: StrategyValidation = ctx.get_intermediate("strategy_validation")
    optimized_query = ctx.original_input.get("user_query", "") if isinstance(ctx.original_input, dict) else ""
    optimized_parsed = dict(ctx.original_input.get("parsed_question", {}) if isinstance(ctx.original_input, dict) else {})

    if validated and validated.get("is_valid"):
        changes = validated.get("validated_changes", {})
        if "event" in changes:
            optimized_parsed["event"] = changes["event"]
            optimized_query = f"{optimized_query} {changes['event']}"
        if changes.get("remove_time_filter"):
            optimized_parsed.pop("time", None)
            optimized_query += "（已放宽时间条件）"
        if changes.get("add_color_filter"):
            optimized_query += "（需更精确条件）"

    return {
        "decision": "retry",
        "feedback": f"发现问题({len(errors)}项)，正在优化查询",
        "needs_retry": True,
        "can_continue": True,
        "quality_score": score.get("overall", 0.0) if score else 0.0,
        "errors": errors or [],
        "strategies": strategies or [],
        "optimized_query": optimized_query,
        "optimized_parsed": optimized_parsed,
    }


def create_cot_reflection_engine(max_retries: int = DEFAULT_MAX_RETRIES, callback: Optional[ReflectionCallback] = None) -> CoTEngine:
    engine = CoTEngine("Reflection")
    engine.metadata["max_retries"] = max_retries

    review_step = SequentialCoTStep("result_review", _step_result_review, "结果复盘")
    location_step = SequentialCoTStep("error_location", _step_error_location, "错误定位")
    root_cause_step = SequentialCoTStep("root_cause_analysis", _step_root_cause_analysis, "根因分析")
    scoring_step = SequentialCoTStep("quality_scoring", _step_quality_scoring, "质量评分")
    strategy_step = SequentialCoTStep("strategy_generation", _step_strategy_generation, "策略生成")
    validation_step = SequentialCoTStep("strategy_validation", _step_strategy_validation, "策略验证")
    eval_step = SequentialCoTStep("quality_evaluation", _step_quality_evaluation, "质量评估")
    decision_step = SequentialCoTStep("final_decision", _step_final_decision, "最终决策")

    engine.add_step(review_step)
    engine.add_step(location_step)
    engine.add_step(root_cause_step)
    engine.add_step(scoring_step)
    engine.add_step(strategy_step)
    engine.add_step(validation_step)
    engine.add_step(eval_step)
    engine.add_step(decision_step)

    return engine


def create_reflection_node(
    llm: Any = None,
    max_retries: int = DEFAULT_MAX_RETRIES,
    retry_delay: float = DEFAULT_RETRY_DELAY,
    callback: Optional[ReflectionCallback] = None,
):
    cot_engine = create_cot_reflection_engine(max_retries, callback)
    actual_callback = callback or ReflectionCallback()

    def reflection_node(state: AgentState, config: RunnableConfig, store: BaseStore) -> dict[str, Any]:
        del config, store

        current_retry = int(state.get("retry_count", 0) or 0)
        logger.info(f"[Reflection CoT] 第{current_retry + 1}次反思开始, 当前重试次数={current_retry}/{max_retries}")

        try:
            if current_retry >= max_retries:
                return _handle_max_retries(state, current_retry, max_retries, actual_callback)

            ctx = cot_engine.execute(state, max_duration_ms=10000.0)

            if ctx.status == StepStatus.FAILED:
                logger.warning(f"[Reflection CoT] 推理失败: {ctx.metadata.get('error')}")
                return _handle_exception(state, current_retry, Exception(ctx.metadata.get("error", "Unknown")), actual_callback)

            decision = ctx.get_intermediate("final_decision")
            if not decision:
                decision = {"decision": "unknown", "needs_retry": False, "can_continue": False}

            if decision.get("decision") == "max_retries_reached":
                return _handle_max_retries(state, current_retry, max_retries, actual_callback)

            if decision.get("needs_retry") and decision.get("can_continue"):
                return _handle_retry_coT(state, current_retry, decision, ctx, max_retries, retry_delay, actual_callback)

            return _handle_success_coT(state, current_retry, decision, ctx, actual_callback)

        except Exception as exc:
            return _handle_exception(state, current_retry, exc, actual_callback)

    return reflection_node


def _handle_max_retries(state: Dict[str, Any], current_retry: int, max_retries: int, callback: ReflectionCallback) -> dict[str, Any]:
    logger.warning(f"[Reflection CoT] 达到最大重试次数 {max_retries}，停止优化")
    callback.handle_max_retries(state)

    thought = f"反思评估(CoT): 已达到最大重试次数({current_retry}/{max_retries})，停止优化，启用降级策略"

    return {
        "reflection_result": {
            "feedback": f"已达到最大优化次数({max_retries})，停止迭代",
            "quality_score": 0.0,
            "needs_retry": False,
            "optimized": False,
            "can_continue": False,
            "max_retries_reached": True,
            "retry_count": current_retry,
            "errors": [],
            "cot_chain": [],
        },
        "retry_count": current_retry,
        "thought": thought,
        "messages": [AIMessage(content="反思: 达到最大重试次数，启用降级策略")],
    }


def _handle_retry_coT(state: Dict[str, Any], current_retry: int, decision: Dict[str, Any], ctx, max_retries: int, retry_delay: float, callback: ReflectionCallback) -> dict[str, Any]:
    logger.info(f"[Reflection CoT] 检测到需要优化，触发重试机制")

    if retry_delay > 0:
        time.sleep(retry_delay)

    callback.handle_retry(state, current_retry + 1)

    optimized_query = decision.get("optimized_query", state.get("user_query", ""))
    optimized_parsed = decision.get("optimized_parsed", state.get("parsed_question", {}))

    thought = (
        f"反思评估(CoT): quality={decision.get('quality_score', 0.0)}, "
        f"errors={len(decision.get('errors', []))}, 需要优化=True, "
        f"优化查询={optimized_query[:30]}..., "
        f"重试次数={current_retry + 1}/{max_retries}"
    )

    logger.info(f"[Reflection CoT] 重试 {current_retry + 1}/{max_retries}: {optimized_query}")

    return {
        "reflection_result": {
            "feedback": f"发现问题({len(decision.get('errors', []))}项)，正在优化查询",
            "quality_score": decision.get("quality_score", 0.0),
            "needs_retry": True,
            "optimized": True,
            "can_continue": True,
            "errors": decision.get("errors", []),
            "strategies": decision.get("strategies", []),
            "max_retries_reached": False,
            "retry_count": current_retry + 1,
            "cot_chain": ctx.get_full_chain() if hasattr(ctx, "get_full_chain") else [],
        },
        "user_query": optimized_query,
        "parsed_question": optimized_parsed,
        "retry_count": current_retry + 1,
        "thought": thought,
        "messages": [AIMessage(content=f"反思: {', '.join(e.get('description', '') for e in decision.get('errors', []))}，正在优化...")],
    }


def _handle_success_coT(state: Dict[str, Any], current_retry: int, decision: Dict[str, Any], ctx, callback: ReflectionCallback) -> dict[str, Any]:
    logger.info(f"[Reflection CoT] 查询质量满意，输出结果")
    callback.handle_success(state)

    thought = (
        f"反思评估(CoT): quality={decision.get('quality_score', 0.0)}, "
        f"errors={len(decision.get('errors', []))}, 查询质量满意, "
        f"总重试次数={current_retry}"
    )

    return {
        "reflection_result": {
            "feedback": "查询质量满意",
            "quality_score": decision.get("quality_score", 0.0),
            "needs_retry": False,
            "optimized": False,
            "can_continue": False,
            "errors": decision.get("errors", []),
            "strategies": [],
            "max_retries_reached": False,
            "retry_count": current_retry,
            "cot_chain": ctx.get_full_chain() if hasattr(ctx, "get_full_chain") else [],
        },
        "thought": thought,
        "messages": [AIMessage(content=f"反思完成: 查询质量评分={decision.get('quality_score', 0.0)}, 重试={current_retry}次")],
    }


def _handle_exception(state: Dict[str, Any], current_retry: int, exc: Exception, callback: ReflectionCallback) -> dict[str, Any]:
    logger.error(f"[Reflection CoT] 反思过程发生异常: {exc}", exc_info=True)
    callback.handle_error(exc, state)

    thought = f"反思评估(CoT): 发生异常={exc}，启用降级策略"

    return {
        "reflection_result": {
            "feedback": f"反思过程发生错误: {exc}",
            "quality_score": 0.0,
            "needs_retry": False,
            "optimized": False,
            "can_continue": False,
            "error_occurred": True,
            "error_message": str(exc),
            "retry_count": current_retry,
            "errors": [],
            "cot_chain": [],
        },
        "tool_error": str(exc),
        "retry_count": current_retry,
        "thought": thought,
        "messages": [AIMessage(content=f"反思异常: {exc}，启用降级策略")],
    }


def route_after_reflection(state: AgentState) -> str:
    reflection_result = state.get("reflection_result", {})

    if reflection_result.get("error_occurred"):
        return "final_answer_node"

    needs_retry = reflection_result.get("needs_retry", False)
    can_continue = reflection_result.get("can_continue", False)
    max_retries_reached = reflection_result.get("max_retries_reached", False)

    if max_retries_reached:
        return "final_answer_node"

    if needs_retry and can_continue:
        return "tool_router"

    return "final_answer_node"


def create_reflection_callback(
    on_retry_log: bool = True,
    on_max_retries_log: bool = True,
    on_error_log: bool = True,
    on_success_log: bool = False,
) -> ReflectionCallback:
    callbacks = {}

    if on_retry_log:
        def log_retry(state, retry_count):
            logger.info(f"[Callback] 重试触发, retry_count={retry_count}")
        callbacks["on_retry"] = log_retry

    if on_max_retries_log:
        def log_max_retries(state):
            logger.warning(f"[Callback] 达到最大重试次数")
        callbacks["on_max_retries"] = log_max_retries

    if on_error_log:
        def log_error(exc, state):
            logger.error(f"[Callback] 反思异常: {exc}")
        callbacks["on_error"] = log_error

    if on_success_log:
        def log_success(state):
            logger.info(f"[Callback] 反思成功")
        callbacks["on_success"] = log_success

    return ReflectionCallback(**callbacks)


def run_reflection_node_tests():
    import logging
    logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')

    print("\n=== Test 1: 首次反思，需要重试 ===")
    reflection = create_reflection_node(max_retries=3)
    state1 = {
        "user_query": "进入",
        "parsed_question": {"event": None},
        "hybrid_result": [],
        "retry_count": 0,
        "tool_error": None,
    }
    out1 = reflection(state1, {}, None)
    print(f"needs_retry: {out1['reflection_result']['needs_retry']}")
    print(f"retry_count: {out1['retry_count']}")
    assert out1["reflection_result"]["needs_retry"] == True
    assert out1["retry_count"] == 1

    print("\n=== Test 2: 达到最大重试次数 ===")
    reflection = create_reflection_node(max_retries=2)
    state2 = {
        "user_query": "进入",
        "parsed_question": {"event": None},
        "hybrid_result": [],
        "retry_count": 2,
        "tool_error": None,
    }
    out2 = reflection(state2, {}, None)
    print(f"needs_retry: {out2['reflection_result']['needs_retry']}")
    print(f"max_retries_reached: {out2['reflection_result'].get('max_retries_reached')}")
    assert out2["reflection_result"]["needs_retry"] == False
    assert out2["reflection_result"]["max_retries_reached"] == True

    print("\n=== Test 3: 查询质量满意 ===")
    reflection = create_reflection_node(max_retries=3)
    state3 = {
        "user_query": "红色车辆进入镜头",
        "parsed_question": {"event": "进入", "color": "红色"},
        "hybrid_result": [{"event_id": 1}, {"event_id": 2}, {"event_id": 3}],
        "retry_count": 0,
        "tool_error": None,
    }
    out3 = reflection(state3, {}, None)
    print(f"needs_retry: {out3['reflection_result']['needs_retry']}")
    print(f"quality_score: {out3['reflection_result']['quality_score']}")
    assert out3["reflection_result"]["needs_retry"] == False

    print("\n=== Test 4: 路由函数 - 需要重试 ===")
    state5 = {"reflection_result": {"needs_retry": True, "can_continue": True, "max_retries_reached": False}}
    route5 = route_after_reflection(state5)
    print(f"route: {route5}")
    assert route5 == "tool_router"

    print("\n=== Test 5: 路由函数 - 达到最大次数 ===")
    state6 = {"reflection_result": {"needs_retry": True, "can_continue": True, "max_retries_reached": True}}
    route6 = route_after_reflection(state6)
    print(f"route: {route6}")
    assert route6 == "final_answer_node"

    print("\n=== Test 6: 路由函数 - 查询满意 ===")
    state7 = {"reflection_result": {"needs_retry": False, "can_continue": False, "max_retries_reached": False}}
    route7 = route_after_reflection(state7)
    print(f"route: {route7}")
    assert route7 == "final_answer_node"

    print("\n=== All tests passed! ===")


if __name__ == "__main__":
    run_reflection_node_tests()
