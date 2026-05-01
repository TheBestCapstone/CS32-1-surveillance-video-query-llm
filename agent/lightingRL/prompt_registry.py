from __future__ import annotations

from typing import Any, Mapping


SELF_QUERY_SYSTEM_PROMPT_KEY = "self_query.system"
SELF_QUERY_USER_PROMPT_KEY = "self_query.user"
QUERY_CLASSIFICATION_SYSTEM_PROMPT_KEY = "query_classification.system"
QUERY_CLASSIFICATION_USER_PROMPT_KEY = "query_classification.user"
SUMMARY_SYSTEM_PROMPT_KEY = "summary.system"
SUMMARY_USER_PROMPT_KEY = "summary.user"


DEFAULT_PROMPT_TEMPLATES: dict[str, str] = {
    SELF_QUERY_SYSTEM_PROMPT_KEY: "Return valid JSON only.",
    SELF_QUERY_USER_PROMPT_KEY: (
        "You are a self-query planner for a basketball video retrieval agent. "
        "Analyze the user's request without answering it. "
        "If the query is already clear, keep the rewrite very close to the original wording. "
        "Do not broaden the scope, and do not replace important domain terms with loose synonyms. "
        "Preserve object/color/location/action phrases exactly whenever possible. "
        "Produce a retrieval-friendly rewrite that preserves the original meaning, "
        "highlights constraints, clarifies the user's real need, and gives a short high-level reasoning summary. "
        "Do not invent facts. Keep the rewritten query concise and faithful to the user intent."
        "\n\nUser query: {raw_query}"
    ),
    QUERY_CLASSIFICATION_SYSTEM_PROMPT_KEY: "严格输出 JSON。",
    QUERY_CLASSIFICATION_USER_PROMPT_KEY: (
        "你是查询分类器。请判断用户问题属于 structured / semantic / mixed。"
        "structured: 明确字段过滤、存在性/计数/列表查询为主；"
        "semantic: 语义理解、相似检索、关系描述为主；"
        "mixed: 两者都明显存在。"
        "判定优先级：若问题主要是是否存在/列出/查某类目标，即使语句是自然语言，也优先 structured。"
        "只有当问题核心依赖语义关系（near/around/similar/行为过程）时才判 semantic。"
        "示例："
        "1) Did you see any person in the database? -> structured；"
        "2) Show me dark persons. -> structured；"
        "3) Find a person near the left bleachers. -> semantic。"
        "仅输出结构化 JSON。"
        "\n\n用户问题: {query}"
    ),
    SUMMARY_SYSTEM_PROMPT_KEY: "Return only the final English summary text.",
    SUMMARY_USER_PROMPT_KEY: (
        "You are the final response summarizer for a basketball retrieval assistant. "
        "Write a concise, friendly, natural English summary for a native speaker. "
        "Be accurate, grounded in the provided results, and easy to read. "
        "Do not mention internal routing, SQL, hybrid retrieval, or chain-of-thought. "
        "Keep the answer under 90 words. Do not include a sources section; sources will be appended separately."
        "\n\nOriginal user query: {original_query}"
        "\nRewritten retrieval query: {rewritten_query}"
        "\nRetrieved result count: {row_count}"
        "\nTop results: {top_results}"
        "\nDraft answer: {raw_answer}"
    ),
}


def get_prompt_template(
    key: str,
    overrides: Mapping[str, str] | None = None,
) -> str:
    if overrides and key in overrides:
        return overrides[key]
    if key not in DEFAULT_PROMPT_TEMPLATES:
        raise KeyError(f"Unknown prompt key: {key}")
    return DEFAULT_PROMPT_TEMPLATES[key]


def render_prompt(
    key: str,
    *,
    overrides: Mapping[str, str] | None = None,
    **kwargs: Any,
) -> str:
    template = get_prompt_template(key, overrides=overrides)
    return template.format(**kwargs)
