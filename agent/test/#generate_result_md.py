import json
import sys
import time
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[2]
AGENT_DIR = ROOT_DIR / "agent"
if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))

from node.hybrid_search_node import create_hybrid_search_node
from node.pure_sql_node import create_pure_sql_node
from node.tool_router_node import create_tool_router_node


class _FakeStructuredLLM:
    def __init__(self, payload: dict[str, Any]):
        self.payload = payload

    def invoke(self, messages, config=None):
        del messages, config
        return self.payload


class _FakeLLM:
    def __init__(self, payload: dict[str, Any]):
        self.payload = payload

    def with_structured_output(self, schema):
        del schema
        return _FakeStructuredLLM(self.payload)


def _json_block(data: Any) -> str:
    return "```json\n" + json.dumps(data, ensure_ascii=False, indent=2) + "\n```\n"


def run() -> Path:
    result_path = ROOT_DIR / "result.md"
    rows: list[str] = []
    rows.append("# Test Result Report\n")
    rows.append(f"- Generated At: `{time.strftime('%Y-%m-%d %H:%M:%S')}`\n")
    rows.append("- Scope: `tool_router -> hybrid/pure_sql` end-to-end process snapshots\n")

    # Case 1: Router -> Hybrid
    query1 = "Where is the blue car in the parking lot"
    router1 = create_tool_router_node(
        llm=_FakeLLM(
            {
                "object": ["car"],
                "color": ["blue"],
                "location": ["parking lot"],
                "event": "Blue car enters the parking lot",
                "confidence": 0.95,
            }
        )
    )
    state1 = router1({"messages": [{"type": "human", "content": query1}]}, {}, None)
    rows.append("\n## Case 1: Router Decision (Hybrid)\n")
    rows.append(f"- Question: `{query1}`\n")
    rows.append(f"- Route Mode: `{state1.get('tool_choice', {}).get('mode')}`\n")
    rows.append("- Parsed Quadruple:\n")
    rows.append(_json_block(state1.get("query_quadruple", {})))
    rows.append("- Generated Meta/Event:\n")
    rows.append(_json_block({"meta_list": state1.get("meta_list", []), "event_list": state1.get("event_list", [])}))

    # Case 2: Hybrid Execution
    hybrid_node = create_hybrid_search_node()
    hybrid_state = dict(state1)
    hybrid_state["meta_list"] = [{"field": "object_type", "op": "contains", "value": "car"}]
    t0 = time.perf_counter()
    hybrid_out = hybrid_node(hybrid_state, {}, None)
    hybrid_ms = round((time.perf_counter() - t0) * 1000, 2)
    top5_hybrid = [
        {
            "video_id": item.get("video_id"),
            "event_text_cn": item.get("event_text_cn") or item.get("event_summary_cn"),
        }
        for item in hybrid_out.get("hybrid_result", [])[:5]
    ]
    rows.append("\n## Case 2: Hybrid Retrieval\n")
    rows.append(f"- Question: `{query1}`\n")
    rows.append(f"- Node: `{hybrid_out.get('current_node')}`\n")
    rows.append(f"- Latency: `{hybrid_ms} ms`\n")
    rows.append(f"- Result Count: `{len(hybrid_out.get('hybrid_result', []))}`\n")
    rows.append("- Top1-Top5:\n")
    rows.append(_json_block(top5_hybrid))
    rows.append("- Thought:\n")
    rows.append(_json_block({"thought": hybrid_out.get("thought")}))

    # Case 3: Router -> SQL
    query2 = "A person enters the frame"
    router2 = create_tool_router_node(
        llm=_FakeLLM(
            {
                "object": ["person"],
                "color": [],
                "location": [],
                "event": "A person enters the frame",
                "confidence": 0.9,
            }
        )
    )
    state2 = router2({"messages": [{"type": "human", "content": query2}]}, {}, None)
    rows.append("\n## Case 3: Router Decision (SQL)\n")
    rows.append(f"- Question: `{query2}`\n")
    rows.append(f"- Route Mode: `{state2.get('tool_choice', {}).get('mode')}`\n")
    rows.append("- Parsed Quadruple:\n")
    rows.append(_json_block(state2.get("query_quadruple", {})))
    rows.append("- Generated Meta/Event:\n")
    rows.append(_json_block({"meta_list": state2.get("meta_list", []), "event_list": state2.get("event_list", [])}))

    # Case 4: SQL Execution
    sql_node = create_pure_sql_node()
    sql_state = dict(state2)
    sql_state["sql_plan"] = {
        "table": "episodic_events",
        "fields": ["event_id", "video_id", "object_type", "start_time", "end_time"],
        "where": [{"field": "object_type", "op": "contains", "value": "person"}],
        "order_by": "start_time ASC",
        "limit": 5,
    }
    t1 = time.perf_counter()
    sql_out = sql_node(sql_state, {}, None)
    sql_ms = round((time.perf_counter() - t1) * 1000, 2)
    top5_sql = [
        {
            "video_id": item.get("video_id"),
            "event_text_cn": item.get("event_summary_cn"),
        }
        for item in sql_out.get("sql_result", [])[:5]
    ]
    rows.append("\n## Case 4: SQL Retrieval\n")
    rows.append(f"- Question: `{query2}`\n")
    rows.append(f"- Node: `{sql_out.get('current_node')}`\n")
    rows.append(f"- Latency: `{sql_ms} ms`\n")
    rows.append(f"- Result Count: `{len(sql_out.get('sql_result', []))}`\n")
    rows.append("- Top1-Top5:\n")
    rows.append(_json_block(top5_sql))
    rows.append("- Thought:\n")
    rows.append(_json_block({"thought": sql_out.get("thought")}))

    result_path.write_text("".join(rows), encoding="utf-8")
    return result_path


if __name__ == "__main__":
    path = run()
    print(path)
