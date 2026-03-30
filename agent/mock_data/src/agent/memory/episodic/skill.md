# Episodic memory retrieval (tool skill)

How to wrap the SQLite + sqlite-vec episodic store as an agent tool, and when to call it.

## 1. When to use this store

Call the tool when the user asks about **past video content** that is backed by indexed events, for example:

- Factual questions over stored events (objects, colors, coarse scene region, time ranges).
- Filtered retrieval (by `video_id`, `object_type`, `scene_zone`, time window) plus optional semantic ranking.
- Follow-ups that need evidence rows (event id, time span, summary text).

## 2. Tool wrapper

Expose `EventRetriever` from `src.retrieval.event_retriever` (or `agent.retrieval.event_retriever` depending on your `PYTHONPATH`).

### Suggested tool function

```python
from src.retrieval.event_retriever import EventRetriever

episodic_retriever = EventRetriever()

def search_episodic_memory(
    query: str,
    object_type: str = None,
    video_id: str = None,
    top_k: int = 5,
) -> str:
    """
    Hybrid search: vector similarity over `retrieval_text` embeddings, optional SQL filters.

    Args:
        query: Natural-language query, e.g. "parked silver car near entrance"
        object_type: Optional filter, e.g. "car", "person", "bike", "truck"
        video_id: Optional scope, e.g. "VIRAT_S_000001_00_000000_000500.mp4"
        top_k: Max rows to return

    Returns:
        JSON string of ranked hits (subset of columns + distance).
    """
    results = episodic_retriever.hybrid_event_search(
        query_text=query,
        top_k=top_k,
        video_id=video_id,
        object_type=object_type,
    )

    if not results:
        return "[]"

    formatted_results = []
    for res in results:
        formatted_results.append({
            "event_id": res["event_id"],
            "video_id": res["video_id"],
            "time_range": f"{res['start_time']}s - {res['end_time']}s",
            "summary": res["event_summary"],
            "relevance_distance": round(res["distance"], 4),
        })

    import json
    return json.dumps(formatted_results, ensure_ascii=False, indent=2)
```

## 3. Agent workflow notes

1. **Router**: If the answer depends on indexed video events, route to this tool instead of guessing.
2. **Args**: Map user language to `query`, and extract `video_id` / `object_type` / `scene_zone` when clearly stated (structured filters are optional on `hybrid_event_search`).
3. **Read results**: Use returned `time_range` and `summary` as citations; keep answers consistent with stored text.
