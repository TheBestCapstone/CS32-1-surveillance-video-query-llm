import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "agent"))
from sub_agents.pure_sql_agent import run_pure_sql_sub_agent
from graph import build_llm, load_env
load_env()
llm = build_llm()
summary, rows = run_pure_sql_sub_agent("停车场里那辆蓝色轿车是什么时候进入画面的？（已移除颜色条件）（已移除地点条件）（已放宽过滤条件）", llm)
print("Summary:", summary)
print("Rows:", rows)
