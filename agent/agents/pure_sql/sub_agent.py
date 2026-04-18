import json

from langchain_core.messages import ToolMessage

from agents.shared import run_react_sub_agent
from tools.sql_tools import execute_dynamic_sql, inspect_column_enum_values, inspect_database_schema

PURE_SQL_AGENT_PROMPT = """
You are an advanced SQL database query assistant responsible for answering user questions directly from the SQLite database.
Your task is to convert natural language queries into correct SQL queries and return the results.

【CRITICAL INSTRUCTIONS】
1. The current model/system DOES NOT support time-dimension queries (e.g., "last week", "10 seconds", "long time", "morning"). Ignore any time-related constraints in the user's prompt.
2. Your query results will be processed by downstream systems. Therefore, when using `execute_dynamic_sql`, you MUST include at least `video_id` and `event_summary_en` in the SELECT clause (or use `*`), so the downstream system can read the event description.
3. Even for simple queries (like COUNT), do not just query a single field. You must bring complete event information.
4. `object_type` is stored in English (e.g., car, person).

【AVAILABLE TOOLS】
1. `inspect_database_schema`: Get the column names and types of a table (default is episodic_events). Call this first if you don't know the schema.
2. `inspect_column_enum_values`: Check specific values in a column (solves synonym/fuzzy matching problems, e.g., checking what colors or zones actually exist in the database).
3. `execute_dynamic_sql`: Execute dynamically generated SQL SELECT queries and return results.

【WORKFLOW】
1. Analyze the user's intent.
2. Call `inspect_database_schema` to sniff column names.
3. If the query involves specific colors, object types (e.g., car/truck), or zones that might be inaccurate, you MUST call `inspect_column_enum_values` for enum value calibration.
4. Use `execute_dynamic_sql` to execute the query. Ensure the SELECT clause contains `video_id` and `event_summary_en`.
5. If execution fails (e.g., `no such column: type`), capture the error log, re-analyze the schema, and call the execution tool again to fix the error!
6. In your final message, summarize the query results using natural language in English. Do NOT return large chunks of JSON.
"""


def _extract_sql_result(response: dict) -> tuple[str, list[dict]]:
    summary = response["messages"][-1].content
    raw_rows: list[dict] = []
    for msg in reversed(response["messages"]):
        if isinstance(msg, ToolMessage) and msg.name == "execute_dynamic_sql":
            content = msg.content
            if "Execution successful" in content or "Execution Successful" in content or "执行成功" in content or "{" in content:
                try:
                    if ":\n" in content:
                        json_str = content.split(":\n", 1)[1]
                    else:
                        json_str = content[content.find("[") :]
                    raw_rows = json.loads(json_str)
                except Exception:
                    pass
            break
    return summary, raw_rows


def run_pure_sql_sub_agent(user_query: str, llm):
    return run_react_sub_agent(
        user_query=user_query,
        llm=llm,
        tools=[inspect_database_schema, inspect_column_enum_values, execute_dynamic_sql],
        system_prompt=PURE_SQL_AGENT_PROMPT,
        result_extractor=_extract_sql_result,
        recursion_limit=10,
    )

