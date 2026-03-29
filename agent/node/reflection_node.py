import logging
import time
from typing import Any, Callable, Dict, List, Optional

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.store.base import BaseStore

from .error_classifier import ErrorClassifier, create_error_classifier
from .query_evaluator import QueryEvaluator, create_query_evaluator
from .query_optimizer import QueryOptimizer, create_query_optimizer
from .types import AgentState

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


def create_reflection_node(
    llm: Any = None,
    max_retries: int = DEFAULT_MAX_RETRIES,
    retry_delay: float = DEFAULT_RETRY_DELAY,
    callback: Optional[ReflectionCallback] = None,
):
    evaluator = create_query_evaluator()
    classifier = create_error_classifier()
    optimizer = create_query_optimizer()
    actual_callback = callback or ReflectionCallback()

    def reflection_node(state: AgentState, config: RunnableConfig, store: BaseStore) -> dict[str, Any]:
        del config, store
        current_retry = int(state.get("retry_count", 0) or 0)
        user_query = state.get("user_query", "")
        parsed_question = state.get("parsed_question", {})
        tool_error = state.get("tool_error")

        logger.info(f"[Reflection] 第{current_retry + 1}次反思开始, 当前重试次数={current_retry}/{max_retries}")

        try:
            if current_retry >= max_retries:
                return _handle_max_retries(state, current_retry, max_retries, actual_callback)

            search_result = _get_search_result(state)
            quality_score = evaluator.evaluate(user_query, parsed_question, search_result)
            errors = classifier.classify(quality_score, parsed_question, tool_error)
            needs_retry = classifier.needs_optimization(errors) and current_retry < max_retries
            can_continue = current_retry < max_retries

            if needs_retry and can_continue:
                return _handle_retry(
                    state, current_retry, quality_score, errors,
                    optimizer, user_query, parsed_question,
                    max_retries, retry_delay, actual_callback
                )

            return _handle_success(
                state, quality_score, errors, current_retry, actual_callback
            )

        except Exception as exc:
            return _handle_exception(state, current_retry, exc, actual_callback)

    return reflection_node


def _get_search_result(state: AgentState) -> List[Dict[str, Any]]:
    return (
        state.get("hybrid_result")
        or state.get("sql_result")
        or state.get("video_vect_result")
        or state.get("merged_result")
        or []
    )


def _handle_max_retries(
    state: Dict[str, Any],
    current_retry: int,
    max_retries: int,
    callback: ReflectionCallback
) -> dict[str, Any]:
    logger.warning(f"[Reflection] 达到最大重试次数 {max_retries}，停止优化")
    callback.handle_max_retries(state)

    thought = f"反思评估: 已达到最大重试次数({current_retry}/{max_retries})，停止优化，启用降级策略"

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
        },
        "retry_count": current_retry,
        "thought": thought,
        "messages": [AIMessage(content="反思: 达到最大重试次数，启用降级策略")],
    }


def _handle_retry(
    state: Dict[str, Any],
    current_retry: int,
    quality_score: Dict[str, Any],
    errors: List[Dict[str, Any]],
    optimizer: QueryOptimizer,
    user_query: str,
    parsed_question: Dict[str, Any],
    max_retries: int,
    retry_delay: float,
    callback: ReflectionCallback
) -> dict[str, Any]:
    logger.info(f"[Reflection] 检测到需要优化，触发重试机制")

    if retry_delay > 0:
        time.sleep(retry_delay)

    optimization = optimizer.optimize(user_query, parsed_question, errors)
    optimized_query = optimization.get("optimized_query", user_query)
    optimized_parsed = optimization.get("optimized_parsed", parsed_question)

    callback.handle_retry(state, current_retry + 1)

    thought = (
        f"反思评估: quality={quality_score.get('overall')}, "
        f"errors={len(errors)}, 需要优化={True}, "
        f"优化查询={optimized_query}, "
        f"重试次数={current_retry + 1}/{max_retries}"
    )

    logger.info(f"[Reflection] 重试 {current_retry + 1}/{max_retries}: {optimized_query}")

    return {
        "reflection_result": {
            "feedback": f"发现问题({len(errors)}项)，正在优化查询",
            "quality_score": quality_score.get("overall", 0.0),
            "needs_retry": True,
            "optimized": True,
            "can_continue": True,
            "errors": errors,
            "max_retries_reached": False,
            "retry_count": current_retry + 1,
        },
        "user_query": optimized_query,
        "parsed_question": optimized_parsed,
        "retry_count": current_retry + 1,
        "thought": thought,
        "messages": [AIMessage(content=f"反思: {quality_score.get('issues', [])}，正在优化...")],
    }


def _handle_success(
    state: Dict[str, Any],
    quality_score: Dict[str, Any],
    errors: List[Dict[str, Any]],
    current_retry: int,
    callback: ReflectionCallback
) -> dict[str, Any]:
    logger.info(f"[Reflection] 查询质量满意，输出结果")
    callback.handle_success(state)

    thought = (
        f"反思评估: quality={quality_score.get('overall')}, "
        f"errors={len(errors)}, 查询质量满意, "
        f"总重试次数={current_retry}"
    )

    return {
        "reflection_result": {
            "feedback": "查询质量满意",
            "quality_score": quality_score.get("overall", 0.0),
            "needs_retry": False,
            "optimized": False,
            "can_continue": False,
            "errors": errors,
            "max_retries_reached": False,
            "retry_count": current_retry,
        },
        "thought": thought,
        "messages": [AIMessage(content=f"反思完成: 查询质量评分={quality_score.get('overall')}, 重试={current_retry}次")],
    }


def _handle_exception(
    state: Dict[str, Any],
    current_retry: int,
    exc: Exception,
    callback: ReflectionCallback
) -> dict[str, Any]:
    logger.error(f"[Reflection] 反思过程发生异常: {exc}", exc_info=True)
    callback.handle_error(exc, state)

    thought = f"反思评估: 发生异常={exc}，启用降级策略"

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
    print(f"optimized_query: {out1.get('user_query')}")
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

    print("\n=== Test 4: 回调函数触发 ===")
    retry_callbacks = []
    def track_retry(state, retry_count):
        retry_callbacks.append(retry_count)

    callback = ReflectionCallback(on_retry=track_retry)
    reflection = create_reflection_node(max_retries=3, callback=callback)
    state4 = {
        "user_query": "进入",
        "parsed_question": {"event": None},
        "hybrid_result": [],
        "retry_count": 0,
        "tool_error": None,
    }
    out4 = reflection(state4, {}, None)
    print(f"callback triggered: {len(retry_callbacks) > 0}")
    assert len(retry_callbacks) > 0

    print("\n=== Test 5: 路由函数 - 需要重试 ===")
    state5 = {"reflection_result": {"needs_retry": True, "can_continue": True, "max_retries_reached": False}}
    route5 = route_after_reflection(state5)
    print(f"route: {route5}")
    assert route5 == "tool_router"

    print("\n=== Test 6: 路由函数 - 达到最大次数 ===")
    state6 = {"reflection_result": {"needs_retry": True, "can_continue": True, "max_retries_reached": True}}
    route6 = route_after_reflection(state6)
    print(f"route: {route6}")
    assert route6 == "final_answer_node"

    print("\n=== Test 7: 路由函数 - 查询满意 ===")
    state7 = {"reflection_result": {"needs_retry": False, "can_continue": False, "max_retries_reached": False}}
    route7 = route_after_reflection(state7)
    print(f"route: {route7}")
    assert route7 == "final_answer_node"

    print("\n=== All tests passed! ===")


if __name__ == "__main__":
    run_reflection_node_tests()