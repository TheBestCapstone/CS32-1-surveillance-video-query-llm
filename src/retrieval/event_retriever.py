import sqlite3
import sqlite_vec
import struct
import json
from typing import List, Dict, Any, Optional

from src.indexing.embedder import get_qwen_embedding

from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_DB_PATH = str(BASE_DIR / "src" / "agent" / "memory" / "episodic" / "episodic_memory.db")

def serialize_f32(vector: list[float]) -> bytes:
    return struct.pack(f"{len(vector)}f", *vector)

class EventRetriever:
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path

    def _get_db_connection(self):
        db = sqlite3.connect(self.db_path)
        db.row_factory = sqlite3.Row  # 返回字典格式
        db.enable_load_extension(True)
        sqlite_vec.load(db)
        db.enable_load_extension(False)
        return db

    def get_event_detail(self, event_id: int) -> Optional[Dict[str, Any]]:
        """按 event_id 获取完整事件详情"""
        db = self._get_db_connection()
        cursor = db.cursor()
        
        cursor.execute("SELECT * FROM episodic_events WHERE event_id = ?", (event_id,))
        row = cursor.fetchone()
        
        db.close()
        
        if row:
            return dict(row)
        return None

    def structured_search(self, 
                          video_id: str = None, 
                          object_type: str = None,
                          scene_zone_cn: str = None,
                          min_duration: float = None,
                          start_time_after: float = None,
                          limit: int = 10) -> List[Dict[str, Any]]:
        """纯结构化字段检索 (不使用向量)"""
        db = self._get_db_connection()
        cursor = db.cursor()
        
        query = "SELECT * FROM episodic_events WHERE 1=1"
        params = []
        
        if video_id:
            query += " AND video_id = ?"
            params.append(video_id)
        if object_type:
            query += " AND object_type = ?"
            params.append(object_type)
        if scene_zone_cn:
            query += " AND scene_zone_cn = ?"
            params.append(scene_zone_cn)
        if min_duration is not None:
            query += " AND duration >= ?"
            params.append(min_duration)
        if start_time_after is not None:
            query += " AND start_time >= ?"
            params.append(start_time_after)
            
        query += " ORDER BY start_time ASC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        db.close()
        
        return [dict(row) for row in rows]

    def hybrid_event_search(self, 
                            query_text: str, 
                            top_k: int = 5,
                            video_id: str = None,
                            object_type: str = None,
                            scene_zone_cn: str = None,
                            start_time_after: float = None,
                            end_time_before: float = None) -> List[Dict[str, Any]]:
        """
        混合检索：同时做 SQLite 条件过滤 和 向量相似检索
        """
        # 1. 对查询文本进行 embedding
        try:
            query_vector = get_qwen_embedding(query_text)
        except Exception as e:
            print(f"获取 Query Embedding 失败: {e}")
            return []

        db = self._get_db_connection()
        cursor = db.cursor()

        # 2. 构建查询 SQL (结合 vec0 虚拟表和普通表)
        # 使用 vec_distance_L2 或者通过 match 查询
        
        base_query = """
            SELECT 
                e.event_id,
                e.video_id,
                e.start_time,
                e.end_time,
                e.event_summary_cn,
                v.distance
            FROM episodic_events_vec v
            JOIN episodic_events e ON v.rowid = e.event_id
            WHERE v.embedding MATCH ?
            AND k = ?
        """
        
        params = [serialize_f32(query_vector), top_k]
        
        # 增加结构化过滤条件
        if video_id:
            base_query += " AND e.video_id = ?"
            params.append(video_id)
            
        if object_type:
            base_query += " AND e.object_type = ?"
            params.append(object_type)
            
        if scene_zone_cn:
            base_query += " AND e.scene_zone_cn = ?"
            params.append(scene_zone_cn)
            
        if start_time_after is not None:
            base_query += " AND e.start_time >= ?"
            params.append(start_time_after)
            
        if end_time_before is not None:
            base_query += " AND e.end_time <= ?"
            params.append(end_time_before)
            
        # 排序
        base_query += " ORDER BY v.distance ASC"
        
        cursor.execute(base_query, params)
        rows = cursor.fetchall()
        db.close()
        
        results = [dict(row) for row in rows]
        return results

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    try:
        load_dotenv()
    except Exception:
        pass
        
    if not os.environ.get("DASHSCOPE_API_KEY"):
        print("测试需要设置 DASHSCOPE_API_KEY")
    else:
        retriever = EventRetriever()
        
        print("🔍 测试 get_event_detail (event_id=1):")
        detail = retriever.get_event_detail(1)
        if detail:
            print(f"成功获取: {detail.get('event_summary_cn')}")
        else:
            print("未找到事件，可能数据库为空。")
            
        print("\n🔍 测试 hybrid_event_search ('寻找停放的汽车'):")
        results = retriever.hybrid_event_search("寻找停放的汽车", top_k=3)
        for idx, res in enumerate(results):
            print(f"[{idx+1}] ID: {res['event_id']}, 视频: {res['video_id']}, 距离: {res['distance']:.4f}")
            print(f"    摘要: {res['event_summary_cn']}")
