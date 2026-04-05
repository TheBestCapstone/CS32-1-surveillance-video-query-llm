import json
import os
import sys
import time
import unittest
from pathlib import Path

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.store.memory import InMemoryStore

AGENT_DIR = Path(__file__).resolve().parents[1]
if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))

from node.hybrid_search_node import create_hybrid_search_node
from node.tool_router_node import create_tool_router_node, route_by_tool_choice
from node.types import AgentState


def _build_hybrid_graph():
    hybrid_node = create_hybrid_search_node()

    builder = StateGraph(AgentState)
    builder.add_node("hybrid_search_node", hybrid_node)
    builder.add_edge(START, "hybrid_search_node")
    builder.add_edge("hybrid_search_node", END)
    return builder.compile(checkpointer=MemorySaver(), store=InMemoryStore())


def _load_env() -> None:
    env_file = AGENT_DIR.parent / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _build_real_llm() -> ChatOpenAI:
    _load_env()
    return ChatOpenAI(
        model_name="qwen3-max",
        temperature=0.0,
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        base_url=os.getenv("DASHSCOPE_URL"),
    )


def _build_router_to_hybrid_graph(llm):
    router_node = create_tool_router_node(llm=llm)
    hybrid_node = create_hybrid_search_node()

    def passthrough(state: AgentState, config, store):
        del config, store
        return state

    builder = StateGraph(AgentState)
    builder.add_node("tool_router", router_node)
    builder.add_node("hybrid_search_node", hybrid_node)
    builder.add_node("pure_sql_node", passthrough)
    builder.add_node("video_vect_node", passthrough)
    builder.add_node("parallel_search_node", passthrough)
    builder.add_edge(START, "tool_router")
    builder.add_conditional_edges(
        "tool_router",
        route_by_tool_choice,
        {
            "hybrid_search_node": "hybrid_search_node",
            "pure_sql_node": "pure_sql_node",
            "video_vect_node": "video_vect_node",
            "parallel_search_node": "parallel_search_node",
        },
    )
    builder.add_edge("hybrid_search_node", END)
    builder.add_edge("pure_sql_node", END)
    builder.add_edge("video_vect_node", END)
    builder.add_edge("parallel_search_node", END)
    return builder.compile(checkpointer=MemorySaver(), store=InMemoryStore())


