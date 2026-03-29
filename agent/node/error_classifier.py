from typing import Any, Dict, List, Optional, TypedDict


class ErrorType(TypedDict):
    category: str
    sub_category: str
    description: str
    severity: str


class ErrorClassifier:
    EMPTY_RESULT = "empty_result"
    TOO_FEW_RESULTS = "too_few_results"
    TOO_MANY_RESULTS = "too_many_results"
    AMBIGUOUS_QUERY = "ambiguous_query"
    MISSING_EVENT = "missing_event"
    MISSING_TIME = "missing_time"
    MISSING_COLOR = "missing_color"
    SYNTAX_ERROR = "syntax_error"
    NO_ERROR = "no_error"

    def classify(
        self,
        quality_score: Dict[str, Any],
        parsed_question: Dict[str, Any],
        tool_error: Optional[str] = None,
    ) -> List[ErrorType]:
        errors: list[ErrorType] = []

        if tool_error:
            errors.append(ErrorType(
                category="tool_error",
                sub_category="execution",
                description=str(tool_error),
                severity="high",
            ))

        issues = quality_score.get("issues", [])
        for issue in issues:
            if "为空" in issue:
                errors.append(ErrorType(
                    category=self.EMPTY_RESULT,
                    sub_category="no_data",
                    description=issue,
                    severity="high",
                ))
            elif "过少" in issue:
                errors.append(ErrorType(
                    category=self.TOO_FEW_RESULTS,
                    sub_category="insufficient",
                    description=issue,
                    severity="medium",
                ))
            elif "过多" in issue:
                errors.append(ErrorType(
                    category=self.TOO_MANY_RESULTS,
                    sub_category="excessive",
                    description=issue,
                    severity="medium",
                ))
            elif "完整性不足" in issue:
                errors.append(ErrorType(
                    category=self.AMBIGUOUS_QUERY,
                    sub_category="incomplete",
                    description=issue,
                    severity="high",
                ))

        if not parsed_question.get("event") or (isinstance(parsed_question.get("event"), str) and parsed_question.get("event", "").lower() == "null"):
            errors.append(ErrorType(
                category=self.MISSING_EVENT,
                sub_category="field_missing",
                description="缺少事件类型描述",
                severity="high",
            ))

        return errors

    def has_critical_errors(self, errors: List[ErrorType]) -> bool:
        return any(e.get("severity") == "high" for e in errors)

    def needs_optimization(self, errors: List[ErrorType]) -> bool:
        return len(errors) > 0


def create_error_classifier() -> ErrorClassifier:
    return ErrorClassifier()


if __name__ == "__main__":
    classifier = create_error_classifier()

    errors = classifier.classify(
        {"issues": ["检索结果为空"]},
        {"event": "进入"},
    )
    print("errors:", errors)
    print("has critical:", classifier.has_critical_errors(errors))