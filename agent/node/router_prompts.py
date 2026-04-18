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
