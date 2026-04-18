import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

AGENT_DIR = Path(__file__).resolve().parents[1]
if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))
TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

from result_test_runner import run_result_tests


class _FakeGraph:
    def stream(self, state, config, stream_mode="values"):
        del config, stream_mode
        question = state["messages"][0].content
        if "行人" in question:
            yield {
                "tool_choice": {"mode": "pure_sql"},
                "final_answer": "ok",
                "current_node": "pure_sql_node",
                "sql_result": [{"video_id": "v1.mp4", "event_summary_cn": "行人出现"}],
                "tool_error": None,
                "thought": "ok",
            }
        else:
            yield {
                "tool_choice": {"mode": "hybrid_search"},
                "final_answer": "ok",
                "current_node": "hybrid_search_node",
                "hybrid_result": [{"video_id": "v2.mp4", "event_text_cn": "车辆进入"}],
                "tool_error": None,
                "thought": "ok",
            }


class TestResultRunner(unittest.TestCase):
    def test_data_driven_report_generation(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            cases_path = tmp / "cases.json"
            result_md = tmp / "result.md"
            result_json = tmp / "result_report.json"
            cases_path.write_text(
                json.dumps(
                    [
                        {
                            "id": "A1",
                            "question": "帮我找行人",
                            "expected_answer": "返回行人结果",
                            "expected_routes": ["pure_sql"],
                            "min_results": 1,
                            "required_top_fields": ["video_id", "event_text"],
                        },
                        {
                            "id": "A2",
                            "question": "停车场车辆进入",
                            "expected_answer": "返回车辆结果",
                            "expected_routes": ["hybrid_search"],
                            "min_results": 1,
                            "required_top_fields": ["video_id", "event_text"],
                        },
                    ],
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            with patch("result_test_runner.graph_module.create_graph", return_value=_FakeGraph()):
                out = run_result_tests(cases_path=cases_path, output_md=result_md, output_json=result_json)

            self.assertEqual(out["summary"]["total"], 2)
            self.assertEqual(out["summary"]["failed"], 0)
            self.assertTrue(result_md.exists())
            self.assertTrue(result_json.exists())


if __name__ == "__main__":
    unittest.main()
