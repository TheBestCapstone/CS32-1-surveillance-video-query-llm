import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.DEBUG)
sys.path.insert(0, str(Path(__file__).parent / "agent"))

from sub_agents.pure_sql_agent import run_pure_sql_sub_agent
from graph import build_llm, load_env

load_env()
llm = build_llm()

query = "停车场边缘步行区有没有白色车辆长时间静止？"
print(f"Testing Query: {query}")
summary, rows = run_pure_sql_sub_agent(query, llm)
print("\n--- Final Summary ---")
print(summary)
print("\n--- Final Rows ---")
print(rows)
