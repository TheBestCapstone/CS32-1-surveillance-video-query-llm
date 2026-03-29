from typing import Any, Dict, List

from .types import ReflectionResult


def do_reflection(rows: List[Dict[str, Any]], event_list: List[str], meta_list: List[Dict[str, Any]]) -> ReflectionResult:
    result_count = len(rows)
    feedback = None
    quality_score = 1.0
    needs_retry = False

    if result_count == 0:
        feedback = "检索结果为空，建议补充更多查询条件或放宽过滤条件"
        quality_score = 0.0
        needs_retry = True
    elif result_count < 3:
        feedback = f"检索结果较少({result_count}条)，结果可能不够全面"
        quality_score = 0.5
    elif result_count > 50:
        feedback = f"检索结果较多({result_count}条)，建议增加更精确的过滤条件"
        quality_score = 0.7

    return ReflectionResult(
        feedback=feedback,
        quality_score=quality_score,
        needs_retry=needs_retry,
    )


def create_reflection_tool():
    def reflection_tool(rows: List[Dict[str, Any]], event_list: List[str], meta_list: List[Dict[str, Any]]) -> ReflectionResult:
        return do_reflection(rows, event_list, meta_list)
    return reflection_tool


if __name__ == "__main__":
    result = do_reflection([{"event_id": 1}], ["进入"], [{"field": "color", "op": "contains", "value": "红"}])
    print("reflection result:", result)