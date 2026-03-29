from typing import Any, Dict, List, Optional

from node.preprocess.base import SearchMode


class QueryAnalyzer:
    def __init__(self):
        self.semantic_keywords = {"进入", "离开", "移动", "停止", "出现", "消失", "驶入", "横穿"}

    def analyze_query(self, user_query: str) -> Dict[str, Any]:
        query_lower = user_query.lower()
        has_color = any(kw in query_lower for kw in ["红", "蓝", "白", "黑", "颜色"])
        has_time = any(kw in query_lower for kw in ["今天", "昨天", "上午", "下午", "时间", "点", "时", "日"])
        has_motion = any(kw in query_lower for kw in ["静止", "运动", "移动", "停止"])
        has_object_type = any(kw in query_lower for kw in ["车", "人", "行人", "车辆", "自行车", "摩托车"])
        has_semantic_event = any(kw in query_lower for kw in ["进入", "离开", "移动", "停止", "出现"])

        has_structured_condition = has_color or has_time or has_motion

        return {
            "has_color": has_color,
            "has_time": has_time,
            "has_motion": has_motion,
            "has_object_type": has_object_type,
            "has_semantic_event": has_semantic_event,
            "has_structured_condition": has_structured_condition,
            "recommended_mode": SearchMode.SQL_FILTER_SEMANTIC if has_structured_condition else SearchMode.DIRECT_SEMANTIC,
        }


class SQLSanitizer:
    @staticmethod
    def sanitize_string(value: str, max_length: int = 100) -> str:
        if not isinstance(value, str):
            return ""
        sanitized = value.strip()[:max_length]
        dangerous_patterns = ["'", '"', ";", "--", "/*", "*/", "DROP", "DELETE", "INSERT", "UPDATE", "UNION"]
        for pattern in dangerous_patterns:
            if pattern.upper() in sanitized.upper():
                sanitized = sanitized.replace(pattern, "")
        return sanitized

    @staticmethod
    def sanitize_color(color: Optional[str]) -> Optional[str]:
        if not color:
            return None
        allowed_colors = {"红色", "蓝色", "白色", "黑色", "银色", "灰色", "黄色", "绿色", "橙色", "紫色", "粉色"}
        sanitized = SQLSanitizer.sanitize_string(color)
        if sanitized in allowed_colors:
            return sanitized
        return None

    @staticmethod
    def sanitize_time_value(value: Any) -> Optional[float]:
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
