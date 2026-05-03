from typing import Any


SELF_QUERY_SYSTEM_PROMPT_KEY = "rewrite.self_query.system"
SELF_QUERY_USER_PROMPT_KEY = "rewrite.self_query.user"


_PROMPTS: dict[str, str] = {
    SELF_QUERY_SYSTEM_PROMPT_KEY: (
        "You rewrite user queries for retrieval. Preserve meaning, keep constraints, "
        "and respond with JSON that matches the requested schema.\n\n"
        "For the 'expansion_terms' field: if the query uses abstract or transformed language "
        "(e.g. 'rectangular container' instead of 'box', 'logistics operation' instead of 'carrying'), "
        "generate 3-5 concrete, observable alternative phrasings that would appear directly in "
        "video annotation text. Use simple nouns and verbs. Leave empty if the query is already "
        "concrete enough.\n\n"
        "SCENE ATTRIBUTE VOCABULARY:\n"
        "{scene_vocab_list}\n\n"
        "For the 'scene_constraints' field: from the vocabulary above, select ONLY the attributes "
        "that are clearly implied by the query. weight=0.9 for direct mention, 0.7 for strong "
        "inference, 0.5 for weak inference. Leave empty array if no attributes are relevant."
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
