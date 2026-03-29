from typing import Any, Dict, List


class SimpleRerankTool:
    def rerank(
        self,
        rows: List[Dict[str, Any]],
        event_list: List[str],
        meta_list: List[Dict[str, Any]],
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        ranked: List[Dict[str, Any]] = []
        event_terms = [term.strip() for term in event_list if isinstance(term, str) and term.strip()]
        color_values = [
            str(item.get("value", "")).strip()
            for item in meta_list
            if isinstance(item, dict) and item.get("field") == "object_color_cn"
        ]
        for row in rows:
            distance = float(row.get("_distance", 1e9))
            summary = str(row.get("event_summary_cn", ""))
            notes = str(row.get("appearance_notes_cn", ""))
            color = str(row.get("object_color_cn", ""))
            score = -distance
            for term in event_terms:
                if term in summary:
                    score += 0.2
                if term in notes:
                    score += 0.1
            for color_value in color_values:
                if color_value and color_value in color:
                    score += 0.2
            item = dict(row)
            item["rerank_score"] = round(score, 6)
            ranked.append(item)
        ranked.sort(key=lambda x: x.get("rerank_score", -1e9), reverse=True)
        return ranked[:top_k]


def create_rerank_tool(reranker: SimpleRerankTool | None = None):
    actual_reranker = reranker or SimpleRerankTool()

    def rerank_tool(
        rows: List[Dict[str, Any]],
        event_list: List[str],
        meta_list: List[Dict[str, Any]],
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        return actual_reranker.rerank(rows, event_list, meta_list, top_k)

    return rerank_tool


if __name__ == "__main__":
    tool = SimpleRerankTool()
    result = tool.rerank([{"event_id": 1, "_distance": 0.2}], ["进入"], [], top_k=5)
    print("rerank result:", result)