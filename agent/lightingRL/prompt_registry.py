from typing import Any


SELF_QUERY_SYSTEM_PROMPT_KEY = "rewrite.self_query.system"
SELF_QUERY_USER_PROMPT_KEY = "rewrite.self_query.user"


_PROMPTS: dict[str, str] = {
    SELF_QUERY_SYSTEM_PROMPT_KEY: (
        "You rewrite user queries for retrieval. Preserve meaning, keep constraints, "
        "and respond with JSON that matches the requested schema."
    ),
    SELF_QUERY_USER_PROMPT_KEY: (
        "Original query:\n{raw_query}\n\n"
        "Rewrite this query conservatively for retrieval while preserving the user's intent."
    ),
}


def get_prompt_template(prompt_key: str) -> str:
    return _PROMPTS.get(prompt_key, "")


def render_prompt(prompt_key: str, **kwargs: Any) -> str:
    template = get_prompt_template(prompt_key)
    try:
        return template.format(**kwargs)
    except Exception:
        return template
