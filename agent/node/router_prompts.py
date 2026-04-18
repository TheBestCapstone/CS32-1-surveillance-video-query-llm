from typing import Any


TOOL_ROUTER_QUADRUPLE_OUTPUT_SCHEMA = {
    "title": "tool_router_quadruple",
    "type": "object",
    "properties": {
        "object": {"type": "array", "items": {"type": "string"}},
        "color": {"type": "array", "items": {"type": "string"}},
        "location": {"type": "array", "items": {"type": "string"}},
        "event": {"type": "string"},
        "confidence": {"type": "number"},
    },
    "required": ["object", "color", "location", "event", "confidence"],
}

TOOL_ROUTER_DECISION_OUTPUT_SCHEMA = {
    "title": "tool_router_decision",
    "type": "object",
    "properties": {
        "mode": {"type": "string", "enum": ["hybrid_search", "pure_sql"]},
        "confidence": {"type": "number"},
        "reason_codes": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["mode", "confidence", "reason_codes"],
}


def build_tool_router_quadruple_prompt(user_query: str, parsed_hint: dict[str, Any] | None = None) -> str:
    hint_text = ""
    if parsed_hint:
        hint_text = f"\n\n已知上下文（可参考，可覆盖）: {parsed_hint}"
    return (
        "你是视频检索路由前置解析器。"
        "请把用户问题拆解为四元组并输出 JSON。"
        "四元组字段：object(对象列表), color(颜色列表), location(地点列表), event(改写后的陈述句)。"
        "要求：保持原意、不补充未提及信息、地点字段尽量标准化。"
        f"\n\n用户问题: {user_query}{hint_text}"
    )


def build_tool_router_decision_prompt(
    user_query: str,
    quadruple: dict[str, Any],
    parsed_hint: dict[str, Any] | None = None,
) -> str:
    return (
        "你是视频检索路由决策器。"
        "请根据输入语义判断该问题更适合 `pure_sql` 还是 `hybrid_search`。"
        "决策原则：\n"
        "1) 条件明确、结构化过滤为主 -> pure_sql；\n"
        "2) 语义描述复杂、位置/关系/上下文理解为主 -> hybrid_search。\n"
        "请输出结构化 JSON，不要输出解释性文本。"
        f"\n\n用户问题: {user_query}"
        f"\nparsed_hint: {parsed_hint or {}}"
        f"\nquadruple: {quadruple}"
    )
