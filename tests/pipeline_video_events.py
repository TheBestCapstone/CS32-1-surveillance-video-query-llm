"""
兼容入口：视频 → YOLO+跟踪 → 事件与 clip JSON。
推荐在代码中调用：video.factory.coordinator.run_video_to_events(...)
"""

from video.factory.processors.event_track_pipeline import main

if __name__ == "__main__":
    main()
