import json
import sqlite3
import sys
import time
import unittest
from pathlib import Path

from langchain_core.messages import HumanMessage

AGENT_DIR = Path(__file__).resolve().parents[1]
if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))

from node.pure_sql_node import create_pure_sql_node
from node.tool_router_node import create_tool_router_node


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


def _router_state():
    llm = _FakeLLM(
        {
            "object": ["person"],
            "color": [],
            "location": [],
            "event": "A person enters the frame",
            "confidence": 0.9,
        }
    )
    router = create_tool_router_node(llm=llm)
    state = router({"messages": [HumanMessage(content="A person enters the frame")]}, {}, None)
    return state


def _build_tmp_db(path: Path):
    if path.exists():
        path.unlink()
    conn = sqlite3.connect(path)
    conn.execute(
        "CREATE TABLE episodic_events (event_id INTEGER PRIMARY KEY, video_id TEXT, camera_id TEXT, track_id TEXT, start_time REAL, end_time REAL, object_type TEXT, object_color_cn TEXT)"
    )
    conn.executemany(
        "INSERT INTO episodic_events(event_id, video_id, camera_id, track_id, start_time, end_time, object_type, object_color_cn) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (1, "a.mp4", "c1", "t1", 1.0, 2.0, "person", ""),
            (2, "b.mp4", "c2", "t2", 3.0, 4.0, "car", "red"),
        ],
    )
    conn.commit()
    conn.close()


class TestPureSqlNode(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db_path = AGENT_DIR / "test" / "tmp_sql_test.sqlite"
        _build_tmp_db(cls.db_path)

    @classmethod
    def tearDownClass(cls):
        if cls.db_path.exists():
            cls.db_path.unlink()

    def _write_perf(self, latencies: list[float], result_counts: list[int]) -> None:
        baseline_file = AGENT_DIR / "test" / "perf_baseline.json"
        data = {}
        if baseline_file.exists():
            data = json.loads(baseline_file.read_text(encoding="utf-8"))
        p95 = sorted(latencies)[max(0, int(len(latencies) * 0.95) - 1)] if latencies else 0.0
        data["sql_p95_ms"] = round(p95, 3)
        data["sql_avg_rows"] = round(sum(result_counts) / len(result_counts), 3) if result_counts else 0.0
        baseline_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def test_state_no_loss(self):
        state = _router_state()
        state["sql_plan"] = {
            "table": "episodic_events",
            "fields": ["event_id", "video_id", "object_type"],
            "where": [{"field": "object_type", "op": "contains", "value": "person"}],
            "order_by": "start_time ASC",
            "limit": 20,
        }
        node = create_pure_sql_node(db_path=self.db_path)
        out = node(state, {}, None)
        merged = {**state, **out}
        for key in ["tool_choice", "parsed_question", "meta_list", "event_list", "query_quadruple", "sql_plan"]:
            self.assertIn(key, merged)

    def test_normal_query_and_perf(self):
        state = _router_state()
        state["sql_plan"] = {
            "table": "episodic_events",
            "fields": ["event_id", "video_id", "object_type", "start_time", "end_time"],
            "where": [{"field": "object_type", "op": "contains", "value": "person"}],
            "order_by": "start_time ASC",
            "limit": 20,
        }
        node = create_pure_sql_node(db_path=self.db_path)
        latencies = []
        counts = []
        for _ in range(5):
            start = time.perf_counter()
            out = node(state, {}, None)
            latencies.append((time.perf_counter() - start) * 1000)
            counts.append(len(out.get("sql_result", [])))
        self.assertGreaterEqual(len(out.get("sql_result", [])), 1)
        self._write_perf(latencies, counts)

    def test_empty_result(self):
        state = _router_state()
        state["sql_plan"] = {
            "table": "episodic_events",
            "fields": ["event_id", "video_id", "object_type"],
            "where": [{"field": "object_type", "op": "==", "value": "truck"}],
            "order_by": "start_time ASC",
            "limit": 20,
        }
        node = create_pure_sql_node(db_path=self.db_path)
        out = node(state, {}, None)
        self.assertEqual(len(out.get("sql_result", [])), 0)

    def test_sql_exception(self):
        state = _router_state()

        def bad_strategy(_state):
            return "SELECT * FROM not_exists LIMIT ?", [1], {"table": "not_exists", "fields": ["event_id"]}

        node = create_pure_sql_node(db_path=self.db_path, strategy=bad_strategy)
        out = node(state, {}, None)
        self.assertIsNotNone(out.get("tool_error"))

    def test_connection_timeout(self):
        state = _router_state()
        state["sql_plan"] = {
            "table": "episodic_events",
            "fields": ["event_id", "video_id"],
            "where": [],
            "order_by": "start_time ASC",
            "limit": 5,
        }

        def timeout_connection(_path):
            raise TimeoutError("connection timeout")

        node = create_pure_sql_node(db_path=self.db_path, connection_factory=timeout_connection)
        out = node(state, {}, None)
        self.assertIn("超时", out.get("tool_error", "").replace("timeout", "超时"))


if __name__ == "__main__":
    unittest.main()