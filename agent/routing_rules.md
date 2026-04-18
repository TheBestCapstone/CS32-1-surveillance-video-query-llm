# Routing Rules (Default, Hit-Rate First)

## Supported Modes

- `hybrid_search`
- `pure_sql`

`parallel` and `video_vect` are disabled and unreachable.

## Rule Set

### RR-BASE-001: Structured Priority

- Structured score counts:
  - object detected: +1
  - color detected: +1
  - location detected: +1
  - explicit time phrase detected: +1
- If `structured_score >= 2` and event is not complex, route to `pure_sql`.

### RR-BASE-002: Semantic Priority

- If event is complex (e.g. "先...再...", "进入后离开"), route to `hybrid_search`.
- If location exists and semantic complexity exists, route to `hybrid_search`.

### RR-BASE-003: Safe Default

- Otherwise route to `pure_sql`.

## Output Contracts

- `tool_choice.mode` in `{hybrid_search, pure_sql}`
- `tool_choice.sql_needed/hybrid_needed` must be consistent with mode
- `tool_choice.sub_queries` keys only from `{sql, hybrid}`
- `routing_metrics` contains:
  - `route_reason_codes`
  - `route_confidence`

## Reflection Mandatory Validation

Before reflection final decision:

- mode validity
- needed flag consistency
- sub-query key validity
- retry upper bound
- performance guardrail (`candidate_limit <= 200` for hybrid)
