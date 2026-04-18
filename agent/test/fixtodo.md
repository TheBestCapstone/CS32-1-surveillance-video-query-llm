# Fix Todo

## P0
- Fix parallel graph state propagation: `query_classification_node` must persist `user_query` and reset ephemeral state for new queries.
- Fix hidden Hybrid failure handling: Chroma/embedding failures must populate `hybrid_error` and trigger degraded fallback.
- Re-run comprehensive test suite after the two fixes above.

## P1
- Improve structured filter extraction for location phrases such as `parking area`, `right side`, and similar zone aliases.
- Verify negative retrieval stays empty for absent object types such as `car`.
- Verify semantic cases produce real `hybrid_rows_count > 0` instead of SQL-only fallback.

## P2
- Tighten top-result relevance checks for `dark`, `parking`, and `bleachers` scenarios.
- Compare post-fix latency against the current comprehensive test baseline.
- Add explicit `llm_final_output` to comprehensive reports for answer-level inspection.
- Correct semantic trend metrics to count `semantic` label cases instead of all `hybrid_search` routes.
