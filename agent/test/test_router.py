import os
import sys
import unittest
from pathlib import Path

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.store.memory import InMemoryStore

AGENT_DIR = Path(__file__).resolve().parents[1]
if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))

from node.tool_router_node import create_tool_router_node, route_by_tool_choice
from node.types import AgentState

ROUTER_TEST_CASES = {
    "hybrid_location": "Where is the blue car in the parking lot",
    "sql_no_location": "A person enters the frame",
    "parallel_mode": "Parallel test question",
}


def _print_current_node(test_name: str, final_state) -> None:
    route = final_state.values.get("route", "none")
    final_answer = final_state.values.get("final_answer", "none")
    mode = final_state.values.get("tool_choice", {}).get("mode", "none")
    print(f"[{test_name}] mode={mode}, current_node={final_answer}, route={route}")


class _FakeStructuredLLM:
    def __init__(self, payload):
        self.payload = payload

    def invoke(self, messages, config=None):
        del messages, config
        return self.payload


class _FakeLLM:
    def __init__(self, payload):
        self.payload = payload

    def with_structured_output(self, schema):
        del schema
        return _FakeStructuredLLM(self.payload)


def _build_router_test_graph(fake_llm):
    router_node = create_tool_router_node(llm=fake_llm)

    def hybrid_search_node(state, config, store):
        del config, store
        return {"route": "hybrid_search_node", "tool_choice": state.get("tool_choice", {})}

    def pure_sql_node(state, config, store):
        del config, store
        return {"route": "pure_sql_node", "tool_choice": state.get("tool_choice", {})}

    def video_vect_node(state, config, store):
        del config, store
        return {"route": "video_vect_node", "tool_choice": state.get("tool_choice", {})}

    def parallel_search_node(state, config, store):
        del config, store
        return {"route": "parallel_search_node", "tool_choice": state.get("tool_choice", {})}

    def final_answer_node(state, config, store):
        del config, store
        return {"final_answer": state.get("route", "none")}

    builder = StateGraph(AgentState)
    builder.add_node("tool_router", router_node)
    builder.add_node("hybrid_search_node", hybrid_search_node)
    builder.add_node("pure_sql_node", pure_sql_node)
    builder.add_node("video_vect_node", video_vect_node)
    builder.add_node("parallel_search_node", parallel_search_node)
    builder.add_node("final_answer_node", final_answer_node)

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
    builder.add_edge("hybrid_search_node", "final_answer_node")
    builder.add_edge("pure_sql_node", "final_answer_node")
    builder.add_edge("video_vect_node", "final_answer_node")
    builder.add_edge("parallel_search_node", "final_answer_node")
    builder.add_edge("final_answer_node", END)

    return builder.compile(checkpointer=MemorySaver(), store=InMemoryStore())


class TestRouterWithGraph(unittest.TestCase):
    def setUp(self):
        self.env_backup = {
            "TOOL_ROUTER_MODE_WITH_LOCATION": os.getenv("TOOL_ROUTER_MODE_WITH_LOCATION"),
            "TOOL_ROUTER_MODE_WITHOUT_LOCATION": os.getenv("TOOL_ROUTER_MODE_WITHOUT_LOCATION"),
            "TOOL_ROUTER_FORCE_PARALLEL": os.getenv("TOOL_ROUTER_FORCE_PARALLEL"),
        }
        os.environ["TOOL_ROUTER_MODE_WITH_LOCATION"] = "hybrid_search"
        os.environ["TOOL_ROUTER_MODE_WITHOUT_LOCATION"] = "pure_sql"
        os.environ.pop("TOOL_ROUTER_FORCE_PARALLEL", None)

    def tearDown(self):
        for key, value in self.env_backup.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def test_router_goes_hybrid_when_location_detected(self):
        llm = _FakeLLM(
            {
                "object": ["car"],
                "color": ["blue"],
                "location": ["parking lot"],
                "event": "Blue car enters the parking lot",
                "confidence": 0.9,
            }
        )
        graph = _build_router_test_graph(llm)
        config = {"configurable": {"thread_id": "router-hybrid"}}
        query = ROUTER_TEST_CASES["hybrid_location"]
        list(graph.stream({"messages": [HumanMessage(content=query)]}, config, stream_mode="values"))
        final_state = graph.get_state(config)
        _print_current_node("hybrid", final_state)
        self.assertEqual(final_state.values.get("final_answer"), "hybrid_search_node")

    def test_router_goes_sql_when_location_missing(self):
        llm = _FakeLLM(
            {
                "object": ["truck"],
                "color": ["red"],
                "location": [],
                "event": "Red truck appears",
                "confidence": 0.87,
            }
        )
        graph = _build_router_test_graph(llm)
        config = {"configurable": {"thread_id": "router-sql"}}
        query = ROUTER_TEST_CASES["sql_no_location"]
        list(graph.stream({"messages": [HumanMessage(content=query)]}, config, stream_mode="values"))
        final_state = graph.get_state(config)
        _print_current_node("sql", final_state)
        self.assertEqual(final_state.values.get("final_answer"), "pure_sql_node")

    def test_router_parallel_routes_parallel_node(self):
        os.environ["TOOL_ROUTER_FORCE_PARALLEL"] = "true"
        llm = _FakeLLM(
            {
                "object": ["car"],
                "color": ["blue"],
                "location": ["parking lot"],
                "event": "Blue car enters the parking lot",
                "confidence": 0.95,
            }
        )
        graph = _build_router_test_graph(llm)
        config = {"configurable": {"thread_id": "router-parallel"}}
        query = ROUTER_TEST_CASES["parallel_mode"]
        list(graph.stream({"messages": [HumanMessage(content=query)]}, config, stream_mode="values"))
        final_state = graph.get_state(config)
        _print_current_node("parallel", final_state)
        self.assertEqual(final_state.values.get("final_answer"), "parallel_search_node")
        self.assertEqual(final_state.values.get("tool_choice", {}).get("mode"), "parallel")


if __name__ == "__main__":
    unittest.main()
