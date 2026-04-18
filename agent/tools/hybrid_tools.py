from typing import List, Dict, Any, Optional
from langchain_core.tools import tool
from tools.db_access import LanceDBGateway
from node.types import default_db_path
import sqlite3
from node.types import default_sqlite_db_path
import json

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
            
        where_clauses = " OR ".join(["event_text_cn LIKE ?"] * len(keywords))
        params = [f"%{k}%" for k in keywords]
        
        sql = f"SELECT video_id, start_time, end_time, event_text_cn FROM episodic_events WHERE {where_clauses} LIMIT 3"
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
    db_path = default_db_path()
    try:
        gateway = LanceDBGateway(db_path)
        # 将 filters 字典转换为元组列表
        meta_list = [{"key": k, "value": v} for k, v in filters.items()]
        
        # 为了演示，这里的底层接口暂时只接受 query，我们需要将 alpha 逻辑应用。
        # 假定底层支持或我们通过逻辑模拟：如果 alpha 很高，我们放宽元数据；如果很低，我们强制元数据。
        # 这里演示调用现有接口，并在日志中打印出策略。
        rows = gateway.search_table(
            "episodic_events",
            metadata_filters=meta_list if alpha < 0.8 else [], # alpha很高时放宽过滤
            event_queries=[query] if query else [],
            limit=limit * 2
        )
        
        if not rows:
            return f"使用权重 alpha={alpha} 未检索到结果。可以尝试放宽 filters 或调整 alpha。"
            
        # 简单模拟重排截断
        result_rows = rows[:limit]
        
        # 格式化输出
        output = [
            {
                "video_id": r.get("video_id"),
                "event_text": r.get("event_text_cn"),
                "start_time": r.get("start_time"),
                "distance": r.get("distance", 0.0)
            } for r in result_rows
        ]
        
        return f"Hybrid search successful (weight strategy alpha={alpha}):\n{json.dumps(output, ensure_ascii=False, indent=2)}"
    except Exception as e:
        return f"Hybrid search failed: {str(e)}"
