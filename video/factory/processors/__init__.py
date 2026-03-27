"""
Processors（按 README 拆分）：

- vision.py          — YOLO + 跟踪，逐帧检测
- analyzer.py        — 轨迹聚合、事件切片
- event_track_pipeline.py — 串联上述两步并写 JSON
- event_refine_langchain.py — LLM 精炼 CLI（load_dotenv）
- captioner.py       — 其它多模态描述（若有）

编排入口请用：video.factory.coordinator（run_video_to_events / run_refine_events）。
"""
