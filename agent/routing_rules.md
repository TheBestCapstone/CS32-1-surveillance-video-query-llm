# Routing Rules

## Default Runtime Semantics

The default runtime mode is `parallel_fusion`, not hard single-path routing.

- Both retrieval paths run:
  - `pure_sql`
  - `hybrid`
- Query classification outputs:
  - `structured`
  - `semantic`
  - `mixed`
- The label is used to bias fusion weights, not to disable one branch.

## Default Graph Contracts

- `self_query_node` runs before all retrieval nodes.
- `query_classification_node` produces `classification_result`.
- `parallel_retrieval_fusion_node` produces:
  - `sql_result`
  - `hybrid_result`
  - `merged_result`
  - `rerank_result`
  - `sql_debug.fusion_meta`
- `final_answer_node` produces a grounded draft answer.
- `summary_node` produces the final user-facing answer and appends minimal citations.

## Legacy Router Rules

The following hard route-selection rules apply only when
`AGENT_EXECUTION_MODE=legacy_router`.

- Supported legacy route modes:
  - `hybrid_search`
  - `pure_sql`
- `parallel` and `video_vect` are disabled and unreachable.

### RR-LEGACY-001: Structured Priority

- Structured evidence pushes routing toward `pure_sql`.

### RR-LEGACY-002: Semantic Priority

- Complex semantics or stronger semantic constraints push routing toward `hybrid_search`.

### RR-LEGACY-003: Safe Default

- If the LLM route decision cannot be trusted, fallback is controlled by environment configuration.

## Legacy Output Contracts

- `tool_choice.mode` in `{hybrid_search, pure_sql}`
- `tool_choice.sql_needed/hybrid_needed` must match `mode`
- `tool_choice.sub_queries` keys only from `{sql, hybrid}`
- `routing_metrics` should include route confidence and reason codes when available

## Validation Notes

- `reflection_node` validation is mainly meaningful in `legacy_router`.
- In the default graph, reliability comes from:
  - dual-path execution
  - branch timeout handling
  - degradation fallback
  - fusion guardrails such as `structured_zero_guardrail`
