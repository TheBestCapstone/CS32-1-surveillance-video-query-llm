import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.append(str(BASE_DIR))

from src.retrieval.event_retriever import EventRetriever


def run_tests():
    try:
        from dotenv import load_dotenv

        load_dotenv(BASE_DIR / ".env")
    except Exception:
        pass

    if not os.environ.get("DASHSCOPE_API_KEY"):
        print("Error: set DASHSCOPE_API_KEY (Dashscope / Qwen embedding).")
        print("Example: export DASHSCOPE_API_KEY='your_key'")
        return

    print("DASHSCOPE_API_KEY OK; building retriever...")
    retriever = EventRetriever()

    print("\n" + "=" * 50)
    print("Scenario 1: structured search (no LLM)")
    print("=" * 50)

    print("\n--- 1.1 Long events (duration >= 100) ---")
    long_events = retriever.structured_search(min_duration=100.0, limit=3)
    for res in long_events:
        print(
            f"ID: {res['event_id']:<5} | duration: {res['duration']:.1f}s | summary: {res['event_summary']}"
        )

    print("\n--- 1.2 scene_zone=intersection, object_type=truck ---")
    truck_events = retriever.structured_search(scene_zone="intersection", object_type="truck", limit=3)
    for res in truck_events:
        print(
            f"ID: {res['event_id']:<5} | scene_zone: {res['scene_zone']} | summary: {res['event_summary']}"
        )

    print("\n--- 1.3 Timeline (video_id fixed, start_time >= 1000) ---")
    timeline_events = retriever.structured_search(
        video_id="VIRAT_S_000001_00_000000_000500.mp4",
        start_time_after=1000.0,
        limit=3,
    )
    for res in timeline_events:
        print(
            f"ID: {res['event_id']:<5} | start_time: {res['start_time']}s | summary: {res['event_summary']}"
        )

    print("\n" + "=" * 50)
    print("Scenario 2: semantic vector search")
    print("=" * 50)

    query_1 = "find a parked green car"
    print(f"\n--- query: '{query_1}' ---")
    results = retriever.hybrid_event_search(query_1, top_k=3)
    for idx, res in enumerate(results):
        print(f"[{idx+1}] distance: {res['distance']:.4f} | video: {res['video_id']}")
        print(f"    summary: {res['event_summary']}")

    print("\n" + "=" * 50)
    print("Scenario 3: hybrid search (filters + vector)")
    print("=" * 50)

    query_2 = "person running urgently"
    vid_filter = "VIRAT_S_000006_00_000000_000500.mp4"
    print("\n--- 3.1 Video-scoped hybrid ---")
    print(f"query: '{query_2}'")
    print(f"filters: object_type=person, video_id={vid_filter}")

    results = retriever.hybrid_event_search(
        query_2,
        top_k=3,
        object_type="person",
        video_id=vid_filter,
    )
    for idx, res in enumerate(results):
        print(f"[{idx+1}] distance: {res['distance']:.4f} | ID: {res['event_id']}")
        print(f"    summary: {res['event_summary']}")

    query_3 = "walking back and forth"
    zone_filter = "parking_entrance"
    print("\n--- 3.2 Zone-scoped hybrid ---")
    print(f"query: '{query_3}'")
    print(f"filters: scene_zone={zone_filter}")

    results = retriever.hybrid_event_search(
        query_3,
        top_k=3,
        scene_zone=zone_filter,
    )
    for idx, res in enumerate(results):
        print(f"[{idx+1}] distance: {res['distance']:.4f} | ID: {res['event_id']}")
        print(f"    summary: {res['event_summary']}")

    query_4 = "someone riding a bicycle past"
    vid_time_filter = "VIRAT_S_000001_00_000000_000500.mp4"
    start_t = 500.0
    end_t = 1500.0
    print("\n--- 3.3 Time-window hybrid ---")
    print(f"query: '{query_4}'")
    print(f"filters: video_id={vid_time_filter}, time in [{start_t}, {end_t}]s")

    results = retriever.hybrid_event_search(
        query_4,
        top_k=3,
        video_id=vid_time_filter,
        start_time_after=start_t,
        end_time_before=end_t,
    )
    for idx, res in enumerate(results):
        print(f"[{idx+1}] distance: {res['distance']:.4f} | ID: {res['event_id']}")
        print(f"    time: {res['start_time']}s - {res['end_time']}s")
        print(f"    summary: {res['event_summary']}")


if __name__ == "__main__":
    run_tests()
