from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from langgraph.prebuilt import create_react_agent
from tools.hybrid_tools import get_temporal_anchor, dynamic_weighted_vector_search
import json

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

def run_hybrid_sub_agent(user_query: str, llm):
    tools = [get_temporal_anchor, dynamic_weighted_vector_search]
    agent = create_react_agent(llm, tools, prompt=SystemMessage(content=HYBRID_SEARCH_AGENT_PROMPT))
    
    messages = [HumanMessage(content=user_query)]
    response = agent.invoke({"messages": messages})
    
    summary = response["messages"][-1].content
    raw_rows = []
    
    for msg in reversed(response["messages"]):
        if isinstance(msg, ToolMessage) and msg.name == "dynamic_weighted_vector_search":
            content = msg.content
            if "混合检索成功" in content:
                try:
                    json_str = content.split(":\n", 1)[1]
                    raw_rows = json.loads(json_str)
                except Exception:
                    pass
            break
            
    return summary, raw_rows

if __name__ == "__main__":
    summary, rows = run_hybrid_sub_agent("那辆红色轿车离开后，又有什么人经过了那个路口？")
    print("Summary:", summary)
    print("Rows:", rows)
