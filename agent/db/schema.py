from __future__ import annotations

# Single source of truth for table schema/indexes and seed-field mapping.
# Update this file first when database fields change.

TABLE_NAME = "episodic_events"

CREATE_TABLE_SQL = f"""
CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Core identity
    video_id TEXT NOT NULL,
    camera_id TEXT,
    track_id TEXT,
    entity_hint TEXT,

    -- Temporal range
    clip_start_sec REAL,
    clip_end_sec REAL,
    start_time REAL,
    end_time REAL,
    duration_sec REAL,

    -- Structured retrieval fields (SQL-focused)
    object_type TEXT,
    object_color_en TEXT,
    scene_zone_en TEXT,
    motion_level TEXT,
    event_type TEXT,
    is_stationary INTEGER,

    -- Geometry fields for structured/range filtering
    start_bbox_x1 REAL,
    start_bbox_y1 REAL,
    start_bbox_x2 REAL,
    start_bbox_y2 REAL,
    end_bbox_x1 REAL,
    end_bbox_y1 REAL,
    end_bbox_x2 REAL,
    end_bbox_y2 REAL,

    -- Semantic retrieval companion fields (vector DB side)
    appearance_notes_en TEXT,
    event_text_en TEXT,
    event_summary_en TEXT,
    keywords_json TEXT,
    semantic_tags_json TEXT,
    vector_doc_text TEXT,
    vector_ref_id TEXT,

    -- Traceability and evolution
    source_format TEXT,
    schema_version TEXT,
    metadata_json TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""

INDEX_SQL_LIST = [
    f"CREATE INDEX IF NOT EXISTS idx_events_video_id ON {TABLE_NAME}(video_id);",
    f"CREATE INDEX IF NOT EXISTS idx_events_camera_id ON {TABLE_NAME}(camera_id);",
    f"CREATE INDEX IF NOT EXISTS idx_events_track_id ON {TABLE_NAME}(track_id);",
    f"CREATE INDEX IF NOT EXISTS idx_events_object_type ON {TABLE_NAME}(object_type);",
    f"CREATE INDEX IF NOT EXISTS idx_events_color ON {TABLE_NAME}(object_color_en);",
    f"CREATE INDEX IF NOT EXISTS idx_events_zone ON {TABLE_NAME}(scene_zone_en);",
    f"CREATE INDEX IF NOT EXISTS idx_events_event_type ON {TABLE_NAME}(event_type);",
    f"CREATE INDEX IF NOT EXISTS idx_events_motion_level ON {TABLE_NAME}(motion_level);",
    f"CREATE INDEX IF NOT EXISTS idx_events_start_time ON {TABLE_NAME}(start_time);",
    f"CREATE INDEX IF NOT EXISTS idx_events_end_time ON {TABLE_NAME}(end_time);",
]


INSERT_COLUMNS = [
    "video_id",
    "camera_id",
    "track_id",
    "entity_hint",
    "clip_start_sec",
    "clip_end_sec",
    "start_time",
    "end_time",
    "duration_sec",
    "object_type",
    "object_color_en",
    "scene_zone_en",
    "motion_level",
    "event_type",
    "is_stationary",
    "start_bbox_x1",
    "start_bbox_y1",
    "start_bbox_x2",
    "start_bbox_y2",
    "end_bbox_x1",
    "end_bbox_y1",
    "end_bbox_x2",
    "end_bbox_y2",
    "appearance_notes_en",
    "event_text_en",
    "event_summary_en",
    "keywords_json",
    "semantic_tags_json",
    "vector_doc_text",
    "vector_ref_id",
    "source_format",
    "schema_version",
    "metadata_json",
]

