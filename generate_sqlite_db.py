import json
import sqlite3
from pathlib import Path

def create_and_populate_db():
    json_path = Path("agent/mock_data/data/video_events_mock.json")
    db_path = Path("data/SQLite/episodic_events.sqlite")
    
    if not json_path.exists():
        print(f"Error: {json_path} does not exist.")
        return

    # Ensure target directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Delete old DB if it exists
    if db_path.exists():
        db_path.unlink()
        
    print(f"Creating new database at {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create table with all needed fields
    cursor.execute("""
    CREATE TABLE episodic_events (
        event_id INTEGER PRIMARY KEY AUTOINCREMENT,
        video_id TEXT,
        camera_id TEXT,
        track_id TEXT,
        start_time REAL,
        end_time REAL,
        object_type TEXT,
        object_color_cn TEXT,
        scene_zone_cn TEXT,
        appearance_notes_cn TEXT,
        event_text_cn TEXT,
        event_summary_cn TEXT
    )
    """)
    
    print(f"Loading data from {json_path}...")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    all_events = []
    for video in data:
        for event in video.get("events", []):
            track_id = event.get("entity_hint", "").replace("track_id=", "")
            
            # Construct summary text if not present
            obj_color = event.get("object_color_cn", "")
            obj_type = event.get("object_type", "")
            scene_zone = event.get("scene_zone_cn", "")
            appearance = event.get("appearance_notes_cn", "")
            event_summary = f"{obj_color}的{obj_type}在{scene_zone}{appearance}"
            
            all_events.append((
                event.get("video_id", ""),
                event.get("camera_id", ""),
                track_id,
                float(event.get("start_time", 0.0)),
                float(event.get("end_time", 0.0)),
                obj_type,
                obj_color,
                scene_zone,
                appearance,
                event.get("event_text_cn", ""),
                event_summary
            ))
            
    print(f"Inserting {len(all_events)} records...")
    cursor.executemany("""
        INSERT INTO episodic_events (
            video_id, camera_id, track_id, start_time, end_time, 
            object_type, object_color_cn, scene_zone_cn, 
            appearance_notes_cn, event_text_cn, event_summary_cn
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, all_events)
    
    conn.commit()
    conn.close()
    print("Database generation complete!")

if __name__ == "__main__":
    create_and_populate_db()
