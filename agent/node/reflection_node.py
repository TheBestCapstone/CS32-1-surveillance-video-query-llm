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


class RouteRuleViolation(TypedDict):
    rule_id: str
    conflict_type: str
    detail: str
    suggestion: str


class RouteRuleValidation(TypedDict):
    is_valid: bool
    violations: List[RouteRuleViolation]


def _step_result_review(ctx: CoTContext) -> Dict[str, Any]:
    state = ctx.original_input if isinstance(ctx.original_input, dict) else {}
    user_query = state.get("user_query", "")
    parsed_question = state.get("parsed_question", {})

    search_result = (
        state.get("hybrid_result")
        or state.get("sql_result")
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
    
    state = ctx.original_input if isinstance(ctx.original_input, dict) else {}
    sql_debug = state.get("sql_debug", {})

    if sql_debug.get("last_error"):
        errors.append(ErrorType(
            category="sql_execution_error",
            sub_category="runtime",
            description=f"SQL execution failed: {sql_debug.get('last_error')}",
            severity="high",
        ))
        
    skipped_filters = sql_debug.get("skipped_filters", [])
    if skipped_filters:
        skipped_fields = [list(f.keys())[0] for f in skipped_filters]
        errors.append(ErrorType(
            category="invalid_filter",
            sub_category="field_not_found",
            description=f"Query contains invalid filter fields: {skipped_fields}",
            severity="medium",
        ))

    if result_count == 0:
        errors.append(ErrorType(
            category="empty_result",
            sub_category="no_data",
            description="Empty retrieval result",
            severity="high",
        ))

    if not parsed_question.get("event") or (isinstance(parsed_question.get("event"), str) and parsed_question.get("event", "").lower() in ("null", "none", "")):
        errors.append(ErrorType(
            category="missing_event",
            sub_category="field_missing",
            description="Missing event type description",
            severity="high",
        ))

    if result_count > 0 and result_count < 3:
        errors.append(ErrorType(
            category="too_few_results",
            sub_category="insufficient",
            description=f"Too few results ({result_count}), query conditions might be too strict",
            severity="medium",
        ))

    if result_count > 100:
        errors.append(ErrorType(
            category="too_many_results",
            sub_category="excessive",
            description=f"Too many results ({result_count}), query conditions might be too loose",
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
        
        state = ctx.original_input if isinstance(ctx.original_input, dict) else {}
        if state.get("current_node", "") in ("pure_sql_node", "hybrid_search_node"):
            # If sub-agent has completed execution, no need for the main graph to intervene
            root_causes.append(RootCauseAnalysis(
                root_cause="Sub-agent completed autonomous retrieval, no main graph intervention needed",
                affected_fields=[],
                severity="low",
                recommendation="Stop optimization",
            ))
            continue
        severity = error.get("severity", "medium")

        if category == "empty_result":
            root_causes.append(RootCauseAnalysis(
                root_cause="Query conditions cannot match any results",
                affected_fields=["event", "meta_list"],
                severity=severity,
                recommendation="Relax query conditions or add more keywords",
            ))
        elif category == "missing_event":
            root_causes.append(RootCauseAnalysis(
                root_cause="Missing core event description, retrieval lacks clear target",
                affected_fields=["event"],
                severity=severity,
                recommendation="Supplement event type, such as enter, leave, appear, etc.",
            ))
        elif category == "too_few_results":
            root_causes.append(RootCauseAnalysis(
                root_cause="Query conditions are too strict",
                affected_fields=["meta_list"],
                severity=severity,
                recommendation="Relax time, color, and other filtering conditions",
            ))
        elif category == "too_many_results":
            root_causes.append(RootCauseAnalysis(
                root_cause="Query conditions are too loose",
                affected_fields=["meta_list"],
                severity=severity,
                recommendation="Add more precise filtering conditions",
            ))

    if not root_causes:
        root_causes.append(RootCauseAnalysis(
            root_cause="No obvious issues",
            affected_fields=[],
            severity="low",
            recommendation="Keep current query",
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
        issues.append("User query is empty")
        completeness = 0.0
        clarity = 0.0

    if not review.get("parsed_question", {}).get("event"):
        completeness -= 0.3

    result_count = review.get("result_count", 0)
    if result_count == 0:
        issues.append("Retrieval result is empty")
        completeness = 0.3
    elif result_count < 3:
        completeness = 0.5
    elif result_count > 100:
        completeness = 0.7

    if completeness < 0.5:
        issues.append("Query completeness is insufficient, optimization needed")

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
    
    state = ctx.original_input if isinstance(ctx.original_input, dict) else {}
    if state.get("current_node", "") in ("pure_sql_node", "hybrid_search_node"):
        # If sub-agent has completed execution, it has performed its internal autonomous retry. The main graph does not need to generate strategies or retry.
        strategies.append(OptimizationStrategy(
            strategy_name="unoptimizable",
            changes={"unoptimizable": True},
            expected_improvement="Sub-agent completed autonomous retrieval, no main graph intervention needed",
            risk_level="none",
        ))
        return strategies

    for error in errors:
        category = error.get("category", "")

        if category == "missing_event":
            strategies.append(OptimizationStrategy(
                strategy_name="supplement_event",
                changes={"event": "appear"},
                expected_improvement="Better retrieval with supplemented event description",
                risk_level="low",
            ))
        elif category == "too_few_results":
            state = ctx.original_input if isinstance(ctx.original_input, dict) else {}
            if state.get("current_node", "") in ("pure_sql_node", "hybrid_search_node"):
                strategies.append(OptimizationStrategy(
                    strategy_name="unoptimizable",
                    changes={"unoptimizable": True},
                    expected_improvement="Sub-agent completed autonomous retrieval, few results is normal, no retry",
                    risk_level="none",
                ))
            else:
                strategies.append(OptimizationStrategy(
                    strategy_name="relax_conditions",
                    changes={"remove_time_filter": True},
                    expected_improvement="More results after relaxing conditions",
                    risk_level="medium",
                ))
        elif category == "too_many_results":
            state = ctx.original_input if isinstance(ctx.original_input, dict) else {}
            if state.get("current_node", "") in ("pure_sql_node", "hybrid_search_node"):
                strategies.append(OptimizationStrategy(
                    strategy_name="unoptimizable",
                    changes={"unoptimizable": True},
                    expected_improvement="Sub-agent completed autonomous retrieval, many results is normal, no retry",
                    risk_level="none",
                ))
            else:
                strategies.append(OptimizationStrategy(
                    strategy_name="tighten_conditions",
                    changes={"add_color_filter": True},
                    expected_improvement="More relevant results with precise conditions",
                    risk_level="medium",
                ))
        elif category == "invalid_filter":
            strategies.append(OptimizationStrategy(
                strategy_name="remove_invalid_field",
                changes={"remove_strict_filters": True},
                expected_improvement="Remove unsupported field filtering",
                risk_level="low",
            ))
        elif category == "empty_result":
            state = ctx.original_input if isinstance(ctx.original_input, dict) else {}
            current_node = state.get("current_node", "")
            parsed = state.get("parsed_question", {})
            
            # Dynamic check: if sub-agent completed with empty results, or conditions are minimal, determine as unoptimizable
            if current_node in ("pure_sql_node", "hybrid_search_node") or (not parsed.get("color") and not parsed.get("location") and not parsed.get("time")):
                strategies.append(OptimizationStrategy(
                    strategy_name="unoptimizable",
                    changes={"unoptimizable": True},
                    expected_improvement="Sub-agent completed autonomous retrieval or conditions are minimal, target likely does not exist, stop blind retries",
                    risk_level="none",
                ))
            else:
                strategies.append(OptimizationStrategy(
                    strategy_name="generalize_query",
                    changes={"remove_strict_filters": True, "remove_color": True, "remove_location": True},
                    expected_improvement="Generalize query to get results",
                    risk_level="medium",
                ))

    if not strategies:
        strategies.append(OptimizationStrategy(
            strategy_name="no_change",
            changes={},
            expected_improvement="No optimization needed",
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
            warnings.append(f"Strategy {strategy['strategy_name']} has high risk")
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


def _step_route_rule_validation(ctx: CoTContext) -> RouteRuleValidation:
    state = ctx.original_input if isinstance(ctx.original_input, dict) else {}
    tool_choice = state.get("tool_choice", {}) if isinstance(state.get("tool_choice", {}), dict) else {}
    mode = tool_choice.get("mode", "")
    sql_needed = bool(tool_choice.get("sql_needed", False))
    hybrid_needed = bool(tool_choice.get("hybrid_needed", False))
    sub_queries = tool_choice.get("sub_queries", {}) if isinstance(tool_choice.get("sub_queries", {}), dict) else {}
    retry_count = int(state.get("retry_count", 0) or 0)
    max_retries = int(ctx.metadata.get("max_retries", DEFAULT_MAX_RETRIES))
    search_cfg = state.get("search_config", {}) if isinstance(state.get("search_config", {}), dict) else {}
    candidate_limit = int(search_cfg.get("candidate_limit", 80) or 80)

    violations: List[RouteRuleViolation] = []
    allowed_modes = {"hybrid_search", "pure_sql"}
    if mode not in allowed_modes:
        violations.append(RouteRuleViolation(
            rule_id="RR-001",
            conflict_type="unreachable_node",
            detail=f"mode={mode} not in allowed set {sorted(allowed_modes)}",
            suggestion="Restrict route output to hybrid_search or pure_sql.",
        ))
    if sql_needed and hybrid_needed:
        violations.append(RouteRuleViolation(
            rule_id="RR-002",
            conflict_type="logic_conflict",
            detail="sql_needed and hybrid_needed are both True.",
            suggestion="Structured priority scenarios should only enable pure_sql; semantic priority scenarios should only enable hybrid_search.",
        ))
    if mode == "pure_sql" and not sql_needed:
        violations.append(RouteRuleViolation(
            rule_id="RR-003",
            conflict_type="logic_conflict",
            detail="mode=pure_sql but sql_needed=False.",
            suggestion="Keep mode consistent with needed flags.",
        ))
    if mode == "hybrid_search" and not hybrid_needed:
        violations.append(RouteRuleViolation(
            rule_id="RR-004",
            conflict_type="logic_conflict",
            detail="mode=hybrid_search but hybrid_needed=False.",
            suggestion="Keep mode consistent with needed flags.",
        ))
    if set(sub_queries.keys()) - {"sql", "hybrid"}:
        violations.append(RouteRuleViolation(
            rule_id="RR-005",
            conflict_type="unreachable_node",
            detail=f"sub_queries has invalid keys: {list(set(sub_queries.keys()) - {'sql', 'hybrid'})}",
            suggestion="Only keep sql/hybrid sub-query keys.",
        ))
    if retry_count > max_retries:
        violations.append(RouteRuleViolation(
            rule_id="RR-006",
            conflict_type="dead_loop",
            detail=f"retry_count={retry_count} exceeds max_retries={max_retries}",
            suggestion="Force terminate retry loop in route_after_reflection.",
        ))
    if mode == "hybrid_search" and candidate_limit > 200:
        violations.append(RouteRuleViolation(
            rule_id="RR-007",
            conflict_type="performance_bottleneck",
            detail=f"candidate_limit={candidate_limit} is too high, may cause latency spikes.",
            suggestion="Keep candidate_limit between 80~200, and tune based on hit rate.",
        ))

    return RouteRuleValidation(is_valid=len(violations) == 0, violations=violations)


def _step_final_decision(ctx: CoTContext) -> Dict[str, Any]:
    needs_optimization: bool = ctx.get_intermediate("quality_evaluation")
    if not isinstance(needs_optimization, bool):
        needs_optimization = _step_quality_evaluation(ctx)

    errors: List[ErrorType] = ctx.get_intermediate("error_location")
    score: QualityScore = ctx.get_intermediate("quality_scoring")
    strategies: List[OptimizationStrategy] = ctx.get_intermediate("strategy_generation")
    route_validation: RouteRuleValidation = ctx.get_intermediate("route_rule_validation")

    if route_validation and not route_validation.get("is_valid", True):
        return {
            "decision": "validation_failed",
            "feedback": "Route rule validation failed, proceeding to next stage is prohibited",
            "needs_retry": False,
            "can_continue": False,
            "validation_failed": True,
            "violations": route_validation.get("violations", []),
            "quality_score": score.get("overall", 0.0) if score else 0.0,
            "errors": errors or [],
            "strategies": [],
        }

    current_retry = ctx.original_input.get("retry_count", 0) if isinstance(ctx.original_input, dict) else 0
    max_retries = ctx.metadata.get("max_retries", DEFAULT_MAX_RETRIES)

    if current_retry >= max_retries:
        return {
            "decision": "max_retries_reached",
            "feedback": f"Maximum optimization iterations ({max_retries}) reached, stopping iteration",
            "needs_retry": False,
            "can_continue": False,
            "quality_score": score.get("overall", 0.0) if score else 0.0,
            "errors": errors or [],
            "strategies": strategies or [],
        }

    if not needs_optimization:
        return {
            "decision": "satisfactory",
            "feedback": "Query quality is satisfactory",
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
        
        # Handle unoptimizable cases
        if changes.get("unoptimizable"):
            return {
                "decision": "unoptimizable",
                "feedback": "Current query conditions have been simplified to the limit, target highly likely does not exist, stopping retry",
                "needs_retry": False,
                "can_continue": False,
                "quality_score": score.get("overall", 0.0) if score else 0.0,
                "errors": errors or [],
                "strategies": strategies or [],
            }

        if "event" in changes:
            optimized_parsed["event"] = changes["event"]
            optimized_query = f"{optimized_query} {changes['event']}"
        if changes.get("remove_time_filter"):
            optimized_parsed.pop("time", None)
            optimized_query += " (Relaxed time condition)"
        if changes.get("remove_color"):
            optimized_parsed.pop("color", None)
            optimized_query += " (Removed color condition)"
        if changes.get("remove_location"):
            optimized_parsed.pop("location", None)
            optimized_query += " (Removed location condition)"
        if changes.get("remove_strict_filters"):
            optimized_query += " (Relaxed filtering conditions)"
        if changes.get("add_color_filter"):
            optimized_query += " (Requires more precise conditions)"

    return {
        "decision": "retry",
        "feedback": f"Found issues ({len(errors)} items), optimizing query",
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

    review_step = SequentialCoTStep("result_review", _step_result_review, "Result Review")
    location_step = SequentialCoTStep("error_location", _step_error_location, "Error Location")
    root_cause_step = SequentialCoTStep("root_cause_analysis", _step_root_cause_analysis, "Root Cause Analysis")
    scoring_step = SequentialCoTStep("quality_scoring", _step_quality_scoring, "Quality Scoring")
    strategy_step = SequentialCoTStep("strategy_generation", _step_strategy_generation, "Strategy Generation")
    validation_step = SequentialCoTStep("strategy_validation", _step_strategy_validation, "Strategy Validation")
    eval_step = SequentialCoTStep("quality_evaluation", _step_quality_evaluation, "Quality Evaluation")
    route_validation_step = SequentialCoTStep("route_rule_validation", _step_route_rule_validation, "Route Rule Validation")
    decision_step = SequentialCoTStep("final_decision", _step_final_decision, "Final Decision")

    engine.add_step(review_step)
    engine.add_step(location_step)
    engine.add_step(root_cause_step)
    engine.add_step(scoring_step)
    engine.add_step(strategy_step)
    engine.add_step(validation_step)
    engine.add_step(eval_step)
    engine.add_step(route_validation_step)
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
        logger.info(f"[Reflection CoT] Starting reflection #{current_retry + 1}, current_retry={current_retry}/{max_retries}")

        try:
            if current_retry >= max_retries:
                return _handle_max_retries(state, current_retry, max_retries, actual_callback)

            ctx = cot_engine.execute(state, max_duration_ms=10000.0)

            if ctx.status == StepStatus.FAILED:
                logger.warning(f"[Reflection CoT] Inference failed: {ctx.metadata.get('error')}")
                return _handle_exception(state, current_retry, Exception(ctx.metadata.get("error", "Unknown")), actual_callback)

            decision = ctx.get_intermediate("final_decision")
            if not decision:
                decision = {"decision": "unknown", "needs_retry": False, "can_continue": False}

            if decision.get("decision") == "max_retries_reached":
                return _handle_max_retries(state, current_retry, max_retries, actual_callback)

            if decision.get("decision") == "validation_failed":
                return _handle_validation_failed(state, current_retry, decision)

            if decision.get("needs_retry") and decision.get("can_continue"):
                return _handle_retry_coT(state, current_retry, decision, ctx, max_retries, retry_delay, actual_callback)

            return _handle_success_coT(state, current_retry, decision, ctx, actual_callback)

        except Exception as exc:
            return _handle_exception(state, current_retry, exc, actual_callback)

    return reflection_node


def _handle_max_retries(state: Dict[str, Any], current_retry: int, max_retries: int, callback: ReflectionCallback) -> dict[str, Any]:
    logger.warning(f"[Reflection CoT] Reached maximum retries {max_retries}, stopping optimization")
    callback.handle_max_retries(state)

    thought = f"Reflection Assessment (CoT): Reached maximum retries ({current_retry}/{max_retries}), stopping optimization, enabling fallback strategy"

    return {
        "reflection_result": {
            "feedback": f"Reached maximum optimization iterations ({max_retries}), stopping iteration",
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
        "messages": [AIMessage(content="Reflection: Reached maximum retries, enabling fallback strategy")],
    }


def _handle_retry_coT(state: Dict[str, Any], current_retry: int, decision: Dict[str, Any], ctx, max_retries: int, retry_delay: float, callback: ReflectionCallback) -> dict[str, Any]:
    logger.info(f"[Reflection CoT] Optimization needed detected, triggering retry mechanism")

    if retry_delay > 0:
        time.sleep(retry_delay)

    callback.handle_retry(state, current_retry + 1)

    optimized_query = decision.get("optimized_query", state.get("user_query", ""))
    optimized_parsed = decision.get("optimized_parsed", state.get("parsed_question", {}))

    thought = (
        f"Reflection Assessment (CoT): quality={decision.get('quality_score', 0.0)}, "
        f"errors={len(decision.get('errors', []))}, needs_optimization=True, "
        f"optimized_query={optimized_query[:30]}..., "
        f"retry_count={current_retry + 1}/{max_retries}"
    )

    logger.info(f"[Reflection CoT] Retry {current_retry + 1}/{max_retries}: {optimized_query}")

    return {
        "reflection_result": {
            "feedback": f"Found issues ({len(decision.get('errors', []))} items), optimizing query",
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
        "messages": [AIMessage(content=f"Reflection: {', '.join(e.get('description', '') for e in decision.get('errors', []))}, optimizing...")],
    }


def _handle_success_coT(state: Dict[str, Any], current_retry: int, decision: Dict[str, Any], ctx, callback: ReflectionCallback) -> dict[str, Any]:
    logger.info(f"[Reflection CoT] Query quality satisfactory, outputting results")
    callback.handle_success(state)

    thought = (
        f"Reflection Assessment (CoT): quality={decision.get('quality_score', 0.0)}, "
        f"errors={len(decision.get('errors', []))}, query quality satisfactory, "
        f"total_retries={current_retry}"
    )

    return {
        "reflection_result": {
            "feedback": "Query quality satisfactory",
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
        "messages": [AIMessage(content=f"Reflection Complete: Query quality score={decision.get('quality_score', 0.0)}, retries={current_retry}")],
    }


def _handle_validation_failed(state: Dict[str, Any], current_retry: int, decision: Dict[str, Any]) -> dict[str, Any]:
    violations = decision.get("violations", [])
    details = "; ".join([f"{item.get('rule_id')}:{item.get('conflict_type')}" for item in violations]) or "unknown"
    thought = f"Reflection Assessment (CoT): Route rule validation failed, {details}"
    return {
        "reflection_result": {
            "feedback": decision.get("feedback", "Route rule validation failed"),
            "quality_score": decision.get("quality_score", 0.0),
            "needs_retry": False,
            "optimized": False,
            "can_continue": False,
            "validation_failed": True,
            "violations": violations,
            "retry_count": current_retry,
            "errors": decision.get("errors", []),
            "cot_chain": [],
        },
        "tool_error": "Route rule validation failed",
        "thought": thought,
        "messages": [AIMessage(content=f"Reflection Validation Failed: {details}")],
    }


def _handle_exception(state: Dict[str, Any], current_retry: int, exc: Exception, callback: ReflectionCallback) -> dict[str, Any]:
    logger.error(f"[Reflection CoT] Exception occurred during reflection: {exc}", exc_info=True)
    callback.handle_error(exc, state)

    thought = f"Reflection Assessment (CoT): Exception occurred={exc}, enabling fallback strategy"

    return {
        "reflection_result": {
            "feedback": f"Error occurred during reflection: {exc}",
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
        "messages": [AIMessage(content=f"Reflection Exception: {exc}, enabling fallback strategy")],
    }


def route_after_reflection(state: AgentState) -> str:
    reflection_result = state.get("reflection_result", {})

    if reflection_result.get("validation_failed"):
        return "final_answer_node"

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
            logger.info(f"[Callback] Retry triggered, retry_count={retry_count}")
        callbacks["on_retry"] = log_retry

    if on_max_retries_log:
        def log_max_retries(state):
            logger.warning(f"[Callback] Reached maximum retries")
        callbacks["on_max_retries"] = log_max_retries

    if on_error_log:
        def log_error(exc, state):
            logger.error(f"[Callback] Reflection exception: {exc}")
        callbacks["on_error"] = log_error

    if on_success_log:
        def log_success(state):
            logger.info(f"[Callback] Reflection successful")
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
