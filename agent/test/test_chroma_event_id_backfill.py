"""Smoke test: verify Chroma event_id backfill + RRF overlap fix.

Run:  python -m pytest agent/test/test_chroma_event_id_backfill.py -v
"""

import importlib.util
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _load_module(filepath: Path, name: str) -> None:
    """Load a module with relative imports by setting up sys.modules."""
    spec = importlib.util.spec_from_file_location(name, filepath)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {filepath}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# Pre-load the package hierarchy needed for chroma_builder's relative imports.
# chroma_builder is at agent/db/chroma_builder.py
#   from .config import ... → agent.db.config
#   from ..tools.llm import ... → agent.tools.llm

# Register package stubs
for pkg_name in ["agent", "agent.db", "agent.tools"]:
    if pkg_name not in sys.modules:
        sys.modules[pkg_name] = type(sys)(pkg_name)

# Patch get_qwen_embedding
sys.modules["agent.tools.llm"] = type(sys)("agent.tools.llm")
sys.modules["agent.tools.llm"].get_qwen_embedding = MagicMock(return_value=[[0.1] * 768])

_load_module(ROOT / "db" / "config.py", "agent.db.config")
_load_module(ROOT / "db" / "chroma_builder.py", "agent.db.chroma_builder")

from agent.db.chroma_builder import ChromaBuildConfig, ChromaIndexBuilder


class ChromaEventIdBackfillTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        self.sqlite_path = Path(self.tmpdir.name) / "test.sqlite"
        self._create_sqlite_db()

    def tearDown(self) -> None:
        self.tmpdir.cleanup()

    def _create_sqlite_db(self) -> None:
        from db.schema import CREATE_TABLE_SQL, INSERT_COLUMNS

        conn = sqlite3.connect(str(self.sqlite_path))
        conn.execute(CREATE_TABLE_SQL)
        # Insert 3 test events
        rows = [
            {
                "video_id": "v1",
                "track_id": "t1",
                "entity_hint": "t1",
                "start_time": 10.5,
                "end_time": 15.2,
                "object_type": "car",
                "object_color_en": "red",
                "scene_zone_en": "road",
                "event_text_en": "car drives on road",
                "event_summary_en": "red car moving",
                "appearance_notes_en": "bright red sedan",
            },
            {
                "video_id": "v1",
                "track_id": "t1",
                "entity_hint": "t1",
                "start_time": 20.0,
                "end_time": 25.0,
                "object_type": "car",
                "object_color_en": "red",
                "scene_zone_en": "road",
                "event_text_en": "car turns left",
                "event_summary_en": "car turning",
                "appearance_notes_en": "same red car",
            },
            {
                "video_id": "v1",
                "track_id": "t2",
                "entity_hint": "t2",
                "start_time": 30.0,
                "end_time": 35.0,
                "object_type": "person",
                "object_color_en": "blue",
                "scene_zone_en": "sidewalk",
                "event_text_en": "person walks",
                "event_summary_en": "blue shirt person walking",
                "appearance_notes_en": "person in blue",
            },
        ]
        cols = ", ".join(INSERT_COLUMNS)
        placeholders = ", ".join(["?"] * len(INSERT_COLUMNS))
        conn.executemany(
            f"INSERT INTO episodic_events ({cols}) VALUES ({placeholders})",
            [tuple(row.get(col) for col in INSERT_COLUMNS) for row in rows],
        )
        conn.commit()
        conn.close()

    def test_lookup_event_id_by_natural_key(self) -> None:
        """_lookup_event_id should find the correct SQLite event_id."""
        config = ChromaBuildConfig(
            chroma_path=Path(self.tmpdir.name) / "chroma",
            sqlite_db_path=self.sqlite_path,
        )
        builder = ChromaIndexBuilder(config)

        # Event 1: v1/t1/10.5/15.2 → should return event_id=1
        eid = builder._lookup_event_id("v1", "t1", 10.5, 15.2)
        self.assertEqual(eid, 1, f"Expected event_id=1, got {eid}")

        # Event 2: v1/t1/20.0/25.0 → should return event_id=2
        eid = builder._lookup_event_id("v1", "t1", 20.0, 25.0)
        self.assertEqual(eid, 2, f"Expected event_id=2, got {eid}")

        # Event 3: v1/t2/30.0/35.0 → should return event_id=3
        eid = builder._lookup_event_id("v1", "t2", 30.0, 35.0)
        self.assertEqual(eid, 3, f"Expected event_id=3, got {eid}")

        # Non-existent: should return None
        eid = builder._lookup_event_id("v1", "t1", 99.0, 99.0)
        self.assertIsNone(eid, f"Expected None for non-existent event, got {eid}")

    def test_lookup_event_ids_for_track(self) -> None:
        """_lookup_event_ids_for_track should return all event_ids for a track."""
        config = ChromaBuildConfig(
            chroma_path=Path(self.tmpdir.name) / "chroma",
            sqlite_db_path=self.sqlite_path,
        )
        builder = ChromaIndexBuilder(config)

        # Track t1 has events 1,2
        ids = builder._lookup_event_ids_for_track("v1", "t1")
        self.assertEqual(ids, [1, 2])

        # Track t2 has event 3
        ids = builder._lookup_event_ids_for_track("v1", "t2")
        self.assertEqual(ids, [3])

        # Non-existent track
        ids = builder._lookup_event_ids_for_track("v1", "nonexistent")
        self.assertEqual(ids, [])

    def test_lookup_without_sqlite_returns_none(self) -> None:
        """When sqlite_db_path is None, lookups should return None/empty."""
        config = ChromaBuildConfig(
            chroma_path=Path(self.tmpdir.name) / "chroma",
            sqlite_db_path=None,
        )
        builder = ChromaIndexBuilder(config)

        self.assertIsNone(builder._lookup_event_id("v1", "t1", 10.5, 15.2))
        self.assertEqual(builder._lookup_event_ids_for_track("v1", "t1"), [])


