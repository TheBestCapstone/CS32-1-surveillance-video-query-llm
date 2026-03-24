import json
import random
import os

MOCK_FILE_PATH = os.path.join(os.path.dirname(__file__), "video_events_mock.json")

# 读取原有的数据
try:
    with open(MOCK_FILE_PATH, "r", encoding="utf-8") as f:
        old_data = json.load(f)
        # 如果原来是单个字典，转换为列表
        if not isinstance(old_data, list):
            old_data = [old_data]
except Exception:
    old_data = []

# 定义一批新的视频ID
video_ids = [
    "VIRAT_S_010204_05_000856_000890.mp4",
    "VIRAT_S_050203_09_001000_001100.mp4",
    "VIRAT_S_040000_01_000000_000150.mp4",
    "VIRAT_S_060000_02_000000_000200.mp4",
    "VIRAT_S_010002_08_000345_000450.mp4"
]

colors = ["银灰", "黑", "白", "红", "蓝", "不确定", "黄", "绿"]
obj_types = [
    {"en": "car", "cn": "轿车"}, 
    {"en": "person", "cn": "人"}, 
    {"en": "bike", "cn": "自行车"}, 
    {"en": "truck", "cn": "卡车"}
]
scene_zones = ["停车位区域", "停车场入口附近", "马路对侧停车位", "停车场边缘步行区", "道路中央", "绿化带旁", "大楼入口", "十字路口"]

new_data = []

# 为每个视频生成随机的事件
for vid in video_ids:
    events = []
    num_events = random.randint(8, 20)  # 每个视频生成 8 到 20 个事件
    for i in range(num_events):
        start_t = round(random.uniform(0.0, 50.0), 2)
        end_t = round(start_t + random.uniform(2.0, 30.0), 2)
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
            "clip_end_sec": 120.0,
            "start_time": start_t,
            "end_time": end_t,
            "object_type": obj["en"],
            "object_color_cn": color,
            "appearance_notes_cn": notes,
            "scene_zone_cn": zone,
            "event_text_cn": f"{start_t}-{end_t}秒，{color}色{obj['cn']}在{zone}{notes}。",
            "keywords": [obj["en"], action, "mock_data"],
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
            "entity_hint": f"track_id={i+1}"
        }
        events.append(event)
        
    new_data.append({
        "video_id": vid,
        "events": sorted(events, key=lambda x: x["start_time"])
    })

# 合并新旧数据
final_data = old_data + new_data

# 写回 JSON 文件
with open(MOCK_FILE_PATH, "w", encoding="utf-8") as f:
    json.dump(final_data, f, ensure_ascii=False, indent=2)

print(f"✅ 成功将模拟数据扩展到了 {len(final_data)} 个视频，并保存到 {MOCK_FILE_PATH}")
