import sys
import unittest
from pathlib import Path

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.store.memory import InMemoryStore

AGENT_DIR = Path(__file__).resolve().parents[1]
if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))

from node.answer_node import final_answer_node
from node.hybrid_search_node import create_hybrid_search_node
from node.pure_sql_node import create_pure_sql_node
from node.reflection_node import create_reflection_node, route_after_reflection
from node.tool_router_node import create_tool_router_node, route_by_tool_choice
from node.types import AgentState


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


def _build_graph_for_test(llm):
    builder = StateGraph(AgentState)
    builder.add_node("tool_router", create_tool_router_node(llm=llm))
    builder.add_node("hybrid_search_node", create_hybrid_search_node())
    builder.add_node("pure_sql_node", create_pure_sql_node())
    builder.add_node("reflection_node", create_reflection_node(max_retries=2))
    builder.add_node("final_answer_node", final_answer_node)
    builder.add_edge(START, "tool_router")
    builder.add_conditional_edges(
        "tool_router",
        route_by_tool_choice,
        {"hybrid_search_node": "hybrid_search_node", "pure_sql_node": "pure_sql_node"},
    )
    builder.add_edge("hybrid_search_node", "reflection_node")
    builder.add_edge("pure_sql_node", "reflection_node")
    builder.add_conditional_edges(
        "reflection_node",
        route_after_reflection,
        {"tool_router": "tool_router", "final_answer_node": "final_answer_node"},
    )
    builder.add_edge("final_answer_node", END)
    return builder.compile(checkpointer=MemorySaver(), store=InMemoryStore())


class TestGraphIntegration(unittest.TestCase):
    def test_graph_stable_without_parallel_video_vect(self):
        llm = _FakeLLM(
            {
                "object": ["car"],
                "color": ["blue"],
                "location": ["parking lot"],
                "event": "Blue car enters the parking lot",
                "confidence": 0.95,
            }
        )
        graph = _build_graph_for_test(llm)
        config = {"configurable": {"thread_id": "integration-1"}}
        list(graph.stream({"messages": [{"type": "human", "content": "Where is the blue car in the parking lot"}]}, config, stream_mode="values"))
        out = graph.get_state(config).values
        self.assertIn(out.get("tool_choice", {}).get("mode"), {"hybrid_search", "pure_sql"})
        self.assertNotIn(out.get("tool_choice", {}).get("mode"), {"parallel", "video_vect"})


if __name__ == "__main__":
    unittest.main()
