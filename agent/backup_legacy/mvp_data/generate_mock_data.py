import json
import random
import os

MOCK_FILE_PATH = os.path.join(os.path.dirname(__file__), "video_events_mock.json")

# Load existing mock file if present
try:
    with open(MOCK_FILE_PATH, "r", encoding="utf-8") as f:
        old_data = json.load(f)
        if not isinstance(old_data, list):
            old_data = [old_data]
except Exception:
    old_data = []

video_ids = [
    "VIRAT_S_010204_05_000856_000890.mp4",
    "VIRAT_S_050203_09_001000_001100.mp4",
    "VIRAT_S_040000_01_000000_000150.mp4",
    "VIRAT_S_060000_02_000000_000200.mp4",
    "VIRAT_S_010002_08_000345_000450.mp4",
]

colors = ["silver_gray", "black", "white", "red", "blue", "unknown", "yellow", "green"]
obj_types = [{"en": "car"}, {"en": "person"}, {"en": "bike"}, {"en": "truck"}]
scene_zones = [
    "parking_lot",
    "parking_entrance",
    "opposite_side_parking",
    "walkway_edge",
    "road_center",
    "green_belt",
    "building_entrance",
    "intersection",
]

new_data = []

for vid in video_ids:
    events = []
    num_events = random.randint(8, 20)
    for i in range(num_events):
        start_t = round(random.uniform(0.0, 50.0), 2)
        end_t = round(start_t + random.uniform(2.0, 30.0), 2)
        obj = random.choice(obj_types)
        color = random.choice(colors)
        zone = random.choice(scene_zones)

        if obj["en"] in ["car", "truck"]:
            action = random.choice(
                ["parked_static", "fast_enter", "slow_exit", "pass_by", "reverse"]
            )
            notes = (
                f"{action}, almost no displacement"
                if "parked" in action
                else f"{action} toward {zone}"
            )
        elif obj["en"] == "person":
            action = random.choice(
                ["brief_stop", "brisk_walk", "run", "loiter", "carry_item"]
            )
            notes = f"person in {zone}: {action}"
        else:
            action = random.choice(["ride_through", "parked"])
            notes = f"bike {action}"

        event = {
            "video_id": vid,
            "clip_start_sec": 0.0,
            "clip_end_sec": 120.0,
            "start_time": start_t,
            "end_time": end_t,
            "object_type": obj["en"],
            "object_color": color,
            "appearance_notes": notes,
            "scene_zone": zone,
            "event_text": f"{start_t}-{end_t}s: {color} {obj['en']} in {zone}; {notes}.",
            "keywords": [obj["en"], action, "mock_data"],
            "start_bbox_xyxy": [
                round(random.uniform(10, 800), 2),
                round(random.uniform(10, 600), 2),
                round(random.uniform(100, 1000), 2),
                round(random.uniform(100, 800), 2),
            ],
            "end_bbox_xyxy": [
                round(random.uniform(10, 800), 2),
                round(random.uniform(10, 600), 2),
                round(random.uniform(100, 1000), 2),
                round(random.uniform(100, 800), 2),
            ],
            "entity_hint": f"track_id={i+1}",
        }
        events.append(event)

    new_data.append({"video_id": vid, "events": sorted(events, key=lambda x: x["start_time"])})

final_data = old_data + new_data

with open(MOCK_FILE_PATH, "w", encoding="utf-8") as f:
    json.dump(final_data, f, ensure_ascii=False, indent=2)

print(f"Wrote {len(final_data)} video bundles to {MOCK_FILE_PATH}")
