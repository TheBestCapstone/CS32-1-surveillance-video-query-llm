"""
测试/本地跑视频流水线时的便捷入口（与仓库根 pipeline_video_events.py 一致）。

在仓库根执行（把路径换成你的视频）:
  python tests/pipeline_video_events.py /path/to/video.mp4 -m n

视频路径：第一个位置参数 `video`；其它与 coordinator CLI 相同（--tracker、--out-dir 等）。
"""

from video.factory.coordinator import cli_run_video_events

if __name__ == "__main__":
    cli_run_video_events()
