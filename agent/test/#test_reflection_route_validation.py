import sys
import unittest
from pathlib import Path

AGENT_DIR = Path(__file__).resolve().parents[1]
if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))

from node.reflection_node import create_reflection_node


class TestReflectionRouteValidation(unittest.TestCase):
    def test_route_validation_blocks_invalid_conflict(self):
        node = create_reflection_node(max_retries=3)
        state = {
            "user_query": "test",
            "tool_choice": {
                "mode": "pure_sql",
                "sql_needed": True,
                "hybrid_needed": True,  # conflict
                "sub_queries": {"sql": {}, "hybrid": {}},
            },
            "retry_count": 0,
            "sql_result": [],
            "hybrid_result": [],
            "meta_list": [],
            "event_list": [],
            "reflection_result": {},
        }
        out = node(state, {}, None)
        self.assertTrue(out.get("reflection_result", {}).get("validation_failed"))
        self.assertIn("路由规则有效性验证失败", out.get("tool_error", ""))
        self.assertGreater(len(out.get("reflection_result", {}).get("violations", [])), 0)

    def test_route_validation_passes_valid_route(self):
        node = create_reflection_node(max_retries=3)
        state = {
            "user_query": "test",
            "tool_choice": {
                "mode": "pure_sql",
                "sql_needed": True,
                "hybrid_needed": False,
                "sub_queries": {"sql": {}},
            },
            "retry_count": 0,
            "sql_result": [{"event_id": 1}],
            "hybrid_result": [],
            "meta_list": [],
            "event_list": [],
            "reflection_result": {},
        }
        out = node(state, {}, None)
        self.assertFalse(out.get("reflection_result", {}).get("validation_failed", False))


if __name__ == "__main__":
    unittest.main()
