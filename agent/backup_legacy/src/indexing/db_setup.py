import sqlite3
import sqlite_vec
import os
from pathlib import Path

# 获取项目根目录 (Capstone)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# 将数据库文件放在 src/agent/memory/episodic/ 目录下
DB_DIR = BASE_DIR / "src" / "agent" / "memory" / "episodic"
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = str(DB_DIR / "episodic_memory.db")

def init_db(db_path=DB_PATH):
    """初始化数据库并创建表结构"""
    # 如果希望每次运行都重新建库，可以先删除
    # if os.path.exists(db_path):
    #     os.remove(db_path)
        
    db = sqlite3.connect(db_path)
    db.enable_load_extension(True)
    sqlite_vec.load(db)
    db.enable_load_extension(False)
    
    cursor = db.cursor()
    
    # 1. 创建存储结构化数据的普通表
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
            object_color_cn TEXT,
            scene_zone_cn TEXT,
            appearance_notes_cn TEXT,
            event_type TEXT,
            event_text_cn TEXT,
            event_summary_cn TEXT,
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
    
    # 2. 创建 sqlite-vec 的虚拟表，用于存储 embedding (Qwen-embedding 维度为 1024)
    # 注意：vec0 虚拟表的 rowid 必须对应结构化表的 event_id
    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS episodic_events_vec USING vec0(
            embedding float[1024]
        );
    """)
    
    db.commit()
    db.close()
    print(f"✅ 数据库表结构初始化成功！文件路径: {db_path}")

if __name__ == "__main__":
    init_db()
