from typing import Any, Dict, List, Optional

from .error_classifier import ErrorClassifier, ErrorType


class QueryOptimizer:
    def __init__(self):
        self.classifier = ErrorClassifier()

    def optimize(
        self,
        user_query: str,
        parsed_question: Dict[str, Any],
        errors: List[ErrorType],
    ) -> Dict[str, Any]:
        optimized_query = user_query
        optimized_parsed = dict(parsed_question)

        for error in errors:
            category = error.get("category", "")

            if category == ErrorClassifier.MISSING_EVENT:
                optimized_query, optimized_parsed = self._supplement_event(optimized_query, optimized_parsed)

            elif category == ErrorClassifier.TOO_FEW_RESULTS:
                optimized_query, optimized_parsed = self._relax_conditions(optimized_query, optimized_parsed)

            elif category == ErrorClassifier.TOO_MANY_RESULTS:
                optimized_query, optimized_parsed = self._tighten_conditions(optimized_query, optimized_parsed)

            elif category == ErrorClassifier.AMBIGUOUS_QUERY:
                optimized_query, optimized_parsed = self._clarify_query(optimized_query, optimized_parsed)

        return {
            "optimized_query": optimized_query,
            "optimized_parsed": optimized_parsed,
            "optimization_applied": len(errors) > 0,
        }

    def _supplement_event(self, query: str, parsed: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
        if not parsed.get("event") or parsed.get("event", "").lower() == "null":
            optimized_query = query + "的目标出现"
            optimized_parsed = dict(parsed)
            optimized_parsed["event"] = "出现"
        return optimized_query, optimized_parsed

    def _relax_conditions(self, query: str, parsed: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
        optimized_query = query
        optimized_parsed = dict(parsed)

        time_condition = [k for k in optimized_parsed if "time" in k.lower()]
        for k in time_condition:
            del optimized_parsed[k]

        optimized_query = query + "（已放宽时间条件）"
        return optimized_query, optimized_parsed

    def _tighten_conditions(self, query: str, parsed: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
        optimized_query = query + "（需更精确条件）"
        optimized_parsed = dict(parsed)
        return optimized_query, optimized_parsed

    def _clarify_query(self, query: str, parsed: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
        color = parsed.get("color")
        if not color or color.lower() == "null":
            optimized_query = query
        else:
            optimized_query = f"{color}的{parsed.get('event', '目标')}"
        optimized_parsed = dict(parsed)
        return optimized_query, optimized_parsed


def create_query_optimizer() -> QueryOptimizer:
    return QueryOptimizer()


if __name__ == "__main__":
    optimizer = create_query_optimizer()

    result = optimizer.optimize(
        "车进入",
        {"event": None, "color": "红色"},
        [{"category": "missing_event", "sub_category": "field_missing", "description": "缺少事件", "severity": "high"}],
    )
    print("optimized:", result)