from typing import Any

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.store.base import BaseStore

from .reflection_tool import do_reflection
from .rerank_tool import SimpleRerankTool
from .types import AgentState


def create_parallel_merge_node():
    reranker = SimpleRerankTool()

    def parallel_merge_node(state: AgentState, config: RunnableConfig, store: BaseStore) -> dict[str, Any]:
        del config, store
        hybrid = state.get("hybrid_result", [])
        sql = state.get("sql_result", [])
        video_vect = state.get("video_vect_result", [])
        merged: dict[Any, dict[str, Any]] = {}

        for row in hybrid:
            event_id = row.get("event_id")
            distance = float(row.get("_distance", 1e9))
            if event_id not in merged or distance < float(merged[event_id].get("_distance", 1e9)):
                row_copy = dict(row)
                row_copy["_source"] = "hybrid"
                merged[event_id] = row_copy

        for row in sql:
            event_id = row.get("event_id")
            distance = float(row.get("_distance", 1e9))
            if event_id not in merged or distance < float(merged[event_id].get("_distance", 1e9)):
                row_copy = dict(row)
                row_copy["_source"] = "sql"
                merged[event_id] = row_copy

        for row in video_vect:
            event_id = row.get("event_id")
            distance = float(row.get("_distance", 1e9))
            if event_id not in merged or distance < float(merged[event_id].get("_distance", 1e9)):
                row_copy = dict(row)
                row_copy["_source"] = "video_vect"
                merged[event_id] = row_copy

        final_merged = sorted(merged.values(), key=lambda x: float(x.get("_distance", 1e9)))

        reflection_result = do_reflection(
            rows=final_merged,
            event_list=state.get("event_list", []),
            meta_list=state.get("meta_list", []),
        )

        reranked = reranker.rerank(
            rows=final_merged,
            event_list=state.get("event_list", []),
            meta_list=state.get("meta_list", []),
            top_k=5,
        )

        total = len(final_merged)
        top_ids = [str(item.get("event_id")) for item in reranked[:3]]
        thought = f"并行合并完成: hybrid={len(hybrid)}, sql={len(sql)}, video_vect={len(video_vect)}, merged={total}, top_ids={top_ids}"

        return {
            "merged_result": final_merged,
            "rerank_result": reranked,
            "reflection_result": reflection_result,
            "thought": thought,
            "messages": [AIMessage(content=f"合并完成，共 {total} 条结果")],
        }

    return parallel_merge_node


if __name__ == "__main__":
    merge = create_parallel_merge_node()
    out = merge({
        "hybrid_result": [{"event_id": 1, "_distance": 0.2, "source": "hybrid"}],
        "sql_result": [{"event_id": 2, "_distance": 0.3, "source": "sql"}],
        "video_vect_result": [{"event_id": 3, "_distance": 0.1, "source": "video_vect"}],
        "event_list": ["进入"],
        "meta_list": [],
    }, {}, None)
    print(out["thought"])
    print("merged count:", len(out["merged_result"]))