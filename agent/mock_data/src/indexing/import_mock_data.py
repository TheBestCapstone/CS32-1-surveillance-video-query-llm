import json
import os
import lancedb
import sys
from pathlib import Path
import pyarrow as pa
from tqdm import tqdm

# Add capstone dir to path for embedder
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.append(str(BASE_DIR))

from video.indexing.embedder import get_qwen_embedding

def import_data():
    db_path = str(Path(__file__).resolve().parent.parent / "agent" / "memory" / "episodic" / "lancedb")
    db = lancedb.connect(db_path)
    
    if "episodic_events" not in db.table_names():
        print("表不存在，请先运行 db_setup.py")
        return
        
    tbl = db.open_table("episodic_events")
    
    mock_file = str(Path(__file__).resolve().parent.parent.parent.parent / "mvp_data" / "video_events_10k_mock.json")
    with open(mock_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    records = []
    event_id = 1
    
    print("准备数据并获取 embeddings...")
    for video in tqdm(data):
        vid = video["video_id"]
        for event in video["events"]:
            # 准备文本用于 embedding
            text = event["event_text_cn"]
            try:
                # 获取 embedding
                vector = get_qwen_embedding(text)
                
                # 构建记录
                record = {
                    "event_id": event_id,
                    "video_id": vid,
                    "camera_id": "",
                    "track_id": event.get("entity_hint", "").replace("track_id=", ""),
                    "global_id": "",
                    "start_time": event["start_time"],
                    "end_time": event["end_time"],
                    "duration": event["end_time"] - event["start_time"],
                    "source_clip_start_sec": event["clip_start_sec"],
                    "source_clip_end_sec": event["clip_end_sec"],
                    "object_type": event["object_type"],
                    "object_color_cn": event["object_color_cn"],
                    "scene_zone_cn": event["scene_zone_cn"],
                    "appearance_notes_cn": event["appearance_notes_cn"],
                    "event_type": "",
                    "event_text_cn": text,
                    "event_summary_cn": text,
                    "normalized_state": "",
                    "keywords_json": json.dumps(event["keywords"], ensure_ascii=False),
                    "retrieval_text": text,
                    "start_bbox_x1": event["start_bbox_xyxy"][0],
                    "start_bbox_y1": event["start_bbox_xyxy"][1],
                    "start_bbox_x2": event["start_bbox_xyxy"][2],
                    "start_bbox_y2": event["start_bbox_xyxy"][3],
                    "end_bbox_x1": event["end_bbox_xyxy"][0],
                    "end_bbox_y1": event["end_bbox_xyxy"][1],
                    "end_bbox_x2": event["end_bbox_xyxy"][2],
                    "end_bbox_y2": event["end_bbox_xyxy"][3],
                    "vector": vector
                }
                records.append(record)
                event_id += 1
            except Exception as e:
                print(f"Error getting embedding for text: {text}, Error: {e}")
                
    if records:
        print(f"正在插入 {len(records)} 条记录到 LanceDB...")
        tbl.add(records)
        print("✅ 导入完成！")
    else:
        print("没有成功处理的数据。")

if __name__ == "__main__":
    import_data()
