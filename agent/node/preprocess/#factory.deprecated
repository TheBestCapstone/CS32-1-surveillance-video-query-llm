import logging
from typing import Any

from langchain_core.runnables import RunnableConfig
from langgraph.store.base import BaseStore

from node.preprocess.base import SearchMode
from node.preprocess.hybrid import HybridSearchPreprocessor
from node.preprocess.pure_sql import PureSQLPreprocessor
from node.preprocess.video_vect import VideoVectPreprocessor
from node.types import AgentState

logger = logging.getLogger(__name__)


def create_hybrid_preprocess_node(llm: Any = None):
    preprocessor = HybridSearchPreprocessor(llm)
    def hybrid_preprocess(state: AgentState, config: RunnableConfig, store: BaseStore) -> dict[str, Any]:
        return preprocessor.preprocess(state, config, store)
    return hybrid_preprocess


def create_pure_sql_preprocess_node(llm: Any = None):
    preprocessor = PureSQLPreprocessor(llm)
    def pure_sql_preprocess(state: AgentState, config: RunnableConfig, store: BaseStore) -> dict[str, Any]:
        return preprocessor.preprocess(state, config, store)
    return pure_sql_preprocess


def create_video_vect_preprocess_node(llm: Any = None):
    preprocessor = VideoVectPreprocessor(llm)
    def video_vect_preprocess(state: AgentState, config: RunnableConfig, store: BaseStore) -> dict[str, Any]:
        return preprocessor.preprocess(state, config, store)
    return video_vect_preprocess


def run_tests():
    import logging
    logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')

    from node.preprocess.analyzer import QueryAnalyzer, SQLSanitizer

    print("\n=== Test 1: QueryAnalyzer - 检测直接语义模式 ===")
    analyzer = QueryAnalyzer()
    result1 = analyzer.analyze_query("车辆进入镜头")
    print(f"query: '车辆进入镜头' -> mode={result1['recommended_mode']}")
    assert result1["recommended_mode"] == SearchMode.DIRECT_SEMANTIC

    print("\n=== Test 2: QueryAnalyzer - 检测SQL过滤模式 ===")
    result2 = analyzer.analyze_query("红色车辆今天上午进入镜头")
    print(f"query: '红色车辆今天上午进入镜头' -> mode={result2['recommended_mode']}, has_color={result2['has_color']}")
    assert result2["recommended_mode"] == SearchMode.SQL_FILTER_SEMANTIC

    print("\n=== Test 3: SQLSanitizer - 注入防护 ===")
    sanitized = SQLSanitizer.sanitize_color("红色'; DROP TABLE users;--")
    print(f"sanitized: {sanitized}")
    assert sanitized is None or sanitized == "红色"

    print("\n=== Test 4: HybridSearchPreprocessor - 模式判断 ===")
    class FakeStructuredLLM:
        def invoke(self, messages, config=None):
            return {"rewritten_query": "车辆进入"}
    class FakeLLM:
        def with_structured_output(self, schema):
            return FakeStructuredLLM()

    preprocessor = HybridSearchPreprocessor(FakeLLM())
    out = preprocessor.preprocess({"user_query": "车辆进入", "tool_choice": {"mode": "hybrid"}}, {}, None)
    print(f"mode: {out['search_mode']}, event_list: {out['event_list']}")
    assert out["search_mode"] == SearchMode.DIRECT_SEMANTIC.value
    assert "车辆进入" in out["event_list"]

    print("\n=== Test 5: HybridSearchPreprocessor - SQL过滤模式 ===")
    class FakeStructuredLLMSQL:
        def invoke(self, messages, config=None):
            return {"event": "车辆进入", "color": "红色", "time": "今天", "move": True, "object": "车辆"}
    class FakeLLMSQL:
        def with_structured_output(self, schema):
            return FakeStructuredLLMSQL()
    preprocessor = HybridSearchPreprocessor(FakeLLMSQL())
    out = preprocessor.preprocess({"user_query": "红色车辆今天进入", "tool_choice": {"mode": "hybrid"}}, {}, None)
    print(f"mode: {out['search_mode']}, meta_count: {len(out['meta_list'])}")
    assert out["search_mode"] == SearchMode.SQL_FILTER_SEMANTIC.value
    assert len(out["meta_list"]) > 0

    print("\n=== Test 6: HybridSearchPreprocessor - 物体类型检测 ===")
    class FakeStructuredLLM2:
        def invoke(self, messages, config=None):
            return {"rewritten_query": "行人横穿"}
    class FakeLLM2:
        def with_structured_output(self, schema):
            return FakeStructuredLLM2()
    preprocessor = HybridSearchPreprocessor(FakeLLM2())
    out = preprocessor.preprocess({"user_query": "查找行人横穿马路的视频", "tool_choice": {"mode": "hybrid"}}, {}, None)
    print(f"mode: {out['search_mode']}, event: {out['event_list']}, meta_count: {len(out['meta_list'])}")
    assert out["search_mode"] == SearchMode.DIRECT_SEMANTIC.value
    assert "行人横穿" in out["event_list"]

    print("\n=== All tests passed! ===")


if __name__ == "__main__":
    run_tests()
