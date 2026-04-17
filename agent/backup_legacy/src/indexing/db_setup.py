import sqlite3
import sqlite_vec
import os
from pathlib import Path

# Project root (legacy layout expects src/agent/memory/episodic under BASE_DIR)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

DB_DIR = BASE_DIR / "src" / "agent" / "memory" / "episodic"
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = str(DB_DIR / "episodic_memory.db")


def init_db(db_path=DB_PATH):
    """Create SQLite schema for episodic events + sqlite-vec embeddings."""
    db = sqlite3.connect(db_path)
    db.enable_load_extension(True)
    sqlite_vec.load(db)
    db.enable_load_extension(False)

    cursor = db.cursor()

    # Structured events table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS episodic_events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id TEXT,
            camera_id TEXT,
            track_id TEXT,
            global_id TEXT,
            start_time REAL,
            end_time REAL,
            duration REAL,
            source_clip_start_sec REAL,
            source_clip_end_sec REAL,
            object_type TEXT,
            object_color TEXT,
            scene_zone TEXT,
            appearance_notes TEXT,
            event_type TEXT,
            event_text TEXT,
            event_summary TEXT,
            normalized_state TEXT,
            keywords_json TEXT,
            retrieval_text TEXT,
            start_bbox_x1 REAL,
            start_bbox_y1 REAL,
            start_bbox_x2 REAL,
            start_bbox_y2 REAL,
            end_bbox_x1 REAL,
            end_bbox_y1 REAL,
            end_bbox_x2 REAL,
            end_bbox_y2 REAL
        );
    """)

    # sqlite-vec: rowid must match episodic_events.event_id
    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS episodic_events_vec USING vec0(
            embedding float[1024]
        );
    """)

    db.commit()
    db.close()
    print(f"Database schema initialized: {db_path}")


if __name__ == "__main__":
    init_db()
