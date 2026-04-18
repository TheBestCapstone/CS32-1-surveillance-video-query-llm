from typing import Any
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.store.base import BaseStore
from .types import AgentState, InputValidator
from sub_agents.hybrid_agent import run_hybrid_sub_agent
import time

def create_hybrid_search_node(llm=None, **kwargs):
    def hybrid_search_node(state: AgentState, config: RunnableConfig, store: BaseStore) -> dict[str, Any]:
        del config, store
        
        # Extract original user query
        user_query = InputValidator.extract_latest_query(state)
        
        # If it's a reflection retry, use optimized query
        reflection_result = state.get("reflection_result", {})
        if reflection_result.get("needs_retry", False) and state.get("retry_count", 0) > 0:
            user_query = state.get("optimized_query", user_query)
            
        current_retry = int(state.get("retry_count", 0) or 0)
        
        start = time.perf_counter()
        
        try:
            summary, raw_rows = run_hybrid_sub_agent(user_query, llm)
            duration = time.perf_counter() - start
            
            return {
                "hybrid_result": raw_rows,
                "rerank_result": raw_rows,
                "reflection_result": {"feedback": "Retrieval successful", "quality_score": 1.0, "needs_retry": False},
                "tool_error": None,
                "retry_count": current_retry,
                "current_node": "hybrid_search_node",
                "search_explain": summary,
                "messages": [AIMessage(content=f"Hybrid Search Sub-Agent complete. Summary:\n{summary}")],
            }
        except Exception as exc:
            return {
                "hybrid_result": [],
                "rerank_result": [],
                "reflection_result": {"feedback": f"Sub-Agent execution failed: {exc}", "quality_score": 0.0, "needs_retry": True},
                "tool_error": f"Hybrid Search Sub-Agent failed: {exc}",
                "retry_count": current_retry,
                "current_node": "hybrid_search_node",
                "messages": [AIMessage(content=f"Hybrid Search Sub-Agent failed: {exc}")],
            }

    return hybrid_search_node
