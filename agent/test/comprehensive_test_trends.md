# Comprehensive Test Trends

- Baseline:
```json
{
  "hybrid_p95_ms": 9316.0,
  "hybrid_recall_rate": 0.5,
  "sql_p95_ms": 55.0,
  "sql_avg_rows": 1.0,
  "baseline_time_unit_assumed": "seconds_converted_to_ms"
}
```
- Actual:
```json
{
  "pure_sql_avg_ms": 6567.61,
  "hybrid_search_avg_ms": 7184.06,
  "semantic_label_cases_with_zero_hybrid_rows": 0,
  "semantic_label_cases_total": 4,
  "pure_sql_vs_baseline_ratio": 119.4111,
  "hybrid_vs_baseline_ratio": 0.7712
}
```
- Notes:
- `semantic_label_cases_with_zero_hybrid_rows` is the primary indicator for whether semantic retrieval is truly active.
- `llm_final_output` is now emitted per case in both markdown and JSON reports for direct answer-level inspection.
