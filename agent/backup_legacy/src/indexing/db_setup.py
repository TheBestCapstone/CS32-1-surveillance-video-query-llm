import os
import lancedb
import pyarrow as pa
from pathlib import Path

# 获取项目根目录 (Capstone)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# 将数据库文件放在 src/agent/memory/episodic/ 目录下
DB_DIR = BASE_DIR / "src" / "agent" / "memory" / "episodic" / "lancedb"
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = str(DB_DIR)

def init_db(db_path=DB_PATH):
    """初始化 LanceDB 数据库并创建表结构"""
    db = lancedb.connect(db_path)
    
    # 定义 PyArrow Schema
    # LanceDB 推荐使用 PyArrow 或 Pydantic 来定义表结构
    schema = pa.schema([
        pa.field("event_id", pa.int64()),
        pa.field("video_id", pa.string()),
        pa.field("camera_id", pa.string()),
        pa.field("track_id", pa.string()),
        pa.field("global_id", pa.string()),
        pa.field("start_time", pa.float64()),
        pa.field("end_time", pa.float64()),
        pa.field("duration", pa.float64()),
        pa.field("source_clip_start_sec", pa.float64()),
        pa.field("source_clip_end_sec", pa.float64()),
        pa.field("object_type", pa.string()),
        pa.field("object_color_cn", pa.string()),
        pa.field("scene_zone_cn", pa.string()),
        pa.field("appearance_notes_cn", pa.string()),
        pa.field("event_type", pa.string()),
        pa.field("event_text_cn", pa.string()),
        pa.field("event_summary_cn", pa.string()),
        pa.field("normalized_state", pa.string()),
        pa.field("keywords_json", pa.string()),
        pa.field("retrieval_text", pa.string()),
        pa.field("start_bbox_x1", pa.float64()),
        pa.field("start_bbox_y1", pa.float64()),
        pa.field("start_bbox_x2", pa.float64()),
        pa.field("start_bbox_y2", pa.float64()),
        pa.field("end_bbox_x1", pa.float64()),
        pa.field("end_bbox_y1", pa.float64()),
        pa.field("end_bbox_x2", pa.float64()),
        pa.field("end_bbox_y2", pa.float64()),
        # Qwen-embedding 维度为 1024
        pa.field("vector", pa.list_(pa.float32(), 1024))
    ])
    
    if "episodic_events" not in db.table_names():
        db.create_table("episodic_events", schema=schema)
        print(f"✅ 数据库表结构初始化成功！LanceDB 路径: {db_path}")
    else:
        print(f"⚠️ 数据库表 episodic_events 已存在。LanceDB 路径: {db_path}")

if __name__ == "__main__":
    init_db()
