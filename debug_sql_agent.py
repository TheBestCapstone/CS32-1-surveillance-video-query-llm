import sys
import logging
from pathlib import Path

# Enable debug logging for langgraph/langchain to see what the agent is actually doing
logging.basicConfig(level=logging.DEBUG)

sys.path.insert(0, str(Path(__file__).parent / "agent"))

from sub_agents.pure_sql_agent import run_pure_sql_sub_agent
from graph import build_llm, load_env

load_env()
llm = build_llm()

# Test case C03: 帮我找一下画面中所有行人的出现时段。
query = "帮我找一下画面中所有行人的出现时段。"
print(f"Testing Query: {query}")
summary, rows = run_pure_sql_sub_agent(query, llm)
print("\n--- Final Summary ---")
print(summary)
print("\n--- Final Rows ---")
print(len(rows))