class WeightedRrfOverlapTests(unittest.TestCase):
    """Test that RRF overlap works when event_ids match across branches."""

    def test_overlap_with_matching_event_ids(self) -> None:
        """When SQL and hybrid rows share the same event_id, overlap_count > 0."""
        from agents.shared.fusion_engine import weighted_rrf_fuse

        sql_rows = [
            {"event_id": 42, "video_id": "v1", "track_id": "t1",
             "start_time": 10.5, "end_time": 15.2,
             "event_summary_en": "sql summary", "_source_type": "sql"},
        ]
        hybrid_rows = [
            {"event_id": 42, "video_id": "v1", "track_id": "t1",
             "start_time": 10.5, "end_time": 15.2,
             "event_summary_en": "hybrid summary", "_source_type": "hybrid"},
        ]

        rows, meta = weighted_rrf_fuse(sql_rows, hybrid_rows, label="mixed", limit=5)

        self.assertEqual(len(rows), 1)
        self.assertEqual(meta["overlap_count"], 1,
                         "Expected overlap_count=1 when event_id matches")
        self.assertEqual(rows[0].get("_source_type"), "fused",
                         "Expected _source_type='fused' for overlapping row")
        self.assertTrue(rows[0].get("_fusion_trace", {}).get("seen_in_sql"))
        self.assertTrue(rows[0].get("_fusion_trace", {}).get("seen_in_hybrid"))

    def test_overlap_only_for_same_event_id(self) -> None:
        """Different event_ids should NOT be fused."""
        from agents.shared.fusion_engine import weighted_rrf_fuse

        sql_rows = [
            {"event_id": 1, "video_id": "v1", "track_id": "t1",
             "start_time": 10.5, "end_time": 15.2,
             "event_summary_en": "event A", "_source_type": "sql"},
        ]
        hybrid_rows = [
            {"event_id": 2, "video_id": "v1", "track_id": "t1",
             "start_time": 29.0, "end_time": 32.0,
             "event_summary_en": "event B", "_source_type": "hybrid"},
        ]

        rows, meta = weighted_rrf_fuse(sql_rows, hybrid_rows, label="mixed", limit=5)

        self.assertEqual(len(rows), 2)
        self.assertEqual(meta["overlap_count"], 0,
                         "Expected overlap_count=0 when event_ids differ")
        # Both should keep their source type
        source_types = {r.get("_source_type") for r in rows}
        self.assertNotIn("fused", source_types,
                         "No row should have _source_type='fused'")

    def test_partial_overlap_with_mixed_ids(self) -> None:
        """Only rows with matching event_id should be fused."""
        from agents.shared.fusion_engine import weighted_rrf_fuse

        sql_rows = [
            {"event_id": 1, "video_id": "v1", "track_id": "t1",
             "start_time": 10.0, "end_time": 15.0,
             "event_summary_en": "shared event", "_source_type": "sql"},
            {"event_id": 2, "video_id": "v1", "track_id": "t2",
             "start_time": 20.0, "end_time": 25.0,
             "event_summary_en": "sql only", "_source_type": "sql"},
        ]
        hybrid_rows = [
            {"event_id": 1, "video_id": "v1", "track_id": "t1",
             "start_time": 10.0, "end_time": 15.0,
             "event_summary_en": "shared event", "_source_type": "hybrid"},
            {"event_id": 3, "video_id": "v1", "track_id": "t3",
             "start_time": 30.0, "end_time": 35.0,
             "event_summary_en": "hybrid only", "_source_type": "hybrid"},
        ]

        rows, meta = weighted_rrf_fuse(sql_rows, hybrid_rows, label="mixed", limit=10)

        self.assertEqual(len(rows), 3)
        self.assertEqual(meta["overlap_count"], 1,
                         "Only event_id=1 should be overlapping")

        # event_id=1 row should be fused
        fused_row = [r for r in rows if r.get("event_id") == 1]
        self.assertEqual(len(fused_row), 1)
        self.assertEqual(fused_row[0].get("_source_type"), "fused")

        # event_id=2 row should be sql only
        sql_only = [r for r in rows if r.get("event_id") == 2]
        self.assertEqual(len(sql_only), 1)
        self.assertNotEqual(sql_only[0].get("_source_type"), "fused")

        # event_id=3 row should be hybrid only
        hybrid_only = [r for r in rows if r.get("event_id") == 3]
        self.assertEqual(len(hybrid_only), 1)
        self.assertNotEqual(hybrid_only[0].get("_source_type"), "fused")

    def test_overlap_with_mixed_event_id_types_int_vs_str(self) -> None:
        """P0-1 fix: SQL (int) and Chroma (str) event_ids should fuse correctly.

        This was the root cause of the RRF ID mismatch bug: SQL returns
        ``event_id=42`` (int) while Chroma returns ``event_id="42"`` (str),
        causing ``_row_key`` to generate different keys and ``overlap_count``
        to always be 0.
        """
        from agents.shared.fusion_engine import weighted_rrf_fuse

        sql_rows = [
            {"event_id": 42, "video_id": "v1", "track_id": "t1",
             "start_time": 10.5, "end_time": 15.2,
             "event_summary_en": "sql summary", "_source_type": "sql"},
        ]
        # Chroma returns event_id as string
        hybrid_rows = [
            {"event_id": "42", "video_id": "v1", "track_id": "t1",
             "start_time": 10.5, "end_time": 15.2,
             "event_summary_en": "hybrid summary", "_source_type": "hybrid"},
        ]

        rows, meta = weighted_rrf_fuse(sql_rows, hybrid_rows, label="mixed", limit=5)

        self.assertEqual(len(rows), 1, "Should be 1 fused row, not 2 separate rows")
        self.assertEqual(meta["overlap_count"], 1,
                         "Expected overlap_count=1 when int 42 matches str '42'")
        self.assertEqual(rows[0].get("_source_type"), "fused",
                         "Expected _source_type='fused' for cross-type match")

    def test_overlap_with_numeric_string_event_id(self) -> None:
        """P0-1 fix: '42.0' string should also match int 42."""
        from agents.shared.fusion_engine import weighted_rrf_fuse

        sql_rows = [
            {"event_id": 42, "video_id": "v1", "track_id": "t1",
             "start_time": 10.5, "end_time": 15.2,
             "event_summary_en": "sql row", "_source_type": "sql"},
        ]
        hybrid_rows = [
            {"event_id": "42.0", "video_id": "v1", "track_id": "t1",
             "start_time": 10.5, "end_time": 15.2,
             "event_summary_en": "hybrid row", "_source_type": "hybrid"},
        ]

        rows, meta = weighted_rrf_fuse(sql_rows, hybrid_rows, label="mixed", limit=5)

        self.assertEqual(len(rows), 1, "'42.0' should normalize to 42 and match")
        self.assertEqual(meta["overlap_count"], 1)


if __name__ == "__main__":
    unittest.main()
