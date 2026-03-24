"""
兼容入口：LangChain 精炼 pipeline 产物。
推荐在代码中调用：video.factory.coordinator.run_refine_events(...)
或 video.factory.refinement_runner.run_refine_events_from_files(...)
"""

from video.factory.processors.event_refine_langchain import main

if __name__ == "__main__":
    main()
