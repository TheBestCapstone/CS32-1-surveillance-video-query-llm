import json
import sys
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[2]
AGENT_DIR = ROOT_DIR / "agent"
if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))

load_dotenv(ROOT_DIR / ".env")

from node.answer_node import final_answer_node  # noqa: E402
from node.retrieval_contracts import normalize_hybrid_rows, project_rows_to_parent_context  # noqa: E402
from node.types import default_chroma_collection, default_chroma_parent_collection, default_chroma_path  # noqa: E402
from tools.db_access import ChromaGateway  # noqa: E402


def run_smoke_test(query: str = "person standing still near baseline", limit: int = 6) -> dict:
    child_gateway = ChromaGateway(
        db_path=default_chroma_path(),
        collection_name=default_chroma_collection(),
    )
    child_rows = child_gateway.search(
        query=query,
        metadata_filters=[],
        alpha=0.7,
        limit=limit,
    )
    normalized_child_rows = normalize_hybrid_rows(child_rows)
    parent_rows = project_rows_to_parent_context(normalized_child_rows, limit=3)
    final_state = final_answer_node({"rerank_result": parent_rows}, config={}, store=None)
    final_answer = final_state.get("final_answer", "")

    video_ids = [str(row.get("video_id") or "") for row in parent_rows]
    unique_video_ids = sorted({video_id for video_id in video_ids if video_id})
    all_parent = all(str(row.get("_record_level") or "").lower() == "parent" for row in parent_rows)
    parent_collection_hits = [bool(row.get("_parent_collection_hit")) for row in parent_rows]

    result = {
        "query": query,
        "child_collection": default_chroma_collection(),
        "parent_collection": default_chroma_parent_collection(),
        "child_rows_count": len(normalized_child_rows),
        "parent_rows_count": len(parent_rows),
        "parent_video_ids": unique_video_ids,
        "all_parent_rows": all_parent,
        "parent_collection_hits": parent_collection_hits,
        "dedup_ok": len(unique_video_ids) == len(parent_rows),
        "final_answer_uses_parent_format": ("event_id=" not in str(final_answer)) and ("video=" in str(final_answer)),
        "top_parent_rows": [
            {
                "video_id": row.get("video_id"),
                "parent_hit_count": row.get("_parent_hit_count"),
                "parent_collection_hit": row.get("_parent_collection_hit"),
                "summary": row.get("event_summary_en"),
            }
            for row in parent_rows
        ],
        "final_answer": final_answer,
    }

    assert normalized_child_rows, "child retrieval returned no rows"
    assert parent_rows, "parent projection returned no rows"
    assert all_parent, "projected rows are not all parent-level"
    assert result["dedup_ok"], "parent rows are not deduplicated by video_id"
    assert all(parent_collection_hits), "some parent rows were not loaded from parent collection"
    assert result["final_answer_uses_parent_format"], "final answer still renders child-level event output"
    return result


if __name__ == "__main__":
    output = run_smoke_test()
    print(json.dumps(output, ensure_ascii=False, indent=2))
