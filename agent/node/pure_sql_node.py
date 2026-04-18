from typing import Any
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.store.base import BaseStore
from .types import AgentState, InputValidator
from sub_agents.pure_sql_agent import run_pure_sql_sub_agent
import time

def create_pure_sql_node(llm=None, **kwargs):
    def pure_sql_node(state: AgentState, config: RunnableConfig, store: BaseStore) -> dict[str, Any]:
        del config, store
        
        # Extract original user query
        user_query = InputValidator.extract_latest_query(state)
        
        # If it's a reflection retry, use optimized query
        reflection_result = state.get("reflection_result", {})
        if reflection_result.get("needs_retry", False) and state.get("retry_count", 0) > 0:
            user_query = state.get("optimized_query", user_query)
            
        current_retry = int(state.get("retry_count", 0) or 0)
        
        start = time.perf_counter()
        print(f"[DEBUG] pure_sql_node user_query: {user_query}")
        try:
            summary, raw_rows = run_pure_sql_sub_agent(user_query, llm)
            duration = time.perf_counter() - start
            
            return {
                "sql_result": raw_rows,
                "rerank_result": raw_rows,
                "reflection_result": {"feedback": "Retrieval successful", "quality_score": 1.0, "needs_retry": False},
                "tool_error": None,
                "retry_count": current_retry,
                "current_node": "pure_sql_node",
                "sql_debug": {
                    "duration": duration,
                    "agent_summary": summary
                },
                "messages": [AIMessage(content=f"SQL Sub-Agent retrieval complete. Summary:\n{summary}")],
            }
        except Exception as exc:
            return {
                "sql_result": [],
                "rerank_result": [],
                "reflection_result": {"feedback": f"Sub-Agent execution failed: {exc}", "quality_score": 0.0, "needs_retry": True},
                "tool_error": f"Pure SQL Sub-Agent retrieval failed: {exc}",
                "retry_count": current_retry,
                "current_node": "pure_sql_node",
                "sql_debug": {"last_error": str(exc)},
                "messages": [AIMessage(content=f"Pure SQL Sub-Agent retrieval failed: {exc}")],
            }

    return pure_sql_node
