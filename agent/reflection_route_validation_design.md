# Reflection Route Validation - Design

## Goal

Add a mandatory route-rule validity check in reflection stage. If validation fails, reflection must block progression and output explicit diagnostics.

## Placement

- Stage: `reflection_node` CoT engine
- Order:
  1. result_review
  2. error_location
  3. score_calculation
  4. strategy_generation
  5. strategy_validation
  6. quality_evaluation
  7. **route_rule_validation (new, mandatory)**
  8. final_decision

## Validation Rules

- `RR-001`: mode must be in `{hybrid_search, pure_sql}`
- `RR-002`: `sql_needed` and `hybrid_needed` cannot be both true
- `RR-003`: `mode=pure_sql` requires `sql_needed=true`
- `RR-004`: `mode=hybrid_search` requires `hybrid_needed=true`
- `RR-005`: sub-queries keys must be subset of `{sql, hybrid}`
- `RR-006`: `retry_count` cannot exceed `max_retries`
- `RR-007`: performance guardrail: hybrid `candidate_limit <= 200`

## Output Schema

- `reflection_result.validation_failed: bool`
- `reflection_result.violations: list`
  - `rule_id`
  - `conflict_type`
  - `detail`
  - `suggestion`
- `tool_error = "路由规则有效性验证失败"` when blocked

## Fail-Closed Policy

- Validation failure => `decision=validation_failed`
- `needs_retry=false`, `can_continue=false`
- Route after reflection forced to `final_answer_node` with failure metadata
