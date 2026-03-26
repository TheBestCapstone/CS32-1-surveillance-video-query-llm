import json
import random
import os

def generate_large_mock_data(output_path: str, target_count: int = 10000):
    """生成大规模的模拟事件数据"""
    
    video_ids = [f"VIRAT_S_{i:06d}_00_000000_000500.mp4" for i in range(1, 51)]  # 50个视频
    colors = ["银灰", "黑", "白", "红", "蓝", "不确定", "黄", "绿"]
    obj_types = [
        {"en": "car", "cn": "轿车"}, 
        {"en": "person", "cn": "人"}, 
        {"en": "bike", "cn": "自行车"}, 
        {"en": "truck", "cn": "卡车"}
    ]
    scene_zones = ["停车位区域", "停车场入口附近", "马路对侧停车位", "停车场边缘步行区", "道路中央", "绿化带旁", "大楼入口", "十字路口"]
    
    events_per_video = target_count // len(video_ids)
    all_data = []
    
    print(f"开始生成 {target_count} 条模拟数据...")
    
    global_track_id = 1
    for vid in video_ids:
        events = []
        for _ in range(events_per_video):
            start_t = round(random.uniform(0.0, 3600.0), 2)
            end_t = round(start_t + random.uniform(2.0, 300.0), 2)
            obj = random.choice(obj_types)
            color = random.choice(colors)
            zone = random.choice(scene_zones)
            
            if obj["en"] in ["car", "truck"]:
                action = random.choice(["静止停放", "快速驶入", "缓慢驶出", "路过", "倒车"])
                notes = f"{action}，几乎无明显位移" if "静止" in action else f"{action}并进入{zone}"
            elif obj["en"] == "person":
                action = random.choice(["短暂停留", "快步走过", "奔跑", "徘徊", "搬运物品"])
                notes = f"行人在{zone}{action}"
            else:
                action = random.choice(["骑行通过", "停放"])
                notes = f"自行车{action}"

            event = {
                "video_id": vid,
                "clip_start_sec": 0.0,
                "clip_end_sec": 3600.0,
                "start_time": start_t,
                "end_time": end_t,
                "object_type": obj["en"],
                "object_color_cn": color,
                "appearance_notes_cn": notes,
                "scene_zone_cn": zone,
                "event_text_cn": f"{start_t}-{end_t}秒，{color}色{obj['cn']}在{zone}{notes}。",
                "keywords": [obj["en"], action, "mock_large_data"],
                "start_bbox_xyxy": [
                    round(random.uniform(10, 800), 2),
                    round(random.uniform(10, 600), 2),
                    round(random.uniform(100, 1000), 2),
                    round(random.uniform(100, 800), 2)
                ],
                "end_bbox_xyxy": [
                    round(random.uniform(10, 800), 2),
                    round(random.uniform(10, 600), 2),
                    round(random.uniform(100, 1000), 2),
                    round(random.uniform(100, 800), 2)
                ],
                "entity_hint": f"track_id={global_track_id}"
            }
            events.append(event)
            global_track_id += 1
            
        all_data.append({
            "video_id": vid,
            "events": sorted(events, key=lambda x: x["start_time"])
        })

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    print(f"✅ 成功生成了 {target_count} 条事件，保存到 {output_path}")

if __name__ == "__main__":
    out_path = os.path.join(os.path.dirname(__file__), "../../../mvp_data/video_events_10k_mock.json")
    generate_large_mock_data(os.path.abspath(out_path), 100)