class TestHybridNode(unittest.TestCase):
    @staticmethod
    def _state_base() -> dict:
        return {
            "user_query": "查询车辆事件",
            "tool_choice": {"mode": "hybrid_search", "hybrid_needed": True, "sql_needed": False, "video_vect_needed": False, "sub_queries": {"hybrid": {}}},
            "parsed_question": {"event": "车辆进入画面", "color": "", "location": "", "object": "车辆", "time": None, "move": None},
            "query_quadruple": {"object": ["车辆"], "color": [], "location": [], "event": "车辆进入画面", "confidence": 0.9, "source": "test"},
            "meta_list": [],
            "event_list": [],
            "retry_count": 0,
            "search_config": {"candidate_limit": 80, "top_k_per_event": 20, "rerank_top_k": 5},
            "sql_plan": {"table": "episodic_events"},
            "metrics": {},
        }

    def _run_graph(self, state: dict, thread_id: str):
        graph = _build_hybrid_graph()
        config = {"configurable": {"thread_id": thread_id}}
        list(graph.stream(state, config, stream_mode="values"))
        return graph.get_state(config).values

    @staticmethod
    def _print_case(case_name: str, out: dict) -> None:
        print(
            f"[{case_name}] node={out.get('current_node')}, "
            f"mode={out.get('tool_choice', {}).get('mode')}, "
            f"hybrid_rows={len(out.get('hybrid_result', []))}, "
            f"rerank_rows={len(out.get('rerank_result', []))}, "
            f"error={out.get('tool_error')}"
        )

    def _write_perf(self, latencies: list[float], recall_hit: int, total: int) -> None:
        baseline_file = AGENT_DIR / "test" / "perf_baseline.json"
        data = {}
        if baseline_file.exists():
            data = json.loads(baseline_file.read_text(encoding="utf-8"))
        p95 = sorted(latencies)[max(0, int(len(latencies) * 0.95) - 1)] if latencies else 0.0
        data["hybrid_p95_ms"] = round(p95, 3)
        data["hybrid_recall_rate"] = round((recall_hit / total) if total else 0.0, 3)
        baseline_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def test_state_no_loss_after_hybrid(self):
        state = self._state_base()
        out = self._run_graph(state, "hybrid-state")
        for key in ["tool_choice", "parsed_question", "meta_list", "event_list", "query_quadruple", "search_config", "sql_plan"]:
            self.assertIn(key, out)

    def test_single_table_returns_rows(self):
        state = self._state_base()
        state["meta_list"] = [{"field": "object_type", "op": "contains", "value": "car"}]
        out = self._run_graph(state, "hybrid-single")
        self._print_case("single_table", out)
        self.assertGreaterEqual(len(out.get("hybrid_result", [])), 1)

    def test_multi_table_returns_rows(self):
        state = self._state_base()
        state["hybrid_table_names"] = ["episodic_events", "episodic_events"]
        state["meta_list"] = [{"field": "object_type", "op": "contains", "value": "car"}]
        out = self._run_graph(state, "hybrid-multi")
        self._print_case("multi_table", out)
        self.assertGreaterEqual(len(out.get("hybrid_result", [])), 1)

    def test_empty_result_and_perf_baseline(self):
        strict_state = self._state_base()
        strict_state["meta_list"] = [{"field": "object_type", "op": "==", "value": "this_type_should_not_exist"}]
        strict_state["search_config"] = {"candidate_limit": 80, "top_k_per_event": 20, "rerank_top_k": 5}
        normal_state = self._state_base()
        normal_state["meta_list"] = [{"field": "object_type", "op": "contains", "value": "car"}]
        latencies: list[float] = []
        recall_hit = 0
        total = 6
        out = {}
        for i in range(total):
            state = strict_state if i % 2 == 0 else normal_state
            start = time.perf_counter()
            out = self._run_graph(state, f"hybrid-perf-{i}")
            latencies.append((time.perf_counter() - start) * 1000)
            if out.get("hybrid_result"):
                recall_hit += 1
        self.assertIn("hybrid_result", out)
        self._write_perf(latencies, recall_hit, total)

    def test_exception_input(self):
        state = self._state_base()
        state["meta_list"] = [{"field": "bad-field;", "op": "==", "value": "x"}]
        out = self._run_graph(state, "hybrid-exception")
        self._print_case("exception_input", out)
        self.assertIsNotNone(out.get("tool_error"))

    def test_router_then_hybrid_returns_real_rows(self):
        if not os.getenv("DASHSCOPE_API_KEY"):
            _load_env()
        if not os.getenv("DASHSCOPE_API_KEY"):
            self.skipTest("DASHSCOPE_API_KEY 未配置，跳过真实LLM测试")
        env_backup = {
            "TOOL_ROUTER_MODE_WITH_LOCATION": os.getenv("TOOL_ROUTER_MODE_WITH_LOCATION"),
            "TOOL_ROUTER_MODE_WITHOUT_LOCATION": os.getenv("TOOL_ROUTER_MODE_WITHOUT_LOCATION"),
            "TOOL_ROUTER_FORCE_PARALLEL": os.getenv("TOOL_ROUTER_FORCE_PARALLEL"),
        }
        os.environ["TOOL_ROUTER_MODE_WITH_LOCATION"] = "hybrid_search"
        os.environ["TOOL_ROUTER_MODE_WITHOUT_LOCATION"] = "pure_sql"
        os.environ.pop("TOOL_ROUTER_FORCE_PARALLEL", None)
        try:
            graph = _build_router_to_hybrid_graph(_build_real_llm())
            config = {"configurable": {"thread_id": "router-to-hybrid"}}
            initial_state = {
                "messages": [HumanMessage(content="停车场里的车辆进入情况")],
                "meta_list": [{"field": "object_type", "op": "contains", "value": "car"}],
            }
            list(graph.stream(initial_state, config, stream_mode="values"))
            out = graph.get_state(config).values
            self._print_case("router_to_hybrid", out)
            self.assertEqual(out.get("tool_choice", {}).get("mode"), "hybrid_search")
            self.assertGreaterEqual(len(out.get("hybrid_result", [])), 1)
            self.assertEqual(out.get("current_node"), "hybrid_search_node")
        finally:
            for key, value in env_backup.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value


