import os
import sys
import unittest
from pathlib import Path

AGENT_DIR = Path(__file__).resolve().parent
if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))

from node.tool_router_node import create_tool_router_node, route_by_tool_choice


class _FakeStructuredLLM:
    def __init__(self, payload):
        self.payload = payload

    def invoke(self, messages, config=None):
        del messages, config
        return self.payload


class _FakeLLM:
    def __init__(self, payload=None, should_fail=False):
        self.payload = payload or {
            "object": ["car"],
            "color": ["red"],
            "location": ["parking lot"],
            "event": "Red car enters the parking lot",
            "confidence": 0.91,
        }
        self.should_fail = should_fail

    def with_structured_output(self, schema):
        del schema
        if self.should_fail:
            raise RuntimeError("llm failed")
        return _FakeStructuredLLM(self.payload)


class TestToolRouterNode(unittest.TestCase):
    def setUp(self):
        self._env_backup = {
            "TOOL_ROUTER_MODE_WITH_LOCATION": os.getenv("TOOL_ROUTER_MODE_WITH_LOCATION"),
            "TOOL_ROUTER_MODE_WITHOUT_LOCATION": os.getenv("TOOL_ROUTER_MODE_WITHOUT_LOCATION"),
        }
        os.environ["TOOL_ROUTER_MODE_WITH_LOCATION"] = "hybrid_search"
        os.environ["TOOL_ROUTER_MODE_WITHOUT_LOCATION"] = "pure_sql"

    def tearDown(self):
        for key, value in self._env_backup.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def test_route_to_sql_when_location_exists_but_structured(self):
        llm = _FakeLLM(
            payload={
                "object": ["car"],
                "color": ["blue"],
                "location": ["park parking lot"],
                "event": "Blue car appears in the park parking lot",
                "confidence": 0.88,
            }
        )
        router = create_tool_router_node(llm=llm)
        out = router({"user_query": "Where is that blue car in the park parking lot"}, {}, None)
        self.assertEqual(out["tool_choice"]["mode"], "pure_sql")
        self.assertTrue(out["query_quadruple"]["location"])
        self.assertTrue(out["tool_choice"]["sql_needed"])

    def test_route_to_hybrid_when_complex_event(self):
        llm = _FakeLLM(
            payload={
                "object": ["car"],
                "color": [],
                "location": ["parking lot"],
                "event": "Car first enters then leaves the parking lot",
                "confidence": 0.88,
            }
        )
        router = create_tool_router_node(llm=llm)
        out = router({"user_query": "Car first enters then leaves in the parking lot"}, {}, None)
        self.assertEqual(out["tool_choice"]["mode"], "hybrid_search")
        self.assertTrue(out["tool_choice"]["hybrid_needed"])

    def test_route_to_sql_when_location_missing(self):
        llm = _FakeLLM(
            payload={
                "object": ["truck"],
                "color": ["red"],
                "location": [],
                "event": "Red truck appears",
                "confidence": 0.83,
            }
        )
        router = create_tool_router_node(llm=llm)
        out = router({"user_query": "When did the red truck appear"}, {}, None)
        self.assertEqual(out["tool_choice"]["mode"], "pure_sql")
        self.assertFalse(out["query_quadruple"]["location"])
        self.assertTrue(out["tool_choice"]["sql_needed"])

    def test_graceful_fallback_when_llm_failed(self):
        router = create_tool_router_node(llm=_FakeLLM(should_fail=True))
        out = router({"user_query": "Where is the white car in the parking lot"}, {}, None)
        self.assertIn("query_quadruple", out)
        self.assertIn(out["tool_choice"]["mode"], {"hybrid_search", "pure_sql"})

    def test_legacy_parallel_mode_is_unreachable(self):
        router = create_tool_router_node(
            llm=_FakeLLM(
                payload={
                    "object": ["car"],
                    "color": ["blue"],
                    "location": ["parking lot"],
                    "event": "Blue car appears in the parking lot",
                    "confidence": 0.9,
                }
            )
        )
        out = router({"user_query": "The blue car in the parking lot"}, {}, None)
        self.assertEqual(out["tool_choice"]["mode"], "pure_sql")
        self.assertEqual(route_by_tool_choice({"tool_choice": out["tool_choice"]}), "pure_sql_node")


class TestRouteTargets(unittest.TestCase):
    def test_removed_targets_unreachable(self):
        self.assertEqual(route_by_tool_choice({"tool_choice": {"mode": "video_vect"}}), "hybrid_search_node")
        self.assertEqual(route_by_tool_choice({"tool_choice": {"mode": "parallel"}}), "hybrid_search_node")


if __name__ == "__main__":
    unittest.main()
