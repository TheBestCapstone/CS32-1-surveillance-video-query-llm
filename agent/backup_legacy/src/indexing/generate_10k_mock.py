import json
import random
import os


def generate_large_mock_data(output_path: str, target_count: int = 10000):
    """Generate a large mock episodic-events dataset (English strings only)."""

    video_ids = [f"VIRAT_S_{i:06d}_00_000000_000500.mp4" for i in range(1, 51)]  # 50 synthetic videos
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

    events_per_video = target_count // len(video_ids)
    all_data = []

    print(f"Generating {target_count} mock events...")

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
                "clip_end_sec": 3600.0,
                "start_time": start_t,
                "end_time": end_t,
                "object_type": obj["en"],
                "object_color": color,
                "appearance_notes": notes,
                "scene_zone": zone,
                "event_text": (
                    f"{start_t}-{end_t}s: {color} {obj['en']} in {zone}; {notes}."
                ),
                "keywords": [obj["en"], action, "mock_large_data"],
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
                "entity_hint": f"track_id={global_track_id}",
            }
            events.append(event)
            global_track_id += 1

        all_data.append(
            {"video_id": vid, "events": sorted(events, key=lambda x: x["start_time"])}
        )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    print(f"Done: wrote {target_count} events to {output_path}")


if __name__ == "__main__":
    out_path = os.path.join(os.path.dirname(__file__), "../../../mvp_data/video_events_10k_mock.json")
    generate_large_mock_data(os.path.abspath(out_path), 10000)