MANUAL_CASE = {
    "thread_id": "manual-router-to-hybrid",
    "query": "停车场里的车辆进入情况",
    "location": ["停车场"],
    "meta_list": [{"field": "object_type", "op": "contains", "value": "car"}],
    "search_config": {"candidate_limit": 80, "top_k_per_event": 20, "rerank_top_k": 5},
}


def run_manual_case() -> None:
    if not os.getenv("DASHSCOPE_API_KEY"):
        _load_env()
    if not os.getenv("DASHSCOPE_API_KEY"):
        raise RuntimeError("未配置 DASHSCOPE_API_KEY，无法运行真实LLM手工测试")
    env_backup = {
        "TOOL_ROUTER_MODE_WITH_LOCATION": os.getenv("TOOL_ROUTER_MODE_WITH_LOCATION"),
        "TOOL_ROUTER_MODE_WITHOUT_LOCATION": os.getenv("TOOL_ROUTER_MODE_WITHOUT_LOCATION"),
        "TOOL_ROUTER_FORCE_PARALLEL": os.getenv("TOOL_ROUTER_FORCE_PARALLEL"),
    }
    os.environ["TOOL_ROUTER_MODE_WITH_LOCATION"] = "hybrid_search"
    os.environ["TOOL_ROUTER_MODE_WITHOUT_LOCATION"] = "pure_sql"
    os.environ.pop("TOOL_ROUTER_FORCE_PARALLEL", None)
    try:
        graph = _build_router_to_hybrid_graph(_build_real_llm())
        query = MANUAL_CASE["query"]
        if len(sys.argv) > 2 and sys.argv[2].strip():
            query = sys.argv[2].strip()
        else:
            user_input = input(f"请输入测试问题（直接回车使用默认: {query}）: ").strip()
            if user_input:
                query = user_input
        config = {"configurable": {"thread_id": MANUAL_CASE["thread_id"]}}
        initial_state = {
            "messages": [HumanMessage(content=query)],
            "meta_list": MANUAL_CASE["meta_list"],
            "search_config": MANUAL_CASE["search_config"],
        }
        list(graph.stream(initial_state, config, stream_mode="values"))
        out = graph.get_state(config).values
        top5 = out.get("hybrid_result", [])[:5]
        top5_view = [
            {
                "video_id": item.get("video_id"),
                "event_text_cn": item.get("event_text_cn") or item.get("event_summary_cn"),
                "object_type": item.get("object_type"),
                "object_color_cn": item.get("object_color_cn"),
            }
            for item in top5
        ]
        print("[manual_case] query:", query)
        print("[manual_case] current_node:", out.get("current_node"))
        print("[manual_case] mode:", out.get("tool_choice", {}).get("mode"))
        print("[manual_case] hybrid_rows:", len(out.get("hybrid_result", [])))
        print("[manual_case] top1-top5:", top5_view)
        print("[manual_case] thought:", out.get("thought"))
    finally:
        for key, value in env_backup.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


if __name__ == "__main__":
    if "--manual" in sys.argv:
        run_manual_case()
    else:
        unittest.main()
