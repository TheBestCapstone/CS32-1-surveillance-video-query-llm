import json
import sqlite3
import sqlite_vec
import struct
import concurrent.futures
from src.indexing.embedder import get_qwen_embedding

def serialize_f32(vector: list[float]) -> bytes:
    """将 float list 序列化为 sqlite-vec 支持的二进制格式"""
    return struct.pack(f"{len(vector)}f", *vector)

def preprocess_event(raw_event: dict) -> dict:
    """将原始 JSON 事件处理成标准字段"""
    # 处理 bbox
    start_bbox = raw_event.get("start_bbox_xyxy", [0,0,0,0])
    end_bbox = raw_event.get("end_bbox_xyxy", [0,0,0,0])
    
    # 提取时间
    start_time = raw_event.get("start_time", 0.0)
    end_time = raw_event.get("end_time", 0.0)
    duration = end_time - start_time
    
    # 提取 track_id
    track_id = raw_event.get("entity_hint", "").replace("track_id=", "")
    
    # 提取 keywords (第一个作为 event_type)
    keywords = raw_event.get("keywords", [])
    event_type = keywords[0] if keywords else ""
    keywords_json = json.dumps(keywords, ensure_ascii=False)
    
    # 获取其他属性
    obj_color = raw_event.get("object_color_cn", "")
    obj_type = raw_event.get("object_type", "")
    scene_zone = raw_event.get("scene_zone_cn", "")
    appearance = raw_event.get("appearance_notes_cn", "")
    
    # 生成规范化文本
    event_summary_cn = f"{obj_color}的{obj_type}在{scene_zone}{appearance}"
    normalized_state = appearance.split("，")[0] if "，" in appearance else appearance
    retrieval_text = f"{obj_color} {obj_type} {scene_zone} {appearance} {' '.join(keywords)}"
    
    return {
        "video_id": raw_event.get("video_id", ""),
        "camera_id": raw_event.get("camera_id", ""),
        "track_id": track_id,
        "global_id": f"{raw_event.get('video_id', '')}_{track_id}_{start_time}",
        "start_time": start_time,
        "end_time": end_time,
        "duration": duration,
        "source_clip_start_sec": raw_event.get("clip_start_sec", 0.0),
        "source_clip_end_sec": raw_event.get("clip_end_sec", 0.0),
        "object_type": obj_type,
        "object_color_cn": obj_color,
        "scene_zone_cn": scene_zone,
        "appearance_notes_cn": appearance,
        "event_type": event_type,
        "event_text_cn": raw_event.get("event_text_cn", ""),
        "event_summary_cn": event_summary_cn,
        "normalized_state": normalized_state,
        "keywords_json": keywords_json,
        "retrieval_text": retrieval_text,
        "start_bbox_x1": start_bbox[0],
        "start_bbox_y1": start_bbox[1],
        "start_bbox_x2": start_bbox[2],
        "start_bbox_y2": start_bbox[3],
        "end_bbox_x1": end_bbox[0],
        "end_bbox_y1": end_bbox[1],
        "end_bbox_x2": end_bbox[2],
        "end_bbox_y2": end_bbox[3]
    }

def process_batch(batch_events: list) -> list:
    """处理一批数据，并调用 API 获取 embedding，返回 (parsed_event, embedding) 列表"""
    parsed_events = [preprocess_event(e) for e in batch_events]
    texts = [p["retrieval_text"] for p in parsed_events]
    
    try:
        # 批量调用百炼 API (注意: 百炼单次最多支持 25 条)
        embeddings = get_qwen_embedding(texts)
        return list(zip(parsed_events, embeddings))
    except Exception as e:
        print(f"⚠️ 批处理失败: {e}")
        return []

