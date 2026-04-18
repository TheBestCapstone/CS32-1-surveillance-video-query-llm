import json

from langchain_core.messages import ToolMessage

from agents.shared import run_react_sub_agent
from tools.hybrid_tools import dynamic_weighted_vector_search, get_temporal_anchor

HYBRID_SEARCH_AGENT_PROMPT = """
You are an advanced hybrid retrieval assistant responsible for searching complex temporal and semantic events from a video event library.

【AVAILABLE TOOLS】
1. `get_temporal_anchor`: Used to find the time (anchor) when a specific event occurred. For example, "after the red car leaves...", you can first search for "red car leaves".
2. `dynamic_weighted_vector_search`: Used for hybrid retrieval. You can dynamically adjust the weight by setting alpha (0.0~1.0):
   - Strong attributes (e.g., "find a red car"), lower alpha (e.g., 0.2).
   - Strong semantics (e.g., "crazy reversing to dodge"), increase alpha (e.g., 0.8).

【WORKFLOW】
1. Carefully analyze the user query.
2. If there is a temporal dependency ("after/before XX"), first call `get_temporal_anchor` to find the timestamp, then pass the time range and other info to the next step.
3. Evaluate whether the user's intent leans towards "explicit attributes" or "fuzzy semantics", choose an appropriate alpha to call `dynamic_weighted_vector_search`.
4. Finally, summarize the results using natural language in English. Do not output large chunks of JSON.
"""


def _extract_hybrid_result(response: dict) -> tuple[str, list[dict]]:
    summary = response["messages"][-1].content
    raw_rows: list[dict] = []
    for msg in reversed(response["messages"]):
        if isinstance(msg, ToolMessage) and msg.name == "dynamic_weighted_vector_search":
            content = msg.content
            if "Hybrid search successful on Chroma" in content or "混合检索成功" in content:
                try:
                    json_str = content.split(":\n", 1)[1]
                    raw_rows = json.loads(json_str)
                except Exception:
                    pass
            break
    return summary, raw_rows


def run_hybrid_sub_agent(user_query: str, llm):
    return run_react_sub_agent(
        user_query=user_query,
        llm=llm,
        tools=[get_temporal_anchor, dynamic_weighted_vector_search],
        system_prompt=HYBRID_SEARCH_AGENT_PROMPT,
        result_extractor=_extract_hybrid_result,
    )
