from pathlib import Path
from typing import Any

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.store.base import BaseStore

from tools.py2sql import SQLVideoSearchTool

from .types import AgentState, default_db_path


def create_sql_search_node(db_path: Path | None = None, tool: SQLVideoSearchTool | None = None):
    actual_db_path = db_path or default_db_path()

    def sql_search_node(state: AgentState, config: RunnableConfig, store: BaseStore) -> dict[str, Any]:
        del config, store
        current_retry = int(state.get("retry_count", 0) or 0)
        try:
            search_tool = tool or SQLVideoSearchTool(db_path=actual_db_path)
            sql_rows = search_tool.search(
                metadata_filters=state.get("meta_list", []),
                event_queries=state.get("event_list", []),
                candidate_limit=40,
                top_k_per_event=20,
            )
            return {
                "sql_result": sql_rows,
                "tool_error": None,
                "retry_count": current_retry,
                "messages": [AIMessage(content=f"SQL检索完成，命中 {len(sql_rows)} 条")],
            }
        except Exception as exc:
            return {
                "sql_result": [],
                "tool_error": f"SQL检索失败: {exc}",
                "retry_count": current_retry + 1,
                "messages": [AIMessage(content=f"SQL检索失败: {exc}")],
            }

    return sql_search_node


if __name__ == "__main__":
    class FakeSQLTool:
        def search(self, metadata_filters, event_queries, candidate_limit=40, top_k_per_event=20):
            del metadata_filters, event_queries, candidate_limit, top_k_per_event
            return [{"event_id": 1, "video_id": "demo.mp4", "_distance": 0.2}]

    node = create_sql_search_node(tool=FakeSQLTool())
    out = node({"meta_list": [], "event_list": ["进入"]}, config={}, store=None)
    print(out["messages"][0].content)
