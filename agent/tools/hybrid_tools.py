from typing import Any
from langchain_core.tools import tool
from tools.db_access import ChromaGateway
import sqlite3
import json
from node.types import default_chroma_collection, default_chroma_path, default_sqlite_db_path

@tool
def get_temporal_anchor(event_description: str) -> str:
    """
    Find the timestamp (start_time, end_time) of a specific semantic event to serve as a temporal anchor.
    Example query: 'When did the red car leave?'
    """
    # 简易实现：使用 SQL 的 LIKE 模糊匹配在 sqlite 中查找。也可以让 LLM 动态写 SQL，但工具化封装更安全。
    db_path = default_sqlite_db_path()
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 简单提取关键字（为了演示），实际中可依赖更复杂的提取，这里直接做简单的模糊搜索
        # 如果 event_description 包含颜色或动作，简单分词
        keywords = event_description.split()
        if not keywords:
            keywords = [event_description]
            
        where_clauses = " OR ".join(["COALESCE(event_text_en, event_summary_en, '') LIKE ?"] * len(keywords))
        params = [f"%{k}%" for k in keywords]
        
        sql = (
            f"SELECT video_id, start_time, end_time, "
            f"COALESCE(event_text_en, event_summary_en) AS event_text "
            f"FROM episodic_events WHERE {where_clauses} LIMIT 3"
        )
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return "未找到符合描述的时间锚点。"
            
        res = [dict(r) for r in rows]
        return f"Found temporal anchors:\n{json.dumps(res, ensure_ascii=False, indent=2)}\n\nYou can extract start_time from this."
    except Exception as e:
        return [{"error": "Temporal anchor failed. Please note: Time-dimension queries are generally unsupported, but if finding an event time, it failed here: " + str(e)}]

@tool
def dynamic_weighted_vector_search(query: str, filters: dict, alpha: float = 0.5, limit: int = 5) -> str:
    """
    Execute a dynamic weighted hybrid search (vector similarity + metadata filters).
    Parameters:
    - query: Semantic query string from user (e.g., "vehicle frantically reversing to dodge")
    - filters: Metadata filter dictionary (e.g., {"object_color_en": "Red"})
    - alpha: Weight parameter (0.0 to 1.0).
             alpha = 1.0 means pure vector (semantic) search.
             alpha = 0.0 means pure metadata (attribute) search.
             Increase alpha (e.g., 0.8) if the query focuses more on semantic actions; decrease alpha (e.g., 0.2) if it focuses more on specific attributes.
    - limit: Number of results to return
    """
    db_path = default_chroma_path()
    collection = default_chroma_collection()
    try:
        gateway = ChromaGateway(db_path=db_path, collection_name=collection)
        meta_list = [{"key": k, "value": v} for k, v in filters.items()]

        rows = gateway.search(
            query=query,
            metadata_filters=meta_list if alpha < 0.8 else [],
            alpha=alpha,
            limit=limit,
        )

        if not rows:
            return (
                f"Hybrid search returned no results on Chroma "
                f"(collection={collection}, alpha={alpha}). Try relaxing filters or adjusting alpha."
            )

        output = [
            {
                "event_id": r.get("event_id"),
                "video_id": r.get("video_id"),
                "track_id": r.get("track_id"),
                "event_text": r.get("event_text") or r.get("event_summary_en"),
                "start_time": r.get("start_time"),
                "end_time": r.get("end_time"),
                "object_type": r.get("object_type"),
                "object_color_en": r.get("object_color_en"),
                "scene_zone_en": r.get("scene_zone_en"),
                "distance": r.get("_distance", 0.0),
                "hybrid_score": r.get("_hybrid_score", 0.0),
                "bm25": r.get("_bm25", 0.0),
            }
            for r in rows
        ]

        return f"Hybrid search successful on Chroma (alpha={alpha}):\n{json.dumps(output, ensure_ascii=False, indent=2)}"
    except Exception as e:
        return f"Hybrid search failed on Chroma: {str(e)}"