def ingest_data(json_path: str, db_path: str):
    """读取数据，进行预处理、embedding 批量并行生成，并写入 SQLite"""
    print(f"正在加载数据: {json_path}")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # 展平所有事件
    all_raw_events = []
    for video_data in data:
        all_raw_events.extend(video_data.get("events", []))
    
    total_events = len(all_raw_events)
    print(f"共发现 {total_events} 条事件记录。开始批量处理并入库...")
    
    # 百炼 API 的限制，单次最大支持 10 条
    BATCH_SIZE = 10
    batches = [all_raw_events[i:i + BATCH_SIZE] for i in range(0, total_events, BATCH_SIZE)]
    
    results = []
    # 使用线程池并发请求，加快速度
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(process_batch, batch): i for i, batch in enumerate(batches)}
        completed = 0
        for future in concurrent.futures.as_completed(futures):
            results.extend(future.result())
            completed += 1
            if completed % 10 == 0 or completed == len(batches):
                print(f"Embedding 进度: {completed}/{len(batches)} 批次 ({(completed*BATCH_SIZE)}/{total_events} 条)")
    
    print(f"成功获取 {len(results)} 条记录的 Embedding。准备写入 SQLite...")
    
    db = sqlite3.connect(db_path)
    db.enable_load_extension(True)
    sqlite_vec.load(db)
    db.enable_load_extension(False)
    cursor = db.cursor()
    
    count = 0
    # 开启事务加速写入
    cursor.execute("BEGIN TRANSACTION")
    for parsed, vec in results:
        # 3. 插入结构化数据
        cursor.execute("""
            INSERT INTO episodic_events (
                video_id, camera_id, track_id, global_id, start_time, end_time, duration,
                source_clip_start_sec, source_clip_end_sec, object_type, object_color_cn,
                scene_zone_cn, appearance_notes_cn, event_type, event_text_cn, event_summary_cn,
                normalized_state, keywords_json, retrieval_text,
                start_bbox_x1, start_bbox_y1, start_bbox_x2, start_bbox_y2,
                end_bbox_x1, end_bbox_y1, end_bbox_x2, end_bbox_y2
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            parsed["video_id"], parsed["camera_id"], parsed["track_id"], parsed["global_id"],
            parsed["start_time"], parsed["end_time"], parsed["duration"], parsed["source_clip_start_sec"],
            parsed["source_clip_end_sec"], parsed["object_type"], parsed["object_color_cn"],
            parsed["scene_zone_cn"], parsed["appearance_notes_cn"], parsed["event_type"],
            parsed["event_text_cn"], parsed["event_summary_cn"], parsed["normalized_state"],
            parsed["keywords_json"], parsed["retrieval_text"],
            parsed["start_bbox_x1"], parsed["start_bbox_y1"], parsed["start_bbox_x2"], parsed["start_bbox_y2"],
            parsed["end_bbox_x1"], parsed["end_bbox_y1"], parsed["end_bbox_x2"], parsed["end_bbox_y2"]
        ))
        
        event_id = cursor.lastrowid
        
        # 4. 插入向量数据 (使用相同的 rowid)
        cursor.execute(
            "INSERT INTO episodic_events_vec(rowid, embedding) VALUES (?, ?)",
            (event_id, serialize_f32(vec))
        )
        count += 1
            
    db.commit()
    db.close()
    print(f"✅ 入库完成！成功写入 {count} 条数据到 {db_path}")

if __name__ == "__main__":
    # 需要先执行 export DASHSCOPE_API_KEY="your_api_key"
    import sys
    import os
    from dotenv import load_dotenv
    # 修正路径以便可以直接运行
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
    
    # 尝试加载 .env
    try:
        load_dotenv()
    except Exception:
        pass
    
    mock_data_path = os.path.join(os.path.dirname(__file__), "../../../mvp_data/video_events_10k_mock.json")
    
    # 修改为目标数据库路径
    from pathlib import Path
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    db_path = str(BASE_DIR / "src" / "agent" / "memory" / "episodic" / "episodic_memory.db")
    
    if not os.environ.get("DASHSCOPE_API_KEY"):
        print("❌ 错误：请先设置环境变量 DASHSCOPE_API_KEY")
    else:
        ingest_data(mock_data_path, db_path)
