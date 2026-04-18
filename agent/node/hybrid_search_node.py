from typing import Any
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.store.base import BaseStore

from agents.hybrid_search.sub_agent import run_hybrid_sub_agent
from .retrieval_contracts import build_routing_metrics, build_search_config, normalize_hybrid_rows
from .types import AgentState, InputValidator
import time

def create_hybrid_search_node(llm=None, **kwargs):
    def hybrid_search_node(state: AgentState, config: RunnableConfig, store: BaseStore) -> dict[str, Any]:
        del config, store
        
        user_query = InputValidator.resolve_active_query(state)
        
        # If it's a reflection retry, use optimized query
        reflection_result = state.get("reflection_result", {})
        if reflection_result.get("needs_retry", False) and state.get("retry_count", 0) > 0:
            user_query = state.get("optimized_query", user_query)
            
        current_retry = int(state.get("retry_count", 0) or 0)
        
        start = time.perf_counter()
        
        try:
            summary, raw_rows = run_hybrid_sub_agent(user_query, llm)
            duration = time.perf_counter() - start
            normalized_rows = normalize_hybrid_rows(raw_rows)
            search_config = build_search_config(state.get("search_config", {}))
            
            return {
                "hybrid_result": normalized_rows,
                "rerank_result": normalized_rows,
                "reflection_result": {"feedback": "Retrieval successful", "quality_score": 1.0, "needs_retry": False},
                "tool_error": None,
                "retry_count": current_retry,
                "current_node": "hybrid_search_node",
                "search_explain": summary,
                "routing_metrics": build_routing_metrics(
                    execution_mode="legacy_router",
                    label="semantic",
                    query=user_query,
                    sql_rows_count=0,
                    hybrid_rows_count=len(normalized_rows),
                ),
                "search_config": search_config,
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
