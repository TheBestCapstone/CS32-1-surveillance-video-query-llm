# Comprehensive Test Trends

- Baseline:
```json
{}
```
- Actual:
```json
{
  "pure_sql_avg_ms": 9321.06,
  "hybrid_search_avg_ms": 5136.06,
  "semantic_label_cases_with_zero_hybrid_rows": 4,
  "semantic_label_cases_total": 4
}
```
- Notes:
- `semantic_label_cases_with_zero_hybrid_rows` is the primary indicator for whether semantic retrieval is truly active.
- `llm_final_output` is now emitted per case in both markdown and JSON reports for direct answer-level inspection.
