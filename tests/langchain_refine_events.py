"""
测试/本地跑精炼时的便捷入口。

在仓库根执行（路径换成你的 pipeline 产物）:
  python tests/langchain_refine_events.py \\
    --events pipeline_output/xxx_events.json \\
    --clips pipeline_output/xxx_clips.json

需设置 OPENAI_API_KEY；可先在本目录放 .env。
"""

from video.factory.coordinator import cli_run_refine_events

if __name__ == "__main__":
    cli_run_refine_events()
