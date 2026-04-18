# Comprehensive Agent Test Report

- Generated At: `2026-04-19 04:43:59`
- Cases File: `/home/yangxp/Capstone/agent/test/comprehensive_cases_en.json`
- Data Profile:
```json
{
  "requested_path_exists": false,
  "actual_path": "/home/yangxp/Capstone/data/basketball_output",
  "actual_path_exists": true,
  "files": [
    "basketball_1_clips.json",
    "basketball_1_events.json",
    "basketball_1_events_vector_flat.json",
    "basketball_2_clips.json",
    "basketball_2_events.json",
    "basketball_2_events_vector_flat.json"
  ]
}
```
- Summary:
```json
{
  "total_cases": 11,
  "passed": 11,
  "soft_failed": 0,
  "failed": 0,
  "pass_rate": 1.0,
  "soft_fail_rate": 0.0,
  "hard_fail_rate": 0.0,
  "iterations_total": 15,
  "overall_avg_ms": 7027.43,
  "overall_p95_ms": 8471.5,
  "failure_categories": {
    "runtime_exception": 0,
    "route_mismatch": 0,
    "label_mismatch": 0,
    "tool_error": 0,
    "semantic_backend_failure": 0,
    "keyword_mismatch": 0,
    "result_size_violation": 0,
    "hybrid_health_inconsistency": 0,
    "citation_missing": 0,
    "grounding_gap": 0,
    "trace_gap": 0,
    "routing_metrics_missing": 0
  },
  "dimension_summary": {
    "functional": {
      "PASS": 7,
      "SOFT_FAIL": 0,
      "FAIL": 0
    },
    "routing": {
      "PASS": 3,
      "SOFT_FAIL": 0,
      "FAIL": 0
    },
    "filtering": {
      "PASS": 2,
      "SOFT_FAIL": 0,
      "FAIL": 0
    },
    "semantic": {
      "PASS": 4,
      "SOFT_FAIL": 0,
      "FAIL": 0
    },
    "behavior": {
      "PASS": 1,
      "SOFT_FAIL": 0,
      "FAIL": 0
    },
    "negative": {
      "PASS": 1,
      "SOFT_FAIL": 0,
      "FAIL": 0
    },
    "boundary": {
      "PASS": 2,
      "SOFT_FAIL": 0,
      "FAIL": 0
    },
    "resilience": {
      "PASS": 2,
      "SOFT_FAIL": 0,
      "FAIL": 0
    },
    "performance": {
      "PASS": 2,
      "SOFT_FAIL": 0,
      "FAIL": 0
    }
  },
  "priority_summary": {
    "P0": {
      "PASS": 5,
      "SOFT_FAIL": 0,
      "FAIL": 0
    },
    "P1": {
      "PASS": 6,
      "SOFT_FAIL": 0,
      "FAIL": 0
    }
  },
  "metrics_summary": {
    "sql_branch_non_empty_rate": 0.9091,
    "hybrid_branch_non_empty_rate": 0.9091,
    "dual_branch_non_empty_rate": 0.8182,
    "degraded_rate": 0.0909,
    "sql_error_rate": 0.0,
    "hybrid_error_rate": 0.0,
    "citation_coverage_rate": 1.0,
    "grounding_coverage_rate": 1.0,
    "trace_coverage_rate": 1.0,
    "routing_metrics_coverage_rate": 1.0,
    "search_config_coverage_rate": 1.0,
    "sql_plan_coverage_rate": 1.0
  }
}
```
- Metrics Summary:
```json
{
  "sql_branch_non_empty_rate": 0.9091,
  "hybrid_branch_non_empty_rate": 0.9091,
  "dual_branch_non_empty_rate": 0.8182,
  "degraded_rate": 0.0909,
  "sql_error_rate": 0.0,
  "hybrid_error_rate": 0.0,
  "citation_coverage_rate": 1.0,
  "grounding_coverage_rate": 1.0,
  "trace_coverage_rate": 1.0,
  "routing_metrics_coverage_rate": 1.0,
  "search_config_coverage_rate": 1.0,
  "sql_plan_coverage_rate": 1.0
}
```
- Trends:
```json
{
  "baseline": {
    "hybrid_p95_ms": 9316.0,
    "hybrid_recall_rate": 0.5,
    "sql_p95_ms": 55.0,
    "sql_avg_rows": 1.0,
    "baseline_time_unit_assumed": "seconds_converted_to_ms"
  },
  "actual": {
    "pure_sql_avg_ms": 6567.61,
    "hybrid_search_avg_ms": 7184.06,
    "semantic_label_cases_with_zero_hybrid_rows": 0,
    "semantic_label_cases_total": 4,
    "pure_sql_vs_baseline_ratio": 119.4111,
    "hybrid_vs_baseline_ratio": 0.7712
  }
}
```

## FNC_SQL_001
- Suite: `core_regression`
- Priority: `P0`
- Dimensions: `functional, routing`
- Description: Structured existence query should route to pure_sql and return SQL rows.
- Query: `Did you see any person in the database?`
- Status: `PASS`
- Avg Latency: `7548.73 ms`
- P95 Latency: `7548.73 ms`
- Node Trace:
```json
[
  "self_query_node",
  "query_classification_node",
  "parallel_retrieval_fusion_node",
  "final_answer_node",
  "summary_node"
]
```
- Routing Metrics:
```json
{
  "execution_mode": "parallel_fusion",
  "label": "structured",
  "query": "Did you see any person in the database",
  "sql_rows_count": 27,
  "hybrid_rows_count": 26,
  "sql_error": null,
  "hybrid_error": null
}
```
- Search Config:
```json
{
  "candidate_limit": 80,
  "top_k_per_event": 20,
  "rerank_top_k": 5,
  "distance_threshold": null,
  "hybrid_alpha": 0.7,
  "hybrid_fallback_alpha": 0.9,
  "hybrid_limit": 50,
  "sql_limit": 80
}
```
- SQL Plan:
```json
{
  "table": "episodic_events",
  "fields": [
    "event_id",
    "video_id",
    "track_id",
    "start_time",
    "end_time",
    "object_type",
    "object_color_en",
    "scene_zone_en",
    "appearance_notes_en",
    "event_summary_en"
  ],
  "where": [
    {
      "field": "object_type",
      "op": "=",
      "value": "person"
    }
  ],
  "order_by": "start_time ASC",
  "limit": 80
}
```
- Self Query Result:
```json
{
  "rewritten_query": "Did you see any person in the database",
  "user_need": "Retrieve basketball video results that satisfy: Did you see any person in the database",
  "intent_label": "structured",
  "retrieval_focus": "structured",
  "key_constraints": [
    "did",
    "you",
    "see",
    "any",
    "person",
    "in"
  ],
  "ambiguities": [],
  "reasoning_summary": "Fast-path preprocessing kept the original meaning and only normalized surface noise.",
  "confidence": 0.8,
  "original_user_query": "Did you see any person in the database?"
}
```
- Raw Final Answer:
```json
{
  "raw_final_answer": "Retrieval complete. Most relevant results:\n[1] event_id=1 | video=basketball_1.mp4 | distance=0.0 | summary=From 0.0s to 61.2s, a person with unknown color stays mostly still near the left baseline/bench area.\n[2] event_id=2 | video=basketball_1.mp4 | distance=0.0 | summary=From 0.0s to 16.1s, a person with unknown color remains mostly still near the left-center baseline area.\n[3] event_id=3 | video=basketball_1.mp4 | distance=0.0 | summary=From 0.0s to 12.0s, a person with unknown color remains mostly still near the left-center baseline area.\n[4] event_id=4 | video=basketball_1.mp4 | distance=0.0 | summary=From 0.0s to 143.1s, a person with unknown color stays mostly still near the lower-left court/bench area.\n[5] event_id=5 | video=basketball_1.mp4 | distance=0.0 | summary=From 0.0s to 17.5s, a person with unknown color remains mostly still near the left-center baseline area."
}
```
- LLM Final Output:
```json
{
  "llm_final_output": "Yes, multiple people were detected in the video. In \"basketball_1.mp4,\" individuals (with unknown clothing colors) were seen staying mostly still near the left baseline, left-center baseline, and lower-left court or bench areas, with appearances ranging from 12 to over 140 seconds.\nSources: [sql] basketball_1.mp4 | event_id=1 | 0.0-61.208333333333336; [sql] basketball_1.mp4 | event_id=2 | 0.0-16.083333333333332; [sql] basketball_1.mp4 | event_id=3 | 0.0-12.041666666666666"
}
```
- Assertions:
```json
[
  {
    "name": "no_runtime_exception",
    "passed": true,
    "actual": [],
    "expected": null,
    "severity": "hard"
  },
  {
    "name": "label_matches",
    "passed": true,
    "actual": "structured",
    "expected": "structured",
    "severity": "hard"
  },
  {
    "name": "route_in_expected",
    "passed": true,
    "actual": "pure_sql",
    "expected": [
      "pure_sql"
    ],
    "severity": "hard"
  },
  {
    "name": "final_answer_present",
    "passed": true,
    "actual": "Yes, multiple people were detected in the video. In \"basketball_1.mp4,\" individuals (with unknown clothing colors) were seen staying mostly still near the left baseline, left-center baseline, and lower-left court or bench areas, with appearances ranging from 12 to over 140 seconds.\nSources: [sql] basketball_1.mp4 | event_id=1 | 0.0-61.208333333333336; [sql] basketball_1.mp4 | event_id=2 | 0.0-16.083333333333332; [sql] basketball_1.mp4 | event_id=3 | 0.0-12.041666666666666",
    "expected": "non-empty string",
    "severity": "hard"
  },
  {
    "name": "citation_present",
    "passed": true,
    "actual": "Yes, multiple people were detected in the video. In \"basketball_1.mp4,\" individuals (with unknown clothing colors) were seen staying mostly still near the left baseline, left-center baseline, and lower-left court or bench areas, with appearances ranging from 12 to over 140 seconds.\nSources: [sql] basketball_1.mp4 | event_id=1 | 0.0-61.208333333333336; [sql] basketball_1.mp4 | event_id=2 | 0.0-16.083333333333332; [sql] basketball_1.mp4 | event_id=3 | 0.0-12.041666666666666",
    "expected": "final answer contains Sources:",
    "severity": "soft"
  },
  {
    "name": "grounding_coverage",
    "passed": true,
    "actual": {
      "summary": "Yes, multiple people were detected in the video. In \"basketball_1.mp4,\" individuals (with unknown clothing colors) were seen staying mostly still near the left baseline, left-center baseline, and lower-left court or bench areas, with appearances ranging from 12 to over 140 seconds.",
      "style": "llm_summary",
      "confidence": 0.8,
      "citations": [
        {
          "source_type": "sql",
          "video_id": "basketball_1.mp4",
          "event_id": 1,
          "start_time": 0.0,
          "end_time": 61.208333333333336
        },
        {
          "source_type": "sql",
          "video_id": "basketball_1.mp4",
          "event_id": 2,
          "start_time": 0.0,
          "end_time": 16.083333333333332
        },
        {
          "source_type": "sql",
          "video_id": "basketball_1.mp4",
          "event_id": 3,
          "start_time": 0.0,
          "end_time": 12.041666666666666
        }
      ]
    },
    "expected": "summary_result.citations is non-empty",
    "severity": "soft"
  },
  {
    "name": "rewritten_query_present",
    "passed": true,
    "actual": "Did you see any person in the database",
    "expected": "non-empty rewritten query",
    "severity": "soft"
  },
  {
    "name": "user_need_identified",
    "passed": true,
    "actual": {
      "rewritten_query": "Did you see any person in the database",
      "user_need": "Retrieve basketball video results that satisfy: Did you see any person in the database",
      "intent_label": "structured",
      "retrieval_focus": "structured",
      "key_constraints": [
        "did",
        "you",
        "see",
        "any",
        "person",
        "in"
      ],
      "ambiguities": [],
      "reasoning_summary": "Fast-path preprocessing kept the original meaning and only normalized surface noise.",
      "confidence": 0.8,
      "original_user_query": "Did you see any person in the database?"
    },
    "expected": "structured self-query result with user_need",
    "severity": "soft"
  },
  {
    "name": "trace_has_required_nodes",
    "passed": true,
    "actual": [
      "self_query_node",
      "query_classification_node",
      "parallel_retrieval_fusion_node",
      "final_answer_node",
      "summary_node"
    ],
    "expected": [
      "self_query_node",
      "final_answer_node",
      "summary_node"
    ],
    "severity": "soft"
  },
  {
    "name": "routing_metrics_present",
    "passed": true,
    "actual": {
      "execution_mode": "parallel_fusion",
      "label": "structured",
      "query": "Did you see any person in the database",
      "sql_rows_count": 27,
      "hybrid_rows_count": 26,
      "sql_error": null,
      "hybrid_error": null
    },
    "expected": "non-empty routing_metrics",
    "severity": "soft"
  },
  {
    "name": "search_config_present",
    "passed": true,
    "actual": {
      "candidate_limit": 80,
      "top_k_per_event": 20,
      "rerank_top_k": 5,
      "distance_threshold": null,
      "hybrid_alpha": 0.7,
      "hybrid_fallback_alpha": 0.9,
      "hybrid_limit": 50,
      "sql_limit": 80
    },
    "expected": "non-empty search_config",
    "severity": "soft"
  },
  {
    "name": "sql_plan_present",
    "passed": true,
    "actual": {
      "table": "episodic_events",
      "fields": [
        "event_id",
        "video_id",
        "track_id",
        "start_time",
        "end_time",
        "object_type",
        "object_color_en",
        "scene_zone_en",
        "appearance_notes_en",
        "event_summary_en"
      ],
      "where": [
        {
          "field": "object_type",
          "op": "=",
          "value": "person"
        }
      ],
      "order_by": "start_time ASC",
      "limit": 80
    },
    "expected": "non-empty sql_plan",
    "severity": "soft"
  },
  {
    "name": "no_tool_error",
    "passed": true,
    "actual": null,
    "expected": null,
    "severity": "soft"
  },
  {
    "name": "min_results",
    "passed": true,
    "actual": 50,
    "expected": 1,
    "severity": "hard"
  },
  {
    "name": "min_sql_rows",
    "passed": true,
    "actual": 27,
    "expected": 1,
    "severity": "hard"
  },
  {
    "name": "top_field_video_id",
    "passed": true,
    "actual": [
      "basketball_1.mp4",
      "basketball_1.mp4",
      "basketball_1.mp4",
      "basketball_1.mp4",
      "basketball_1.mp4"
    ],
    "expected": "non-empty",
    "severity": "soft"
  },
  {
    "name": "top_field_event_text",
    "passed": true,
    "actual": [
      "From 0.0s to 61.2s, a person with unknown color stays mostly still near the left baseline/bench area.",
      "From 0.0s to 16.1s, a person with unknown color remains mostly still near the left-center baseline area.",
      "From 0.0s to 12.0s, a person with unknown color remains mostly still near the left-center baseline area.",
      "From 0.0s to 143.1s, a person with unknown color stays mostly still near the lower-left court/bench area.",
      "From 0.0s to 17.5s, a person with unknown color remains mostly still near the left-center baseline area."
    ],
    "expected": "non-empty",
    "severity": "soft"
  }
]
```
- Last Iteration:
```json
{
  "elapsed_ms": 7548.73,
  "route_mode": "pure_sql",
  "label": "structured",
  "llm_final_output": "Yes, multiple people were detected in the video. In \"basketball_1.mp4,\" individuals (with unknown clothing colors) were seen staying mostly still near the left baseline, left-center baseline, and lower-left court or bench areas, with appearances ranging from 12 to over 140 seconds.\nSources: [sql] basketball_1.mp4 | event_id=1 | 0.0-61.208333333333336; [sql] basketball_1.mp4 | event_id=2 | 0.0-16.083333333333332; [sql] basketball_1.mp4 | event_id=3 | 0.0-12.041666666666666",
  "raw_final_answer": "Retrieval complete. Most relevant results:\n[1] event_id=1 | video=basketball_1.mp4 | distance=0.0 | summary=From 0.0s to 61.2s, a person with unknown color stays mostly still near the left baseline/bench area.\n[2] event_id=2 | video=basketball_1.mp4 | distance=0.0 | summary=From 0.0s to 16.1s, a person with unknown color remains mostly still near the left-center baseline area.\n[3] event_id=3 | video=basketball_1.mp4 | distance=0.0 | summary=From 0.0s to 12.0s, a person with unknown color remains mostly still near the left-center baseline area.\n[4] event_id=4 | video=basketball_1.mp4 | distance=0.0 | summary=From 0.0s to 143.1s, a person with unknown color stays mostly still near the lower-left court/bench area.\n[5] event_id=5 | video=basketball_1.mp4 | distance=0.0 | summary=From 0.0s to 17.5s, a person with unknown color remains mostly still near the left-center baseline area.",
  "rewritten_query": "Did you see any person in the database",
  "original_user_query": "Did you see any person in the database?",
  "self_query_result": {
    "rewritten_query": "Did you see any person in the database",
    "user_need": "Retrieve basketball video results that satisfy: Did you see any person in the database",
    "intent_label": "structured",
    "retrieval_focus": "structured",
    "key_constraints": [
      "did",
      "you",
      "see",
      "any",
      "person",
      "in"
    ],
    "ambiguities": [],
    "reasoning_summary": "Fast-path preprocessing kept the original meaning and only normalized surface noise.",
    "confidence": 0.8,
    "original_user_query": "Did you see any person in the database?"
  },
  "summary_result": {
    "summary": "Yes, multiple people were detected in the video. In \"basketball_1.mp4,\" individuals (with unknown clothing colors) were seen staying mostly still near the left baseline, left-center baseline, and lower-left court or bench areas, with appearances ranging from 12 to over 140 seconds.",
    "style": "llm_summary",
    "confidence": 0.8,
    "citations": [
      {
        "source_type": "sql",
        "video_id": "basketball_1.mp4",
        "event_id": 1,
        "start_time": 0.0,
        "end_time": 61.208333333333336
      },
      {
        "source_type": "sql",
        "video_id": "basketball_1.mp4",
        "event_id": 2,
        "start_time": 0.0,
        "end_time": 16.083333333333332
      },
      {
        "source_type": "sql",
        "video_id": "basketball_1.mp4",
        "event_id": 3,
        "start_time": 0.0,
        "end_time": 12.041666666666666
      }
    ]
  },
  "routing_metrics": {
    "execution_mode": "parallel_fusion",
    "label": "structured",
    "query": "Did you see any person in the database",
    "sql_rows_count": 27,
    "hybrid_rows_count": 26,
    "sql_error": null,
    "hybrid_error": null
  },
  "search_config": {
    "candidate_limit": 80,
    "top_k_per_event": 20,
    "rerank_top_k": 5,
    "distance_threshold": null,
    "hybrid_alpha": 0.7,
    "hybrid_fallback_alpha": 0.9,
    "hybrid_limit": 50,
    "sql_limit": 80
  },
  "sql_plan": {
    "table": "episodic_events",
    "fields": [
      "event_id",
      "video_id",
      "track_id",
      "start_time",
      "end_time",
      "object_type",
      "object_color_en",
      "scene_zone_en",
      "appearance_notes_en",
      "event_summary_en"
    ],
    "where": [
      {
        "field": "object_type",
        "op": "=",
        "value": "person"
      }
    ],
    "order_by": "start_time ASC",
    "limit": 80
  },
  "node_trace": [
    "self_query_node",
    "query_classification_node",
    "parallel_retrieval_fusion_node",
    "final_answer_node",
    "summary_node"
  ],
  "final_answer": "Yes, multiple people were detected in the video. In \"basketball_1.mp4,\" individuals (with unknown clothing colors) were seen staying mostly still near the left baseline, left-center baseline, and lower-left court or bench areas, with appearances ranging from 12 to over 140 seconds.\nSources: [sql] basketball_1.mp4 | event_id=1 | 0.0-61.208333333333336; [sql] basketball_1.mp4 | event_id=2 | 0.0-16.083333333333332; [sql] basketball_1.mp4 | event_id=3 | 0.0-12.041666666666666",
  "tool_error": null,
  "error": null,
  "current_node": "summary_node",
  "top5": [
    {
      "event_id": 1,
      "video_id": "basketball_1.mp4",
      "event_text": "From 0.0s to 61.2s, a person with unknown color stays mostly still near the left baseline/bench area.",
      "distance": 0.0
    },
    {
      "event_id": 2,
      "video_id": "basketball_1.mp4",
      "event_text": "From 0.0s to 16.1s, a person with unknown color remains mostly still near the left-center baseline area.",
      "distance": 0.0
    },
    {
      "event_id": 3,
      "video_id": "basketball_1.mp4",
      "event_text": "From 0.0s to 12.0s, a person with unknown color remains mostly still near the left-center baseline area.",
      "distance": 0.0
    },
    {
      "event_id": 4,
      "video_id": "basketball_1.mp4",
      "event_text": "From 0.0s to 143.1s, a person with unknown color stays mostly still near the lower-left court/bench area.",
      "distance": 0.0
    },
    {
      "event_id": 5,
      "video_id": "basketball_1.mp4",
      "event_text": "From 0.0s to 17.5s, a person with unknown color remains mostly still near the left-center baseline area.",
      "distance": 0.0
    }
  ],
  "merged_count": 50,
  "sql_rows_count": 27,
  "hybrid_rows_count": 26,
  "degraded": false,
  "hybrid_summary": "Hybrid direct retrieval complete",
  "sql_summary": "SQL direct retrieval rows=27",
  "hybrid_error": null,
  "sql_error": null,
  "sql_debug": {
    "duration": 1.574371015001816,
    "sql_summary": "SQL direct retrieval rows=27",
    "hybrid_summary": "Hybrid direct retrieval complete",
    "sql_error": null,
    "hybrid_error": null,
    "fusion_meta": {
      "label": "structured",
      "weights": {
        "sql": 0.8,
        "hybrid": 0.2
      },
      "rrf_k": 60.0,
      "sql_count": 27,
      "hybrid_count": 26,
      "fused_count": 50,
      "method": "weighted_rrf",
      "degraded": false
    }
  }
}
```

## FNC_SQL_002
- Suite: `core_regression`
- Priority: `P0`
- Dimensions: `functional, filtering`
- Description: Color filtering should surface dark-clothed results for a structured query.
- Query: `Show me dark-clothed persons.`
- Status: `PASS`
- Avg Latency: `8221.7 ms`
- P95 Latency: `8221.7 ms`
- Node Trace:
```json
[
  "self_query_node",
  "query_classification_node",
  "parallel_retrieval_fusion_node",
  "final_answer_node",
  "summary_node"
]
```
- Routing Metrics:
```json
{
  "execution_mode": "parallel_fusion",
  "label": "structured",
  "query": "Show me dark-clothed persons",
  "sql_rows_count": 6,
  "hybrid_rows_count": 26,
  "sql_error": null,
  "hybrid_error": null
}
```
- Search Config:
```json
{
  "candidate_limit": 80,
  "top_k_per_event": 20,
  "rerank_top_k": 5,
  "distance_threshold": null,
  "hybrid_alpha": 0.7,
  "hybrid_fallback_alpha": 0.9,
  "hybrid_limit": 50,
  "sql_limit": 80
}
```
- SQL Plan:
```json
{
  "table": "episodic_events",
  "fields": [
    "event_id",
    "video_id",
    "track_id",
    "start_time",
    "end_time",
    "object_type",
    "object_color_en",
    "scene_zone_en",
    "appearance_notes_en",
    "event_summary_en"
  ],
  "where": [
    {
      "field": "object_type",
      "op": "=",
      "value": "person"
    },
    {
      "field": "object_color_en",
      "op": "=",
      "value": "dark"
    }
  ],
  "order_by": "start_time ASC",
  "limit": 80
}
```
- Self Query Result:
```json
{
  "rewritten_query": "Show me dark-clothed persons",
  "user_need": "Retrieve basketball video results that satisfy: Show me dark-clothed persons",
  "intent_label": "structured",
  "retrieval_focus": "structured",
  "key_constraints": [
    "show",
    "me",
    "dark",
    "clothed",
    "persons"
  ],
  "ambiguities": [],
  "reasoning_summary": "Fast-path preprocessing kept the original meaning and only normalized surface noise.",
  "confidence": 0.8,
  "original_user_query": "Show me dark-clothed persons."
}
```
- Raw Final Answer:
```json
{
  "raw_final_answer": "Retrieval complete. Most relevant results:\n[1] event_id=22 | video=basketball_2.mp4 | distance=0.0 | summary=From 0.00s to 30.84s, a dark-clothed person stands near the left bleachers with little motion.\n[2] event_id=27 | video=basketball_2.mp4 | distance=0.0 | summary=From 0.00s to 9.96s, a dark-clothed person stands near the left side with little motion.\n[3] event_id=23 | video=basketball_2.mp4 | distance=0.0 | summary=From 40.60s to 44.90s, a dark-clothed person moves across the center-right court area.\n[4] event_id=25 | video=basketball_2.mp4 | distance=0.0 | summary=From 41.50s to 46.85s, a dark-clothed person moves near the left-center court area.\n[5] event_id=26 | video=basketball_2.mp4 | distance=0.0 | summary=From 46.15s to 50.45s, a dark-clothed person moves near the upper-middle court area."
}
```
- LLM Final Output:
```json
{
  "llm_final_output": "In the video *basketball_2.mp4*, several dark-clothed individuals appear: one stands still near the left bleachers (0–30.8s), another near the left side (0–10s), and others move across the court between 40.6s and 50.5s in areas like center-right, left-center, and upper-middle.\nSources: [sql] basketball_2.mp4 | event_id=22 | 0.0-30.84; [sql] basketball_2.mp4 | event_id=27 | 0.0-9.96; [sql] basketball_2.mp4 | event_id=23 | 40.6-44.9"
}
```
- Assertions:
```json
[
  {
    "name": "no_runtime_exception",
    "passed": true,
    "actual": [],
    "expected": null,
    "severity": "hard"
  },
  {
    "name": "label_matches",
    "passed": true,
    "actual": "structured",
    "expected": "structured",
    "severity": "hard"
  },
  {
    "name": "route_in_expected",
    "passed": true,
    "actual": "pure_sql",
    "expected": [
      "pure_sql"
    ],
    "severity": "hard"
  },
  {
    "name": "final_answer_present",
    "passed": true,
    "actual": "In the video *basketball_2.mp4*, several dark-clothed individuals appear: one stands still near the left bleachers (0–30.8s), another near the left side (0–10s), and others move across the court between 40.6s and 50.5s in areas like center-right, left-center, and upper-middle.\nSources: [sql] basketball_2.mp4 | event_id=22 | 0.0-30.84; [sql] basketball_2.mp4 | event_id=27 | 0.0-9.96; [sql] basketball_2.mp4 | event_id=23 | 40.6-44.9",
    "expected": "non-empty string",
    "severity": "hard"
  },
  {
    "name": "citation_present",
    "passed": true,
    "actual": "In the video *basketball_2.mp4*, several dark-clothed individuals appear: one stands still near the left bleachers (0–30.8s), another near the left side (0–10s), and others move across the court between 40.6s and 50.5s in areas like center-right, left-center, and upper-middle.\nSources: [sql] basketball_2.mp4 | event_id=22 | 0.0-30.84; [sql] basketball_2.mp4 | event_id=27 | 0.0-9.96; [sql] basketball_2.mp4 | event_id=23 | 40.6-44.9",
    "expected": "final answer contains Sources:",
    "severity": "soft"
  },
  {
    "name": "grounding_coverage",
    "passed": true,
    "actual": {
      "summary": "In the video *basketball_2.mp4*, several dark-clothed individuals appear: one stands still near the left bleachers (0–30.8s), another near the left side (0–10s), and others move across the court between 40.6s and 50.5s in areas like center-right, left-center, and upper-middle.",
      "style": "llm_summary",
      "confidence": 0.8,
      "citations": [
        {
          "source_type": "sql",
          "video_id": "basketball_2.mp4",
          "event_id": 22,
          "start_time": 0.0,
          "end_time": 30.84
        },
        {
          "source_type": "sql",
          "video_id": "basketball_2.mp4",
          "event_id": 27,
          "start_time": 0.0,
          "end_time": 9.96
        },
        {
          "source_type": "sql",
          "video_id": "basketball_2.mp4",
          "event_id": 23,
          "start_time": 40.6,
          "end_time": 44.9
        }
      ]
    },
    "expected": "summary_result.citations is non-empty",
    "severity": "soft"
  },
  {
    "name": "rewritten_query_present",
    "passed": true,
    "actual": "Show me dark-clothed persons",
    "expected": "non-empty rewritten query",
    "severity": "soft"
  },
  {
    "name": "user_need_identified",
    "passed": true,
    "actual": {
      "rewritten_query": "Show me dark-clothed persons",
      "user_need": "Retrieve basketball video results that satisfy: Show me dark-clothed persons",
      "intent_label": "structured",
      "retrieval_focus": "structured",
      "key_constraints": [
        "show",
        "me",
        "dark",
        "clothed",
        "persons"
      ],
      "ambiguities": [],
      "reasoning_summary": "Fast-path preprocessing kept the original meaning and only normalized surface noise.",
      "confidence": 0.8,
      "original_user_query": "Show me dark-clothed persons."
    },
    "expected": "structured self-query result with user_need",
    "severity": "soft"
  },
  {
    "name": "trace_has_required_nodes",
    "passed": true,
    "actual": [
      "self_query_node",
      "query_classification_node",
      "parallel_retrieval_fusion_node",
      "final_answer_node",
      "summary_node"
    ],
    "expected": [
      "self_query_node",
      "final_answer_node",
      "summary_node"
    ],
    "severity": "soft"
  },
  {
    "name": "routing_metrics_present",
    "passed": true,
    "actual": {
      "execution_mode": "parallel_fusion",
      "label": "structured",
      "query": "Show me dark-clothed persons",
      "sql_rows_count": 6,
      "hybrid_rows_count": 26,
      "sql_error": null,
      "hybrid_error": null
    },
    "expected": "non-empty routing_metrics",
    "severity": "soft"
  },
  {
    "name": "search_config_present",
    "passed": true,
    "actual": {
      "candidate_limit": 80,
      "top_k_per_event": 20,
      "rerank_top_k": 5,
      "distance_threshold": null,
      "hybrid_alpha": 0.7,
      "hybrid_fallback_alpha": 0.9,
      "hybrid_limit": 50,
      "sql_limit": 80
    },
    "expected": "non-empty search_config",
    "severity": "soft"
  },
  {
    "name": "sql_plan_present",
    "passed": true,
    "actual": {
      "table": "episodic_events",
      "fields": [
        "event_id",
        "video_id",
        "track_id",
        "start_time",
        "end_time",
        "object_type",
        "object_color_en",
        "scene_zone_en",
        "appearance_notes_en",
        "event_summary_en"
      ],
      "where": [
        {
          "field": "object_type",
          "op": "=",
          "value": "person"
        },
        {
          "field": "object_color_en",
          "op": "=",
          "value": "dark"
        }
      ],
      "order_by": "start_time ASC",
      "limit": 80
    },
    "expected": "non-empty sql_plan",
    "severity": "soft"
  },
  {
    "name": "no_tool_error",
    "passed": true,
    "actual": null,
    "expected": null,
    "severity": "soft"
  },
  {
    "name": "min_results",
    "passed": true,
    "actual": 32,
    "expected": 1,
    "severity": "hard"
  },
  {
    "name": "min_sql_rows",
    "passed": true,
    "actual": 6,
    "expected": 1,
    "severity": "hard"
  },
  {
    "name": "expected_keywords_any",
    "passed": true,
    "actual": "from 0.00s to 30.84s, a dark-clothed person stands near the left bleachers with little motion. from 0.00s to 9.96s, a dark-clothed person stands near the left side with little motion. from 40.60s to 44.90s, a dark-clothed person moves across the center-right court area. from 41.50s to 46.85s, a dark-clothed person moves near the left-center court area. from 46.15s to 50.45s, a dark-clothed person moves near the upper-middle court area.",
    "expected": [
      "dark"
    ],
    "severity": "hard"
  }
]
```
- Last Iteration:
```json
{
  "elapsed_ms": 8221.7,
  "route_mode": "pure_sql",
  "label": "structured",
  "llm_final_output": "In the video *basketball_2.mp4*, several dark-clothed individuals appear: one stands still near the left bleachers (0–30.8s), another near the left side (0–10s), and others move across the court between 40.6s and 50.5s in areas like center-right, left-center, and upper-middle.\nSources: [sql] basketball_2.mp4 | event_id=22 | 0.0-30.84; [sql] basketball_2.mp4 | event_id=27 | 0.0-9.96; [sql] basketball_2.mp4 | event_id=23 | 40.6-44.9",
  "raw_final_answer": "Retrieval complete. Most relevant results:\n[1] event_id=22 | video=basketball_2.mp4 | distance=0.0 | summary=From 0.00s to 30.84s, a dark-clothed person stands near the left bleachers with little motion.\n[2] event_id=27 | video=basketball_2.mp4 | distance=0.0 | summary=From 0.00s to 9.96s, a dark-clothed person stands near the left side with little motion.\n[3] event_id=23 | video=basketball_2.mp4 | distance=0.0 | summary=From 40.60s to 44.90s, a dark-clothed person moves across the center-right court area.\n[4] event_id=25 | video=basketball_2.mp4 | distance=0.0 | summary=From 41.50s to 46.85s, a dark-clothed person moves near the left-center court area.\n[5] event_id=26 | video=basketball_2.mp4 | distance=0.0 | summary=From 46.15s to 50.45s, a dark-clothed person moves near the upper-middle court area.",
  "rewritten_query": "Show me dark-clothed persons",
  "original_user_query": "Show me dark-clothed persons.",
  "self_query_result": {
    "rewritten_query": "Show me dark-clothed persons",
    "user_need": "Retrieve basketball video results that satisfy: Show me dark-clothed persons",
    "intent_label": "structured",
    "retrieval_focus": "structured",
    "key_constraints": [
      "show",
      "me",
      "dark",
      "clothed",
      "persons"
    ],
    "ambiguities": [],
    "reasoning_summary": "Fast-path preprocessing kept the original meaning and only normalized surface noise.",
    "confidence": 0.8,
    "original_user_query": "Show me dark-clothed persons."
  },
  "summary_result": {
    "summary": "In the video *basketball_2.mp4*, several dark-clothed individuals appear: one stands still near the left bleachers (0–30.8s), another near the left side (0–10s), and others move across the court between 40.6s and 50.5s in areas like center-right, left-center, and upper-middle.",
    "style": "llm_summary",
    "confidence": 0.8,
    "citations": [
      {
        "source_type": "sql",
        "video_id": "basketball_2.mp4",
        "event_id": 22,
        "start_time": 0.0,
        "end_time": 30.84
      },
      {
        "source_type": "sql",
        "video_id": "basketball_2.mp4",
        "event_id": 27,
        "start_time": 0.0,
        "end_time": 9.96
      },
      {
        "source_type": "sql",
        "video_id": "basketball_2.mp4",
        "event_id": 23,
        "start_time": 40.6,
        "end_time": 44.9
      }
    ]
  },
  "routing_metrics": {
    "execution_mode": "parallel_fusion",
    "label": "structured",
    "query": "Show me dark-clothed persons",
    "sql_rows_count": 6,
    "hybrid_rows_count": 26,
    "sql_error": null,
    "hybrid_error": null
  },
  "search_config": {
    "candidate_limit": 80,
    "top_k_per_event": 20,
    "rerank_top_k": 5,
    "distance_threshold": null,
    "hybrid_alpha": 0.7,
    "hybrid_fallback_alpha": 0.9,
    "hybrid_limit": 50,
    "sql_limit": 80
  },
  "sql_plan": {
    "table": "episodic_events",
    "fields": [
      "event_id",
      "video_id",
      "track_id",
      "start_time",
      "end_time",
      "object_type",
      "object_color_en",
      "scene_zone_en",
      "appearance_notes_en",
      "event_summary_en"
    ],
    "where": [
      {
        "field": "object_type",
        "op": "=",
        "value": "person"
      },
      {
        "field": "object_color_en",
        "op": "=",
        "value": "dark"
      }
    ],
    "order_by": "start_time ASC",
    "limit": 80
  },
  "node_trace": [
    "self_query_node",
    "query_classification_node",
    "parallel_retrieval_fusion_node",
    "final_answer_node",
    "summary_node"
  ],
  "final_answer": "In the video *basketball_2.mp4*, several dark-clothed individuals appear: one stands still near the left bleachers (0–30.8s), another near the left side (0–10s), and others move across the court between 40.6s and 50.5s in areas like center-right, left-center, and upper-middle.\nSources: [sql] basketball_2.mp4 | event_id=22 | 0.0-30.84; [sql] basketball_2.mp4 | event_id=27 | 0.0-9.96; [sql] basketball_2.mp4 | event_id=23 | 40.6-44.9",
  "tool_error": null,
  "error": null,
  "current_node": "summary_node",
  "top5": [
    {
      "event_id": 22,
      "video_id": "basketball_2.mp4",
      "event_text": "From 0.00s to 30.84s, a dark-clothed person stands near the left bleachers with little motion.",
      "distance": 0.0
    },
    {
      "event_id": 27,
      "video_id": "basketball_2.mp4",
      "event_text": "From 0.00s to 9.96s, a dark-clothed person stands near the left side with little motion.",
      "distance": 0.0
    },
    {
      "event_id": 23,
      "video_id": "basketball_2.mp4",
      "event_text": "From 40.60s to 44.90s, a dark-clothed person moves across the center-right court area.",
      "distance": 0.0
    },
    {
      "event_id": 25,
      "video_id": "basketball_2.mp4",
      "event_text": "From 41.50s to 46.85s, a dark-clothed person moves near the left-center court area.",
      "distance": 0.0
    },
    {
      "event_id": 26,
      "video_id": "basketball_2.mp4",
      "event_text": "From 46.15s to 50.45s, a dark-clothed person moves near the upper-middle court area.",
      "distance": 0.0
    }
  ],
  "merged_count": 32,
  "sql_rows_count": 6,
  "hybrid_rows_count": 26,
  "degraded": false,
  "hybrid_summary": "Hybrid direct retrieval complete",
  "sql_summary": "SQL direct retrieval rows=6",
  "hybrid_error": null,
  "sql_error": null,
  "sql_debug": {
    "duration": 3.023627223999938,
    "sql_summary": "SQL direct retrieval rows=6",
    "hybrid_summary": "Hybrid direct retrieval complete",
    "sql_error": null,
    "hybrid_error": null,
    "fusion_meta": {
      "label": "structured",
      "weights": {
        "sql": 0.8,
        "hybrid": 0.2
      },
      "rrf_k": 60.0,
      "sql_count": 6,
      "hybrid_count": 26,
      "fused_count": 32,
      "method": "weighted_rrf",
      "degraded": false
    }
  }
}
```

## FNC_HYB_001
- Suite: `semantic_regression`
- Priority: `P0`
- Dimensions: `functional, semantic, routing`
- Description: Semantic location query should route to hybrid_search and activate semantic retrieval.
- Query: `Find a person near the left bleachers.`
- Status: `PASS`
- Avg Latency: `8471.09 ms`
- P95 Latency: `8471.09 ms`
- Node Trace:
```json
[
  "self_query_node",
  "query_classification_node",
  "parallel_retrieval_fusion_node",
  "final_answer_node",
  "summary_node"
]
```
- Routing Metrics:
```json
{
  "execution_mode": "parallel_fusion",
  "label": "semantic",
  "query": "Find a person near the left bleachers",
  "sql_rows_count": 1,
  "hybrid_rows_count": 26,
  "sql_error": null,
  "hybrid_error": null
}
```
- Search Config:
```json
{
  "candidate_limit": 80,
  "top_k_per_event": 20,
  "rerank_top_k": 5,
  "distance_threshold": null,
  "hybrid_alpha": 0.7,
  "hybrid_fallback_alpha": 0.9,
  "hybrid_limit": 50,
  "sql_limit": 80
}
```
- SQL Plan:
```json
{
  "table": "episodic_events",
  "fields": [
    "event_id",
    "video_id",
    "track_id",
    "start_time",
    "end_time",
    "object_type",
    "object_color_en",
    "scene_zone_en",
    "appearance_notes_en",
    "event_summary_en"
  ],
  "where": [
    {
      "field": "object_type",
      "op": "=",
      "value": "person"
    },
    {
      "field": "scene_zone_en",
      "op": "contains",
      "value": "left bleachers"
    }
  ],
  "order_by": "start_time ASC",
  "limit": 80
}
```
- Self Query Result:
```json
{
  "rewritten_query": "Find a person near the left bleachers",
  "user_need": "Retrieve basketball video results that satisfy: Find a person near the left bleachers",
  "intent_label": "semantic",
  "retrieval_focus": "semantic",
  "key_constraints": [
    "find",
    "a",
    "person",
    "near",
    "the",
    "left"
  ],
  "ambiguities": [],
  "reasoning_summary": "Fast-path preprocessing kept the original meaning and only normalized surface noise.",
  "confidence": 0.8,
  "original_user_query": "Find a person near the left bleachers."
}
```
- Raw Final Answer:
```json
{
  "raw_final_answer": "Retrieval complete. Most relevant results:\n[1] event_id=basketball_2.mp4_track_id_1 | video=basketball_2.mp4 | distance=0.201948881149292 | summary=standing near left bleachers with little motion Located in left bleachers. From 0.00s to 30.84s, a dark-clothed person stands near the left bleachers with little motion.\n[2] event_id=basketball_1.mp4_track_1 | video=basketball_1.mp4 | distance=0.32872921228408813 | summary=Little motion; standing near the left baseline/bench area. Located in sidewalk. From 0.0s to 61.2s, a person with unknown color stays mostly still near the left baseline/bench area.\n[3] event_id=basketball_1.mp4_track_29 | video=basketball_1.mp4 | distance=0.3379225730895996 | summary=Little motion; standing near the left side of the court. Located in sidewalk. From 43.8s to 125.7s, a person with unknown color remains mostly still near the left side of the court.\n[4] event_id=basketball_1.mp4_track_30 | video=basketball_1.mp4 | distance=0.3311508297920227 | summary=Little motion; standing near the left-center court area. Located in sidewalk. From 47.8s to 48.8s, a person with unknown color remains mostly still near the left-center court area.\n[5] event_id=basketball_1.mp4_track_11 | video=basketball_1.mp4 | distance=0.3382689356803894 | summary=Little motion; standing near the left-center baseline area. Located in sidewalk. From 11.5s to 91.8s, a person with unknown color remains mostly still near the left-center baseline area."
}
```
- LLM Final Output:
```json
{
  "llm_final_output": "A dark-clothed person stands near the left bleachers with little motion from 0.00s to 30.84s in *basketball_2.mp4*. In *basketball_1.mp4*, several individuals remain mostly still near the left baseline, bench area, or left side of the court at various times.\nSources: [hybrid] basketball_2.mp4 | event_id=basketball_2.mp4_track_id_1 | 0.0-30.84; [hybrid] basketball_1.mp4 | event_id=basketball_1.mp4_track_1 | 0.0-61.208333333333336; [hybrid] basketball_1.mp4 | event_id=basketball_1.mp4_track_29 | 43.791666666666664-125.70833333333331"
}
```
- Assertions:
```json
[
  {
    "name": "no_runtime_exception",
    "passed": true,
    "actual": [],
    "expected": null,
    "severity": "hard"
  },
  {
    "name": "label_matches",
    "passed": true,
    "actual": "semantic",
    "expected": "semantic",
    "severity": "hard"
  },
  {
    "name": "route_in_expected",
    "passed": true,
    "actual": "hybrid_search",
    "expected": [
      "hybrid_search"
    ],
    "severity": "hard"
  },
  {
    "name": "final_answer_present",
    "passed": true,
    "actual": "A dark-clothed person stands near the left bleachers with little motion from 0.00s to 30.84s in *basketball_2.mp4*. In *basketball_1.mp4*, several individuals remain mostly still near the left baseline, bench area, or left side of the court at various times.\nSources: [hybrid] basketball_2.mp4 | event_id=basketball_2.mp4_track_id_1 | 0.0-30.84; [hybrid] basketball_1.mp4 | event_id=basketball_1.mp4_track_1 | 0.0-61.208333333333336; [hybrid] basketball_1.mp4 | event_id=basketball_1.mp4_track_29 | 43.791666666666664-125.70833333333331",
    "expected": "non-empty string",
    "severity": "hard"
  },
  {
    "name": "citation_present",
    "passed": true,
    "actual": "A dark-clothed person stands near the left bleachers with little motion from 0.00s to 30.84s in *basketball_2.mp4*. In *basketball_1.mp4*, several individuals remain mostly still near the left baseline, bench area, or left side of the court at various times.\nSources: [hybrid] basketball_2.mp4 | event_id=basketball_2.mp4_track_id_1 | 0.0-30.84; [hybrid] basketball_1.mp4 | event_id=basketball_1.mp4_track_1 | 0.0-61.208333333333336; [hybrid] basketball_1.mp4 | event_id=basketball_1.mp4_track_29 | 43.791666666666664-125.70833333333331",
    "expected": "final answer contains Sources:",
    "severity": "soft"
  },
  {
    "name": "grounding_coverage",
    "passed": true,
    "actual": {
      "summary": "A dark-clothed person stands near the left bleachers with little motion from 0.00s to 30.84s in *basketball_2.mp4*. In *basketball_1.mp4*, several individuals remain mostly still near the left baseline, bench area, or left side of the court at various times.",
      "style": "llm_summary",
      "confidence": 0.8,
      "citations": [
        {
          "source_type": "hybrid",
          "video_id": "basketball_2.mp4",
          "event_id": "basketball_2.mp4_track_id_1",
          "start_time": 0.0,
          "end_time": 30.84
        },
        {
          "source_type": "hybrid",
          "video_id": "basketball_1.mp4",
          "event_id": "basketball_1.mp4_track_1",
          "start_time": 0.0,
          "end_time": 61.208333333333336
        },
        {
          "source_type": "hybrid",
          "video_id": "basketball_1.mp4",
          "event_id": "basketball_1.mp4_track_29",
          "start_time": 43.791666666666664,
          "end_time": 125.70833333333331
        }
      ]
    },
    "expected": "summary_result.citations is non-empty",
    "severity": "soft"
  },
  {
    "name": "rewritten_query_present",
    "passed": true,
    "actual": "Find a person near the left bleachers",
    "expected": "non-empty rewritten query",
    "severity": "soft"
  },
  {
    "name": "user_need_identified",
    "passed": true,
    "actual": {
      "rewritten_query": "Find a person near the left bleachers",
      "user_need": "Retrieve basketball video results that satisfy: Find a person near the left bleachers",
      "intent_label": "semantic",
      "retrieval_focus": "semantic",
      "key_constraints": [
        "find",
        "a",
        "person",
        "near",
        "the",
        "left"
      ],
      "ambiguities": [],
      "reasoning_summary": "Fast-path preprocessing kept the original meaning and only normalized surface noise.",
      "confidence": 0.8,
      "original_user_query": "Find a person near the left bleachers."
    },
    "expected": "structured self-query result with user_need",
    "severity": "soft"
  },
  {
    "name": "trace_has_required_nodes",
    "passed": true,
    "actual": [
      "self_query_node",
      "query_classification_node",
      "parallel_retrieval_fusion_node",
      "final_answer_node",
      "summary_node"
    ],
    "expected": [
      "self_query_node",
      "final_answer_node",
      "summary_node"
    ],
    "severity": "soft"
  },
  {
    "name": "routing_metrics_present",
    "passed": true,
    "actual": {
      "execution_mode": "parallel_fusion",
      "label": "semantic",
      "query": "Find a person near the left bleachers",
      "sql_rows_count": 1,
      "hybrid_rows_count": 26,
      "sql_error": null,
      "hybrid_error": null
    },
    "expected": "non-empty routing_metrics",
    "severity": "soft"
  },
  {
    "name": "search_config_present",
    "passed": true,
    "actual": {
      "candidate_limit": 80,
      "top_k_per_event": 20,
      "rerank_top_k": 5,
      "distance_threshold": null,
      "hybrid_alpha": 0.7,
      "hybrid_fallback_alpha": 0.9,
      "hybrid_limit": 50,
      "sql_limit": 80
    },
    "expected": "non-empty search_config",
    "severity": "soft"
  },
  {
    "name": "no_tool_error",
    "passed": true,
    "actual": null,
    "expected": null,
    "severity": "soft"
  },
  {
    "name": "min_results",
    "passed": true,
    "actual": 27,
    "expected": 1,
    "severity": "hard"
  },
  {
    "name": "expected_keywords_any",
    "passed": true,
    "actual": "standing near left bleachers with little motion located in left bleachers. from 0.00s to 30.84s, a dark-clothed person stands near the left bleachers with little motion. little motion; standing near the left baseline/bench area. located in sidewalk. from 0.0s to 61.2s, a person with unknown color stays mostly still near the left baseline/bench area. little motion; standing near the left side of the court. located in sidewalk. from 43.8s to 125.7s, a person with unknown color remains mostly still near the left side of the court. little motion; standing near the left-center court area. located in sidewalk. from 47.8s to 48.8s, a person with unknown color remains mostly still near the left-center court area. little motion; standing near the left-center baseline area. located in sidewalk. from 11.5s to 91.8s, a person with unknown color remains mostly still near the left-center baseline area.",
    "expected": [
      "bleachers"
    ],
    "severity": "soft"
  },
  {
    "name": "semantic_backend_effective",
    "passed": true,
    "actual": {
      "hybrid_rows_count": 26,
      "hybrid_error": null,
      "degraded": false
    },
    "expected": "hybrid rows > 0 or explicit degradation/error",
    "severity": "hard"
  },
  {
    "name": "hybrid_health_consistency",
    "passed": true,
    "actual": {
      "hybrid_summary": "Hybrid direct retrieval complete",
      "hybrid_error": null,
      "degraded": false
    },
    "expected": "hybrid failure should be reflected by degraded flag or hybrid_error",
    "severity": "hard"
  }
]
```
- Last Iteration:
```json
{
  "elapsed_ms": 8471.09,
  "route_mode": "hybrid_search",
  "label": "semantic",
  "llm_final_output": "A dark-clothed person stands near the left bleachers with little motion from 0.00s to 30.84s in *basketball_2.mp4*. In *basketball_1.mp4*, several individuals remain mostly still near the left baseline, bench area, or left side of the court at various times.\nSources: [hybrid] basketball_2.mp4 | event_id=basketball_2.mp4_track_id_1 | 0.0-30.84; [hybrid] basketball_1.mp4 | event_id=basketball_1.mp4_track_1 | 0.0-61.208333333333336; [hybrid] basketball_1.mp4 | event_id=basketball_1.mp4_track_29 | 43.791666666666664-125.70833333333331",
  "raw_final_answer": "Retrieval complete. Most relevant results:\n[1] event_id=basketball_2.mp4_track_id_1 | video=basketball_2.mp4 | distance=0.201948881149292 | summary=standing near left bleachers with little motion Located in left bleachers. From 0.00s to 30.84s, a dark-clothed person stands near the left bleachers with little motion.\n[2] event_id=basketball_1.mp4_track_1 | video=basketball_1.mp4 | distance=0.32872921228408813 | summary=Little motion; standing near the left baseline/bench area. Located in sidewalk. From 0.0s to 61.2s, a person with unknown color stays mostly still near the left baseline/bench area.\n[3] event_id=basketball_1.mp4_track_29 | video=basketball_1.mp4 | distance=0.3379225730895996 | summary=Little motion; standing near the left side of the court. Located in sidewalk. From 43.8s to 125.7s, a person with unknown color remains mostly still near the left side of the court.\n[4] event_id=basketball_1.mp4_track_30 | video=basketball_1.mp4 | distance=0.3311508297920227 | summary=Little motion; standing near the left-center court area. Located in sidewalk. From 47.8s to 48.8s, a person with unknown color remains mostly still near the left-center court area.\n[5] event_id=basketball_1.mp4_track_11 | video=basketball_1.mp4 | distance=0.3382689356803894 | summary=Little motion; standing near the left-center baseline area. Located in sidewalk. From 11.5s to 91.8s, a person with unknown color remains mostly still near the left-center baseline area.",
  "rewritten_query": "Find a person near the left bleachers",
  "original_user_query": "Find a person near the left bleachers.",
  "self_query_result": {
    "rewritten_query": "Find a person near the left bleachers",
    "user_need": "Retrieve basketball video results that satisfy: Find a person near the left bleachers",
    "intent_label": "semantic",
    "retrieval_focus": "semantic",
    "key_constraints": [
      "find",
      "a",
      "person",
      "near",
      "the",
      "left"
    ],
    "ambiguities": [],
    "reasoning_summary": "Fast-path preprocessing kept the original meaning and only normalized surface noise.",
    "confidence": 0.8,
    "original_user_query": "Find a person near the left bleachers."
  },
  "summary_result": {
    "summary": "A dark-clothed person stands near the left bleachers with little motion from 0.00s to 30.84s in *basketball_2.mp4*. In *basketball_1.mp4*, several individuals remain mostly still near the left baseline, bench area, or left side of the court at various times.",
    "style": "llm_summary",
    "confidence": 0.8,
    "citations": [
      {
        "source_type": "hybrid",
        "video_id": "basketball_2.mp4",
        "event_id": "basketball_2.mp4_track_id_1",
        "start_time": 0.0,
        "end_time": 30.84
      },
      {
        "source_type": "hybrid",
        "video_id": "basketball_1.mp4",
        "event_id": "basketball_1.mp4_track_1",
        "start_time": 0.0,
        "end_time": 61.208333333333336
      },
      {
        "source_type": "hybrid",
        "video_id": "basketball_1.mp4",
        "event_id": "basketball_1.mp4_track_29",
        "start_time": 43.791666666666664,
        "end_time": 125.70833333333331
      }
    ]
  },
  "routing_metrics": {
    "execution_mode": "parallel_fusion",
    "label": "semantic",
    "query": "Find a person near the left bleachers",
    "sql_rows_count": 1,
    "hybrid_rows_count": 26,
    "sql_error": null,
    "hybrid_error": null
  },
  "search_config": {
    "candidate_limit": 80,
    "top_k_per_event": 20,
    "rerank_top_k": 5,
    "distance_threshold": null,
    "hybrid_alpha": 0.7,
    "hybrid_fallback_alpha": 0.9,
    "hybrid_limit": 50,
    "sql_limit": 80
  },
  "sql_plan": {
    "table": "episodic_events",
    "fields": [
      "event_id",
      "video_id",
      "track_id",
      "start_time",
      "end_time",
      "object_type",
      "object_color_en",
      "scene_zone_en",
      "appearance_notes_en",
      "event_summary_en"
    ],
    "where": [
      {
        "field": "object_type",
        "op": "=",
        "value": "person"
      },
      {
        "field": "scene_zone_en",
        "op": "contains",
        "value": "left bleachers"
      }
    ],
    "order_by": "start_time ASC",
    "limit": 80
  },
  "node_trace": [
    "self_query_node",
    "query_classification_node",
    "parallel_retrieval_fusion_node",
    "final_answer_node",
    "summary_node"
  ],
  "final_answer": "A dark-clothed person stands near the left bleachers with little motion from 0.00s to 30.84s in *basketball_2.mp4*. In *basketball_1.mp4*, several individuals remain mostly still near the left baseline, bench area, or left side of the court at various times.\nSources: [hybrid] basketball_2.mp4 | event_id=basketball_2.mp4_track_id_1 | 0.0-30.84; [hybrid] basketball_1.mp4 | event_id=basketball_1.mp4_track_1 | 0.0-61.208333333333336; [hybrid] basketball_1.mp4 | event_id=basketball_1.mp4_track_29 | 43.791666666666664-125.70833333333331",
  "tool_error": null,
  "error": null,
  "current_node": "summary_node",
  "top5": [
    {
      "event_id": "basketball_2.mp4_track_id_1",
      "video_id": "basketball_2.mp4",
      "event_text": "standing near left bleachers with little motion Located in left bleachers. From 0.00s to 30.84s, a dark-clothed person stands near the left bleachers with little motion.",
      "distance": 0.201948881149292
    },
    {
      "event_id": "basketball_1.mp4_track_1",
      "video_id": "basketball_1.mp4",
      "event_text": "Little motion; standing near the left baseline/bench area. Located in sidewalk. From 0.0s to 61.2s, a person with unknown color stays mostly still near the left baseline/bench area.",
      "distance": 0.32872921228408813
    },
    {
      "event_id": "basketball_1.mp4_track_29",
      "video_id": "basketball_1.mp4",
      "event_text": "Little motion; standing near the left side of the court. Located in sidewalk. From 43.8s to 125.7s, a person with unknown color remains mostly still near the left side of the court.",
      "distance": 0.3379225730895996
    },
    {
      "event_id": "basketball_1.mp4_track_30",
      "video_id": "basketball_1.mp4",
      "event_text": "Little motion; standing near the left-center court area. Located in sidewalk. From 47.8s to 48.8s, a person with unknown color remains mostly still near the left-center court area.",
      "distance": 0.3311508297920227
    },
    {
      "event_id": "basketball_1.mp4_track_11",
      "video_id": "basketball_1.mp4",
      "event_text": "Little motion; standing near the left-center baseline area. Located in sidewalk. From 11.5s to 91.8s, a person with unknown color remains mostly still near the left-center baseline area.",
      "distance": 0.3382689356803894
    }
  ],
  "merged_count": 27,
  "sql_rows_count": 1,
  "hybrid_rows_count": 26,
  "degraded": false,
  "hybrid_summary": "Hybrid direct retrieval complete",
  "sql_summary": "SQL direct retrieval rows=1",
  "hybrid_error": null,
  "sql_error": null,
  "sql_debug": {
    "duration": 2.8357645040014177,
    "sql_summary": "SQL direct retrieval rows=1",
    "hybrid_summary": "Hybrid direct retrieval complete",
    "sql_error": null,
    "hybrid_error": null,
    "fusion_meta": {
      "label": "semantic",
      "weights": {
        "sql": 0.2,
        "hybrid": 0.8
      },
      "rrf_k": 60.0,
      "sql_count": 1,
      "hybrid_count": 26,
      "fused_count": 27,
      "method": "weighted_rrf",
      "degraded": false
    }
  }
}
```

## FNC_HYB_002
- Suite: `semantic_regression`
- Priority: `P0`
- Dimensions: `functional, semantic, behavior`
- Description: Behavior + location query should route to hybrid_search and preserve semantic capability.
- Query: `Look for a person moving on the sidewalk.`
- Status: `PASS`
- Avg Latency: `7779.48 ms`
- P95 Latency: `7779.48 ms`
- Node Trace:
```json
[
  "self_query_node",
  "query_classification_node",
  "parallel_retrieval_fusion_node",
  "final_answer_node",
  "summary_node"
]
```
- Routing Metrics:
```json
{
  "execution_mode": "parallel_fusion",
  "label": "semantic",
  "query": "Look for a person moving on the sidewalk",
  "sql_rows_count": 12,
  "hybrid_rows_count": 26,
  "sql_error": null,
  "hybrid_error": null
}
```
- Search Config:
```json
{
  "candidate_limit": 80,
  "top_k_per_event": 20,
  "rerank_top_k": 5,
  "distance_threshold": null,
  "hybrid_alpha": 0.7,
  "hybrid_fallback_alpha": 0.9,
  "hybrid_limit": 50,
  "sql_limit": 80
}
```
- SQL Plan:
```json
{
  "table": "episodic_events",
  "fields": [
    "event_id",
    "video_id",
    "track_id",
    "start_time",
    "end_time",
    "object_type",
    "object_color_en",
    "scene_zone_en",
    "appearance_notes_en",
    "event_summary_en"
  ],
  "where": [
    {
      "field": "object_type",
      "op": "=",
      "value": "person"
    },
    {
      "field": "scene_zone_en",
      "op": "contains",
      "value": "sidewalk"
    }
  ],
  "order_by": "start_time ASC",
  "limit": 80
}
```
- Self Query Result:
```json
{
  "rewritten_query": "Look for a person moving on the sidewalk",
  "user_need": "Retrieve basketball video results that satisfy: Look for a person moving on the sidewalk",
  "intent_label": "semantic",
  "retrieval_focus": "semantic",
  "key_constraints": [
    "look",
    "for",
    "a",
    "person",
    "moving",
    "on"
  ],
  "ambiguities": [],
  "reasoning_summary": "Fast-path preprocessing kept the original meaning and only normalized surface noise.",
  "confidence": 0.8,
  "original_user_query": "Look for a person moving on the sidewalk."
}
```
- Raw Final Answer:
```json
{
  "raw_final_answer": "Retrieval complete. Most relevant results:\n[1] event_id=basketball_1.mp4_track_8 | video=basketball_1.mp4 | distance=0.28515905141830444 | summary=Little motion; standing near the left-center baseline area. Located in sidewalk. From 0.0s to 5.0s, a person with unknown color remains mostly still near the left-center baseline area.\n[2] event_id=basketball_1.mp4_track_11 | video=basketball_1.mp4 | distance=0.2854006886482239 | summary=Little motion; standing near the left-center baseline area. Located in sidewalk. From 11.5s to 91.8s, a person with unknown color remains mostly still near the left-center baseline area.\n[3] event_id=basketball_1.mp4_track_6 | video=basketball_1.mp4 | distance=0.28660809993743896 | summary=Little motion; standing near the left-center baseline area. Located in sidewalk. From 0.0s to 17.5s, a person with unknown color remains mostly still near the left-center baseline area.\n[4] event_id=basketball_1.mp4_track_3 | video=basketball_1.mp4 | distance=0.28685200214385986 | summary=Little motion; standing near the left-center baseline area. Located in sidewalk. From 0.0s to 12.0s, a person with unknown color remains mostly still near the left-center baseline area.\n[5] event_id=basketball_1.mp4_track_36 | video=basketball_1.mp4 | distance=0.28814852237701416 | summary=Little motion; standing near the left-center court edge. Located in sidewalk. From 62.4s to 64.0s, a person with unknown color remains mostly still near the left-center court edge."
}
```
- LLM Final Output:
```json
{
  "llm_final_output": "The search found several people on the sidewalk near the left-center baseline area of a basketball court, but most were standing still rather than moving. The top results show individuals remaining mostly motionless during various time intervals in the video.\nSources: [hybrid] basketball_1.mp4 | event_id=basketball_1.mp4_track_8 | 0.0-4.958333333333333; [hybrid] basketball_1.mp4 | event_id=basketball_1.mp4_track_11 | 11.5-91.75; [hybrid] basketball_1.mp4 | event_id=basketball_1.mp4_track_6 | 0.0-17.458333333333332"
}
```
- Assertions:
```json
[
  {
    "name": "no_runtime_exception",
    "passed": true,
    "actual": [],
    "expected": null,
    "severity": "hard"
  },
  {
    "name": "label_matches",
    "passed": true,
    "actual": "semantic",
    "expected": "semantic",
    "severity": "hard"
  },
  {
    "name": "route_in_expected",
    "passed": true,
    "actual": "hybrid_search",
    "expected": [
      "hybrid_search"
    ],
    "severity": "hard"
  },
  {
    "name": "final_answer_present",
    "passed": true,
    "actual": "The search found several people on the sidewalk near the left-center baseline area of a basketball court, but most were standing still rather than moving. The top results show individuals remaining mostly motionless during various time intervals in the video.\nSources: [hybrid] basketball_1.mp4 | event_id=basketball_1.mp4_track_8 | 0.0-4.958333333333333; [hybrid] basketball_1.mp4 | event_id=basketball_1.mp4_track_11 | 11.5-91.75; [hybrid] basketball_1.mp4 | event_id=basketball_1.mp4_track_6 | 0.0-17.458333333333332",
    "expected": "non-empty string",
    "severity": "hard"
  },
  {
    "name": "citation_present",
    "passed": true,
    "actual": "The search found several people on the sidewalk near the left-center baseline area of a basketball court, but most were standing still rather than moving. The top results show individuals remaining mostly motionless during various time intervals in the video.\nSources: [hybrid] basketball_1.mp4 | event_id=basketball_1.mp4_track_8 | 0.0-4.958333333333333; [hybrid] basketball_1.mp4 | event_id=basketball_1.mp4_track_11 | 11.5-91.75; [hybrid] basketball_1.mp4 | event_id=basketball_1.mp4_track_6 | 0.0-17.458333333333332",
    "expected": "final answer contains Sources:",
    "severity": "soft"
  },
  {
    "name": "grounding_coverage",
    "passed": true,
    "actual": {
      "summary": "The search found several people on the sidewalk near the left-center baseline area of a basketball court, but most were standing still rather than moving. The top results show individuals remaining mostly motionless during various time intervals in the video.",
      "style": "llm_summary",
      "confidence": 0.8,
      "citations": [
        {
          "source_type": "hybrid",
          "video_id": "basketball_1.mp4",
          "event_id": "basketball_1.mp4_track_8",
          "start_time": 0.0,
          "end_time": 4.958333333333333
        },
        {
          "source_type": "hybrid",
          "video_id": "basketball_1.mp4",
          "event_id": "basketball_1.mp4_track_11",
          "start_time": 11.5,
          "end_time": 91.75
        },
        {
          "source_type": "hybrid",
          "video_id": "basketball_1.mp4",
          "event_id": "basketball_1.mp4_track_6",
          "start_time": 0.0,
          "end_time": 17.458333333333332
        }
      ]
    },
    "expected": "summary_result.citations is non-empty",
    "severity": "soft"
  },
  {
    "name": "rewritten_query_present",
    "passed": true,
    "actual": "Look for a person moving on the sidewalk",
    "expected": "non-empty rewritten query",
    "severity": "soft"
  },
  {
    "name": "user_need_identified",
    "passed": true,
    "actual": {
      "rewritten_query": "Look for a person moving on the sidewalk",
      "user_need": "Retrieve basketball video results that satisfy: Look for a person moving on the sidewalk",
      "intent_label": "semantic",
      "retrieval_focus": "semantic",
      "key_constraints": [
        "look",
        "for",
        "a",
        "person",
        "moving",
        "on"
      ],
      "ambiguities": [],
      "reasoning_summary": "Fast-path preprocessing kept the original meaning and only normalized surface noise.",
      "confidence": 0.8,
      "original_user_query": "Look for a person moving on the sidewalk."
    },
    "expected": "structured self-query result with user_need",
    "severity": "soft"
  },
  {
    "name": "trace_has_required_nodes",
    "passed": true,
    "actual": [
      "self_query_node",
      "query_classification_node",
      "parallel_retrieval_fusion_node",
      "final_answer_node",
      "summary_node"
    ],
    "expected": [
      "self_query_node",
      "final_answer_node",
      "summary_node"
    ],
    "severity": "soft"
  },
  {
    "name": "routing_metrics_present",
    "passed": true,
    "actual": {
      "execution_mode": "parallel_fusion",
      "label": "semantic",
      "query": "Look for a person moving on the sidewalk",
      "sql_rows_count": 12,
      "hybrid_rows_count": 26,
      "sql_error": null,
      "hybrid_error": null
    },
    "expected": "non-empty routing_metrics",
    "severity": "soft"
  },
  {
    "name": "search_config_present",
    "passed": true,
    "actual": {
      "candidate_limit": 80,
      "top_k_per_event": 20,
      "rerank_top_k": 5,
      "distance_threshold": null,
      "hybrid_alpha": 0.7,
      "hybrid_fallback_alpha": 0.9,
      "hybrid_limit": 50,
      "sql_limit": 80
    },
    "expected": "non-empty search_config",
    "severity": "soft"
  },
  {
    "name": "no_tool_error",
    "passed": true,
    "actual": null,
    "expected": null,
    "severity": "soft"
  },
  {
    "name": "min_results",
    "passed": true,
    "actual": 38,
    "expected": 1,
    "severity": "hard"
  },
  {
    "name": "expected_keywords_any",
    "passed": true,
    "actual": "little motion; standing near the left-center baseline area. located in sidewalk. from 0.0s to 5.0s, a person with unknown color remains mostly still near the left-center baseline area. little motion; standing near the left-center baseline area. located in sidewalk. from 11.5s to 91.8s, a person with unknown color remains mostly still near the left-center baseline area. little motion; standing near the left-center baseline area. located in sidewalk. from 0.0s to 17.5s, a person with unknown color remains mostly still near the left-center baseline area. little motion; standing near the left-center baseline area. located in sidewalk. from 0.0s to 12.0s, a person with unknown color remains mostly still near the left-center baseline area. little motion; standing near the left-center court edge. located in sidewalk. from 62.4s to 64.0s, a person with unknown color remains mostly still near the left-center court edge.",
    "expected": [
      "sidewalk",
      "moving"
    ],
    "severity": "soft"
  },
  {
    "name": "semantic_backend_effective",
    "passed": true,
    "actual": {
      "hybrid_rows_count": 26,
      "hybrid_error": null,
      "degraded": false
    },
    "expected": "hybrid rows > 0 or explicit degradation/error",
    "severity": "hard"
  },
  {
    "name": "hybrid_health_consistency",
    "passed": true,
    "actual": {
      "hybrid_summary": "Hybrid direct retrieval complete",
      "hybrid_error": null,
      "degraded": false
    },
    "expected": "hybrid failure should be reflected by degraded flag or hybrid_error",
    "severity": "hard"
  }
]
```
- Last Iteration:
```json
{
  "elapsed_ms": 7779.48,
  "route_mode": "hybrid_search",
  "label": "semantic",
  "llm_final_output": "The search found several people on the sidewalk near the left-center baseline area of a basketball court, but most were standing still rather than moving. The top results show individuals remaining mostly motionless during various time intervals in the video.\nSources: [hybrid] basketball_1.mp4 | event_id=basketball_1.mp4_track_8 | 0.0-4.958333333333333; [hybrid] basketball_1.mp4 | event_id=basketball_1.mp4_track_11 | 11.5-91.75; [hybrid] basketball_1.mp4 | event_id=basketball_1.mp4_track_6 | 0.0-17.458333333333332",
  "raw_final_answer": "Retrieval complete. Most relevant results:\n[1] event_id=basketball_1.mp4_track_8 | video=basketball_1.mp4 | distance=0.28515905141830444 | summary=Little motion; standing near the left-center baseline area. Located in sidewalk. From 0.0s to 5.0s, a person with unknown color remains mostly still near the left-center baseline area.\n[2] event_id=basketball_1.mp4_track_11 | video=basketball_1.mp4 | distance=0.2854006886482239 | summary=Little motion; standing near the left-center baseline area. Located in sidewalk. From 11.5s to 91.8s, a person with unknown color remains mostly still near the left-center baseline area.\n[3] event_id=basketball_1.mp4_track_6 | video=basketball_1.mp4 | distance=0.28660809993743896 | summary=Little motion; standing near the left-center baseline area. Located in sidewalk. From 0.0s to 17.5s, a person with unknown color remains mostly still near the left-center baseline area.\n[4] event_id=basketball_1.mp4_track_3 | video=basketball_1.mp4 | distance=0.28685200214385986 | summary=Little motion; standing near the left-center baseline area. Located in sidewalk. From 0.0s to 12.0s, a person with unknown color remains mostly still near the left-center baseline area.\n[5] event_id=basketball_1.mp4_track_36 | video=basketball_1.mp4 | distance=0.28814852237701416 | summary=Little motion; standing near the left-center court edge. Located in sidewalk. From 62.4s to 64.0s, a person with unknown color remains mostly still near the left-center court edge.",
  "rewritten_query": "Look for a person moving on the sidewalk",
  "original_user_query": "Look for a person moving on the sidewalk.",
  "self_query_result": {
    "rewritten_query": "Look for a person moving on the sidewalk",
    "user_need": "Retrieve basketball video results that satisfy: Look for a person moving on the sidewalk",
    "intent_label": "semantic",
    "retrieval_focus": "semantic",
    "key_constraints": [
      "look",
      "for",
      "a",
      "person",
      "moving",
      "on"
    ],
    "ambiguities": [],
    "reasoning_summary": "Fast-path preprocessing kept the original meaning and only normalized surface noise.",
    "confidence": 0.8,
    "original_user_query": "Look for a person moving on the sidewalk."
  },
  "summary_result": {
    "summary": "The search found several people on the sidewalk near the left-center baseline area of a basketball court, but most were standing still rather than moving. The top results show individuals remaining mostly motionless during various time intervals in the video.",
    "style": "llm_summary",
    "confidence": 0.8,
    "citations": [
      {
        "source_type": "hybrid",
        "video_id": "basketball_1.mp4",
        "event_id": "basketball_1.mp4_track_8",
        "start_time": 0.0,
        "end_time": 4.958333333333333
      },
      {
        "source_type": "hybrid",
        "video_id": "basketball_1.mp4",
        "event_id": "basketball_1.mp4_track_11",
        "start_time": 11.5,
        "end_time": 91.75
      },
      {
        "source_type": "hybrid",
        "video_id": "basketball_1.mp4",
        "event_id": "basketball_1.mp4_track_6",
        "start_time": 0.0,
        "end_time": 17.458333333333332
      }
    ]
  },
  "routing_metrics": {
    "execution_mode": "parallel_fusion",
    "label": "semantic",
    "query": "Look for a person moving on the sidewalk",
    "sql_rows_count": 12,
    "hybrid_rows_count": 26,
    "sql_error": null,
    "hybrid_error": null
  },
  "search_config": {
    "candidate_limit": 80,
    "top_k_per_event": 20,
    "rerank_top_k": 5,
    "distance_threshold": null,
    "hybrid_alpha": 0.7,
    "hybrid_fallback_alpha": 0.9,
    "hybrid_limit": 50,
    "sql_limit": 80
  },
  "sql_plan": {
    "table": "episodic_events",
    "fields": [
      "event_id",
      "video_id",
      "track_id",
      "start_time",
      "end_time",
      "object_type",
      "object_color_en",
      "scene_zone_en",
      "appearance_notes_en",
      "event_summary_en"
    ],
    "where": [
      {
        "field": "object_type",
        "op": "=",
        "value": "person"
      },
      {
        "field": "scene_zone_en",
        "op": "contains",
        "value": "sidewalk"
      }
    ],
    "order_by": "start_time ASC",
    "limit": 80
  },
  "node_trace": [
    "self_query_node",
    "query_classification_node",
    "parallel_retrieval_fusion_node",
    "final_answer_node",
    "summary_node"
  ],
  "final_answer": "The search found several people on the sidewalk near the left-center baseline area of a basketball court, but most were standing still rather than moving. The top results show individuals remaining mostly motionless during various time intervals in the video.\nSources: [hybrid] basketball_1.mp4 | event_id=basketball_1.mp4_track_8 | 0.0-4.958333333333333; [hybrid] basketball_1.mp4 | event_id=basketball_1.mp4_track_11 | 11.5-91.75; [hybrid] basketball_1.mp4 | event_id=basketball_1.mp4_track_6 | 0.0-17.458333333333332",
  "tool_error": null,
  "error": null,
  "current_node": "summary_node",
  "top5": [
    {
      "event_id": "basketball_1.mp4_track_8",
      "video_id": "basketball_1.mp4",
      "event_text": "Little motion; standing near the left-center baseline area. Located in sidewalk. From 0.0s to 5.0s, a person with unknown color remains mostly still near the left-center baseline area.",
      "distance": 0.28515905141830444
    },
    {
      "event_id": "basketball_1.mp4_track_11",
      "video_id": "basketball_1.mp4",
      "event_text": "Little motion; standing near the left-center baseline area. Located in sidewalk. From 11.5s to 91.8s, a person with unknown color remains mostly still near the left-center baseline area.",
      "distance": 0.2854006886482239
    },
    {
      "event_id": "basketball_1.mp4_track_6",
      "video_id": "basketball_1.mp4",
      "event_text": "Little motion; standing near the left-center baseline area. Located in sidewalk. From 0.0s to 17.5s, a person with unknown color remains mostly still near the left-center baseline area.",
      "distance": 0.28660809993743896
    },
    {
      "event_id": "basketball_1.mp4_track_3",
      "video_id": "basketball_1.mp4",
      "event_text": "Little motion; standing near the left-center baseline area. Located in sidewalk. From 0.0s to 12.0s, a person with unknown color remains mostly still near the left-center baseline area.",
      "distance": 0.28685200214385986
    },
    {
      "event_id": "basketball_1.mp4_track_36",
      "video_id": "basketball_1.mp4",
      "event_text": "Little motion; standing near the left-center court edge. Located in sidewalk. From 62.4s to 64.0s, a person with unknown color remains mostly still near the left-center court edge.",
      "distance": 0.28814852237701416
    }
  ],
  "merged_count": 38,
  "sql_rows_count": 12,
  "hybrid_rows_count": 26,
  "degraded": false,
  "hybrid_summary": "Hybrid direct retrieval complete",
  "sql_summary": "SQL direct retrieval rows=12",
  "hybrid_error": null,
  "sql_error": null,
  "sql_debug": {
    "duration": 2.7442294899992703,
    "sql_summary": "SQL direct retrieval rows=12",
    "hybrid_summary": "Hybrid direct retrieval complete",
    "sql_error": null,
    "hybrid_error": null,
    "fusion_meta": {
      "label": "semantic",
      "weights": {
        "sql": 0.2,
        "hybrid": 0.8
      },
      "rrf_k": 60.0,
      "sql_count": 12,
      "hybrid_count": 26,
      "fused_count": 38,
      "method": "weighted_rrf",
      "degraded": false
    }
  }
}
```

## NEG_SQL_001
- Suite: `negative_regression`
- Priority: `P0`
- Dimensions: `functional, negative`
- Description: Absent object query should not return unrelated rows.
- Query: `Are there any cars in the database?`
- Status: `PASS`
- Avg Latency: `5160.43 ms`
- P95 Latency: `5160.43 ms`
- Node Trace:
```json
[
  "self_query_node",
  "query_classification_node",
  "parallel_retrieval_fusion_node",
  "final_answer_node",
  "summary_node"
]
```
- Routing Metrics:
```json
{
  "execution_mode": "parallel_fusion",
  "label": "structured",
  "query": "Are there any cars in the database",
  "sql_rows_count": 0,
  "hybrid_rows_count": 26,
  "sql_error": null,
  "hybrid_error": null
}
```
- Search Config:
```json
{
  "candidate_limit": 80,
  "top_k_per_event": 20,
  "rerank_top_k": 5,
  "distance_threshold": null,
  "hybrid_alpha": 0.7,
  "hybrid_fallback_alpha": 0.9,
  "hybrid_limit": 50,
  "sql_limit": 80
}
```
- SQL Plan:
```json
{
  "table": "episodic_events",
  "fields": [
    "event_id",
    "video_id",
    "track_id",
    "start_time",
    "end_time",
    "object_type",
    "object_color_en",
    "scene_zone_en",
    "appearance_notes_en",
    "event_summary_en"
  ],
  "where": [
    {
      "field": "object_type",
      "op": "=",
      "value": "car"
    }
  ],
  "order_by": "start_time ASC",
  "limit": 80
}
```
- Self Query Result:
```json
{
  "rewritten_query": "Are there any cars in the database",
  "user_need": "Retrieve basketball video results that satisfy: Are there any cars in the database",
  "intent_label": "structured",
  "retrieval_focus": "structured",
  "key_constraints": [
    "are",
    "there",
    "any",
    "cars",
    "in",
    "the"
  ],
  "ambiguities": [],
  "reasoning_summary": "Fast-path preprocessing kept the original meaning and only normalized surface noise.",
  "confidence": 0.8,
  "original_user_query": "Are there any cars in the database?"
}
```
- Raw Final Answer:
```json
{
  "raw_final_answer": "No matching results found. You can add more specific descriptions like colors or actions."
}
```
- LLM Final Output:
```json
{
  "llm_final_output": "No matching results found. You can add more specific descriptions like colors or actions."
}
```
- Assertions:
```json
[
  {
    "name": "no_runtime_exception",
    "passed": true,
    "actual": [],
    "expected": null,
    "severity": "hard"
  },
  {
    "name": "label_matches",
    "passed": true,
    "actual": "structured",
    "expected": "structured",
    "severity": "hard"
  },
  {
    "name": "route_in_expected",
    "passed": true,
    "actual": "pure_sql",
    "expected": [
      "pure_sql"
    ],
    "severity": "hard"
  },
  {
    "name": "final_answer_present",
    "passed": true,
    "actual": "No matching results found. You can add more specific descriptions like colors or actions.",
    "expected": "non-empty string",
    "severity": "hard"
  },
  {
    "name": "rewritten_query_present",
    "passed": true,
    "actual": "Are there any cars in the database",
    "expected": "non-empty rewritten query",
    "severity": "soft"
  },
  {
    "name": "user_need_identified",
    "passed": true,
    "actual": {
      "rewritten_query": "Are there any cars in the database",
      "user_need": "Retrieve basketball video results that satisfy: Are there any cars in the database",
      "intent_label": "structured",
      "retrieval_focus": "structured",
      "key_constraints": [
        "are",
        "there",
        "any",
        "cars",
        "in",
        "the"
      ],
      "ambiguities": [],
      "reasoning_summary": "Fast-path preprocessing kept the original meaning and only normalized surface noise.",
      "confidence": 0.8,
      "original_user_query": "Are there any cars in the database?"
    },
    "expected": "structured self-query result with user_need",
    "severity": "soft"
  },
  {
    "name": "trace_has_required_nodes",
    "passed": true,
    "actual": [
      "self_query_node",
      "query_classification_node",
      "parallel_retrieval_fusion_node",
      "final_answer_node",
      "summary_node"
    ],
    "expected": [
      "self_query_node",
      "final_answer_node",
      "summary_node"
    ],
    "severity": "soft"
  },
  {
    "name": "routing_metrics_present",
    "passed": true,
    "actual": {
      "execution_mode": "parallel_fusion",
      "label": "structured",
      "query": "Are there any cars in the database",
      "sql_rows_count": 0,
      "hybrid_rows_count": 26,
      "sql_error": null,
      "hybrid_error": null
    },
    "expected": "non-empty routing_metrics",
    "severity": "soft"
  },
  {
    "name": "search_config_present",
    "passed": true,
    "actual": {
      "candidate_limit": 80,
      "top_k_per_event": 20,
      "rerank_top_k": 5,
      "distance_threshold": null,
      "hybrid_alpha": 0.7,
      "hybrid_fallback_alpha": 0.9,
      "hybrid_limit": 50,
      "sql_limit": 80
    },
    "expected": "non-empty search_config",
    "severity": "soft"
  },
  {
    "name": "sql_plan_present",
    "passed": true,
    "actual": {
      "table": "episodic_events",
      "fields": [
        "event_id",
        "video_id",
        "track_id",
        "start_time",
        "end_time",
        "object_type",
        "object_color_en",
        "scene_zone_en",
        "appearance_notes_en",
        "event_summary_en"
      ],
      "where": [
        {
          "field": "object_type",
          "op": "=",
          "value": "car"
        }
      ],
      "order_by": "start_time ASC",
      "limit": 80
    },
    "expected": "non-empty sql_plan",
    "severity": "soft"
  },
  {
    "name": "no_tool_error",
    "passed": true,
    "actual": null,
    "expected": null,
    "severity": "soft"
  },
  {
    "name": "max_results",
    "passed": true,
    "actual": 0,
    "expected": 0,
    "severity": "hard"
  }
]
```
- Last Iteration:
```json
{
  "elapsed_ms": 5160.43,
  "route_mode": "pure_sql",
  "label": "structured",
  "llm_final_output": "No matching results found. You can add more specific descriptions like colors or actions.",
  "raw_final_answer": "No matching results found. You can add more specific descriptions like colors or actions.",
  "rewritten_query": "Are there any cars in the database",
  "original_user_query": "Are there any cars in the database?",
  "self_query_result": {
    "rewritten_query": "Are there any cars in the database",
    "user_need": "Retrieve basketball video results that satisfy: Are there any cars in the database",
    "intent_label": "structured",
    "retrieval_focus": "structured",
    "key_constraints": [
      "are",
      "there",
      "any",
      "cars",
      "in",
      "the"
    ],
    "ambiguities": [],
    "reasoning_summary": "Fast-path preprocessing kept the original meaning and only normalized surface noise.",
    "confidence": 0.8,
    "original_user_query": "Are there any cars in the database?"
  },
  "summary_result": {
    "summary": "No matching results found. You can add more specific descriptions like colors or actions.",
    "style": "empty_result_fallback",
    "confidence": 0.95,
    "citations": []
  },
  "routing_metrics": {
    "execution_mode": "parallel_fusion",
    "label": "structured",
    "query": "Are there any cars in the database",
    "sql_rows_count": 0,
    "hybrid_rows_count": 26,
    "sql_error": null,
    "hybrid_error": null
  },
  "search_config": {
    "candidate_limit": 80,
    "top_k_per_event": 20,
    "rerank_top_k": 5,
    "distance_threshold": null,
    "hybrid_alpha": 0.7,
    "hybrid_fallback_alpha": 0.9,
    "hybrid_limit": 50,
    "sql_limit": 80
  },
  "sql_plan": {
    "table": "episodic_events",
    "fields": [
      "event_id",
      "video_id",
      "track_id",
      "start_time",
      "end_time",
      "object_type",
      "object_color_en",
      "scene_zone_en",
      "appearance_notes_en",
      "event_summary_en"
    ],
    "where": [
      {
        "field": "object_type",
        "op": "=",
        "value": "car"
      }
    ],
    "order_by": "start_time ASC",
    "limit": 80
  },
  "node_trace": [
    "self_query_node",
    "query_classification_node",
    "parallel_retrieval_fusion_node",
    "final_answer_node",
    "summary_node"
  ],
  "final_answer": "No matching results found. You can add more specific descriptions like colors or actions.",
  "tool_error": null,
  "error": null,
  "current_node": "summary_node",
  "top5": [],
  "merged_count": 0,
  "sql_rows_count": 0,
  "hybrid_rows_count": 26,
  "degraded": true,
  "hybrid_summary": "Hybrid direct retrieval complete",
  "sql_summary": "SQL direct retrieval rows=0",
  "hybrid_error": null,
  "sql_error": null,
  "sql_debug": {
    "duration": 3.1649444379982015,
    "sql_summary": "SQL direct retrieval rows=0",
    "hybrid_summary": "Hybrid direct retrieval complete",
    "sql_error": null,
    "hybrid_error": null,
    "fusion_meta": {
      "label": "structured",
      "degraded": true,
      "degraded_reason": "structured_zero_guardrail",
      "method": "prefer_empty_sql_over_loose_semantic"
    }
  }
}
```

## BND_INPUT_001
- Suite: `boundary_inputs`
- Priority: `P1`
- Dimensions: `boundary, resilience`
- Description: Empty query should not crash and should still produce a valid final answer.
- Query: ``
- Status: `PASS`
- Avg Latency: `2568.57 ms`
- P95 Latency: `2568.57 ms`
- Node Trace:
```json
[
  "self_query_node",
  "query_classification_node",
  "parallel_retrieval_fusion_node",
  "final_answer_node",
  "summary_node"
]
```
- Routing Metrics:
```json
{
  "execution_mode": "parallel_fusion",
  "label": "mixed",
  "query": "",
  "sql_rows_count": 27,
  "hybrid_rows_count": 0,
  "sql_error": null,
  "hybrid_error": null
}
```
- Search Config:
```json
{
  "candidate_limit": 80,
  "top_k_per_event": 20,
  "rerank_top_k": 5,
  "distance_threshold": null,
  "hybrid_alpha": 0.7,
  "hybrid_fallback_alpha": 0.9,
  "hybrid_limit": 50,
  "sql_limit": 80
}
```
- SQL Plan:
```json
{
  "table": "episodic_events",
  "fields": [
    "event_id",
    "video_id",
    "track_id",
    "start_time",
    "end_time",
    "object_type",
    "object_color_en",
    "scene_zone_en",
    "appearance_notes_en",
    "event_summary_en"
  ],
  "where": [],
  "order_by": "start_time ASC",
  "limit": 80
}
```
- Self Query Result:
```json
{
  "rewritten_query": "",
  "user_need": "Find relevant basketball retrieval results from the user's request.",
  "intent_label": "mixed",
  "retrieval_focus": "mixed",
  "key_constraints": [],
  "ambiguities": [],
  "reasoning_summary": "Fallback to the original query because self-query preprocessing was unavailable.",
  "confidence": 0.35,
  "original_user_query": ""
}
```
- Raw Final Answer:
```json
{
  "raw_final_answer": "Retrieval complete. Most relevant results:\n[1] event_id=1 | video=basketball_1.mp4 | distance=0.0 | summary=From 0.0s to 61.2s, a person with unknown color stays mostly still near the left baseline/bench area.\n[2] event_id=2 | video=basketball_1.mp4 | distance=0.0 | summary=From 0.0s to 16.1s, a person with unknown color remains mostly still near the left-center baseline area.\n[3] event_id=3 | video=basketball_1.mp4 | distance=0.0 | summary=From 0.0s to 12.0s, a person with unknown color remains mostly still near the left-center baseline area.\n[4] event_id=4 | video=basketball_1.mp4 | distance=0.0 | summary=From 0.0s to 143.1s, a person with unknown color stays mostly still near the lower-left court/bench area.\n[5] event_id=5 | video=basketball_1.mp4 | distance=0.0 | summary=From 0.0s to 17.5s, a person with unknown color remains mostly still near the left-center baseline area."
}
```
- LLM Final Output:
```json
{
  "llm_final_output": "In the video *basketball_1.mp4*, multiple clips show a person in an unknown-colored outfit staying mostly still near the left baseline or bench area, with durations ranging from about 12 to 143 seconds.\nSources: [sql] basketball_1.mp4 | event_id=1 | 0.0-61.208333333333336; [sql] basketball_1.mp4 | event_id=2 | 0.0-16.083333333333332; [sql] basketball_1.mp4 | event_id=3 | 0.0-12.041666666666666"
}
```
- Assertions:
```json
[
  {
    "name": "no_runtime_exception",
    "passed": true,
    "actual": [],
    "expected": null,
    "severity": "hard"
  },
  {
    "name": "route_in_expected",
    "passed": true,
    "actual": "hybrid_search",
    "expected": [
      "hybrid_search",
      "pure_sql"
    ],
    "severity": "hard"
  },
  {
    "name": "final_answer_present",
    "passed": true,
    "actual": "In the video *basketball_1.mp4*, multiple clips show a person in an unknown-colored outfit staying mostly still near the left baseline or bench area, with durations ranging from about 12 to 143 seconds.\nSources: [sql] basketball_1.mp4 | event_id=1 | 0.0-61.208333333333336; [sql] basketball_1.mp4 | event_id=2 | 0.0-16.083333333333332; [sql] basketball_1.mp4 | event_id=3 | 0.0-12.041666666666666",
    "expected": "non-empty string",
    "severity": "hard"
  },
  {
    "name": "citation_present",
    "passed": true,
    "actual": "In the video *basketball_1.mp4*, multiple clips show a person in an unknown-colored outfit staying mostly still near the left baseline or bench area, with durations ranging from about 12 to 143 seconds.\nSources: [sql] basketball_1.mp4 | event_id=1 | 0.0-61.208333333333336; [sql] basketball_1.mp4 | event_id=2 | 0.0-16.083333333333332; [sql] basketball_1.mp4 | event_id=3 | 0.0-12.041666666666666",
    "expected": "final answer contains Sources:",
    "severity": "soft"
  },
  {
    "name": "grounding_coverage",
    "passed": true,
    "actual": {
      "summary": "In the video *basketball_1.mp4*, multiple clips show a person in an unknown-colored outfit staying mostly still near the left baseline or bench area, with durations ranging from about 12 to 143 seconds.",
      "style": "llm_summary",
      "confidence": 0.8,
      "citations": [
        {
          "source_type": "sql",
          "video_id": "basketball_1.mp4",
          "event_id": 1,
          "start_time": 0.0,
          "end_time": 61.208333333333336
        },
        {
          "source_type": "sql",
          "video_id": "basketball_1.mp4",
          "event_id": 2,
          "start_time": 0.0,
          "end_time": 16.083333333333332
        },
        {
          "source_type": "sql",
          "video_id": "basketball_1.mp4",
          "event_id": 3,
          "start_time": 0.0,
          "end_time": 12.041666666666666
        }
      ]
    },
    "expected": "summary_result.citations is non-empty",
    "severity": "soft"
  },
  {
    "name": "trace_has_required_nodes",
    "passed": true,
    "actual": [
      "self_query_node",
      "query_classification_node",
      "parallel_retrieval_fusion_node",
      "final_answer_node",
      "summary_node"
    ],
    "expected": [
      "self_query_node",
      "final_answer_node",
      "summary_node"
    ],
    "severity": "soft"
  },
  {
    "name": "routing_metrics_present",
    "passed": true,
    "actual": {
      "execution_mode": "parallel_fusion",
      "label": "mixed",
      "query": "",
      "sql_rows_count": 27,
      "hybrid_rows_count": 0,
      "sql_error": null,
      "hybrid_error": null
    },
    "expected": "non-empty routing_metrics",
    "severity": "soft"
  },
  {
    "name": "search_config_present",
    "passed": true,
    "actual": {
      "candidate_limit": 80,
      "top_k_per_event": 20,
      "rerank_top_k": 5,
      "distance_threshold": null,
      "hybrid_alpha": 0.7,
      "hybrid_fallback_alpha": 0.9,
      "hybrid_limit": 50,
      "sql_limit": 80
    },
    "expected": "non-empty search_config",
    "severity": "soft"
  },
  {
    "name": "no_tool_error",
    "passed": true,
    "actual": null,
    "expected": null,
    "severity": "soft"
  }
]
```
- Last Iteration:
```json
{
  "elapsed_ms": 2568.57,
  "route_mode": "hybrid_search",
  "label": "mixed",
  "llm_final_output": "In the video *basketball_1.mp4*, multiple clips show a person in an unknown-colored outfit staying mostly still near the left baseline or bench area, with durations ranging from about 12 to 143 seconds.\nSources: [sql] basketball_1.mp4 | event_id=1 | 0.0-61.208333333333336; [sql] basketball_1.mp4 | event_id=2 | 0.0-16.083333333333332; [sql] basketball_1.mp4 | event_id=3 | 0.0-12.041666666666666",
  "raw_final_answer": "Retrieval complete. Most relevant results:\n[1] event_id=1 | video=basketball_1.mp4 | distance=0.0 | summary=From 0.0s to 61.2s, a person with unknown color stays mostly still near the left baseline/bench area.\n[2] event_id=2 | video=basketball_1.mp4 | distance=0.0 | summary=From 0.0s to 16.1s, a person with unknown color remains mostly still near the left-center baseline area.\n[3] event_id=3 | video=basketball_1.mp4 | distance=0.0 | summary=From 0.0s to 12.0s, a person with unknown color remains mostly still near the left-center baseline area.\n[4] event_id=4 | video=basketball_1.mp4 | distance=0.0 | summary=From 0.0s to 143.1s, a person with unknown color stays mostly still near the lower-left court/bench area.\n[5] event_id=5 | video=basketball_1.mp4 | distance=0.0 | summary=From 0.0s to 17.5s, a person with unknown color remains mostly still near the left-center baseline area.",
  "rewritten_query": "",
  "original_user_query": "",
  "self_query_result": {
    "rewritten_query": "",
    "user_need": "Find relevant basketball retrieval results from the user's request.",
    "intent_label": "mixed",
    "retrieval_focus": "mixed",
    "key_constraints": [],
    "ambiguities": [],
    "reasoning_summary": "Fallback to the original query because self-query preprocessing was unavailable.",
    "confidence": 0.35,
    "original_user_query": ""
  },
  "summary_result": {
    "summary": "In the video *basketball_1.mp4*, multiple clips show a person in an unknown-colored outfit staying mostly still near the left baseline or bench area, with durations ranging from about 12 to 143 seconds.",
    "style": "llm_summary",
    "confidence": 0.8,
    "citations": [
      {
        "source_type": "sql",
        "video_id": "basketball_1.mp4",
        "event_id": 1,
        "start_time": 0.0,
        "end_time": 61.208333333333336
      },
      {
        "source_type": "sql",
        "video_id": "basketball_1.mp4",
        "event_id": 2,
        "start_time": 0.0,
        "end_time": 16.083333333333332
      },
      {
        "source_type": "sql",
        "video_id": "basketball_1.mp4",
        "event_id": 3,
        "start_time": 0.0,
        "end_time": 12.041666666666666
      }
    ]
  },
  "routing_metrics": {
    "execution_mode": "parallel_fusion",
    "label": "mixed",
    "query": "",
    "sql_rows_count": 27,
    "hybrid_rows_count": 0,
    "sql_error": null,
    "hybrid_error": null
  },
  "search_config": {
    "candidate_limit": 80,
    "top_k_per_event": 20,
    "rerank_top_k": 5,
    "distance_threshold": null,
    "hybrid_alpha": 0.7,
    "hybrid_fallback_alpha": 0.9,
    "hybrid_limit": 50,
    "sql_limit": 80
  },
  "sql_plan": {
    "table": "episodic_events",
    "fields": [
      "event_id",
      "video_id",
      "track_id",
      "start_time",
      "end_time",
      "object_type",
      "object_color_en",
      "scene_zone_en",
      "appearance_notes_en",
      "event_summary_en"
    ],
    "where": [],
    "order_by": "start_time ASC",
    "limit": 80
  },
  "node_trace": [
    "self_query_node",
    "query_classification_node",
    "parallel_retrieval_fusion_node",
    "final_answer_node",
    "summary_node"
  ],
  "final_answer": "In the video *basketball_1.mp4*, multiple clips show a person in an unknown-colored outfit staying mostly still near the left baseline or bench area, with durations ranging from about 12 to 143 seconds.\nSources: [sql] basketball_1.mp4 | event_id=1 | 0.0-61.208333333333336; [sql] basketball_1.mp4 | event_id=2 | 0.0-16.083333333333332; [sql] basketball_1.mp4 | event_id=3 | 0.0-12.041666666666666",
  "tool_error": null,
  "error": null,
  "current_node": "summary_node",
  "top5": [
    {
      "event_id": 1,
      "video_id": "basketball_1.mp4",
      "event_text": "From 0.0s to 61.2s, a person with unknown color stays mostly still near the left baseline/bench area.",
      "distance": 0.0
    },
    {
      "event_id": 2,
      "video_id": "basketball_1.mp4",
      "event_text": "From 0.0s to 16.1s, a person with unknown color remains mostly still near the left-center baseline area.",
      "distance": 0.0
    },
    {
      "event_id": 3,
      "video_id": "basketball_1.mp4",
      "event_text": "From 0.0s to 12.0s, a person with unknown color remains mostly still near the left-center baseline area.",
      "distance": 0.0
    },
    {
      "event_id": 4,
      "video_id": "basketball_1.mp4",
      "event_text": "From 0.0s to 143.1s, a person with unknown color stays mostly still near the lower-left court/bench area.",
      "distance": 0.0
    },
    {
      "event_id": 5,
      "video_id": "basketball_1.mp4",
      "event_text": "From 0.0s to 17.5s, a person with unknown color remains mostly still near the left-center baseline area.",
      "distance": 0.0
    }
  ],
  "merged_count": 27,
  "sql_rows_count": 27,
  "hybrid_rows_count": 0,
  "degraded": false,
  "hybrid_summary": "Hybrid retrieval skipped: empty query",
  "sql_summary": "SQL direct retrieval rows=27",
  "hybrid_error": null,
  "sql_error": null,
  "sql_debug": {
    "duration": 0.0004402429985930212,
    "sql_summary": "SQL direct retrieval rows=27",
    "hybrid_summary": "Hybrid retrieval skipped: empty query",
    "sql_error": null,
    "hybrid_error": null,
    "fusion_meta": {
      "label": "mixed",
      "weights": {
        "sql": 0.5,
        "hybrid": 0.5
      },
      "rrf_k": 60.0,
      "sql_count": 27,
      "hybrid_count": 0,
      "fused_count": 27,
      "method": "weighted_rrf",
      "degraded": false
    }
  }
}
```

## BND_INPUT_002
- Suite: `boundary_inputs`
- Priority: `P1`
- Dimensions: `boundary, routing`
- Description: Short query should still be classified and answered consistently.
- Query: `person`
- Status: `PASS`
- Avg Latency: `6419.02 ms`
- P95 Latency: `6419.02 ms`
- Node Trace:
```json
[
  "self_query_node",
  "query_classification_node",
  "parallel_retrieval_fusion_node",
  "final_answer_node",
  "summary_node"
]
```
- Routing Metrics:
```json
{
  "execution_mode": "parallel_fusion",
  "label": "structured",
  "query": "person",
  "sql_rows_count": 27,
  "hybrid_rows_count": 26,
  "sql_error": null,
  "hybrid_error": null
}
```
- Search Config:
```json
{
  "candidate_limit": 80,
  "top_k_per_event": 20,
  "rerank_top_k": 5,
  "distance_threshold": null,
  "hybrid_alpha": 0.7,
  "hybrid_fallback_alpha": 0.9,
  "hybrid_limit": 50,
  "sql_limit": 80
}
```
- SQL Plan:
```json
{
  "table": "episodic_events",
  "fields": [
    "event_id",
    "video_id",
    "track_id",
    "start_time",
    "end_time",
    "object_type",
    "object_color_en",
    "scene_zone_en",
    "appearance_notes_en",
    "event_summary_en"
  ],
  "where": [
    {
      "field": "object_type",
      "op": "=",
      "value": "person"
    }
  ],
  "order_by": "start_time ASC",
  "limit": 80
}
```
- Self Query Result:
```json
{
  "rewritten_query": "person",
  "user_need": "Retrieve basketball video results that satisfy: person",
  "intent_label": "structured",
  "retrieval_focus": "structured",
  "key_constraints": [
    "person"
  ],
  "ambiguities": [],
  "reasoning_summary": "Fast-path preprocessing kept the original meaning and only normalized surface noise.",
  "confidence": 0.8,
  "original_user_query": "person"
}
```
- Raw Final Answer:
```json
{
  "raw_final_answer": "Retrieval complete. Most relevant results:\n[1] event_id=1 | video=basketball_1.mp4 | distance=0.0 | summary=From 0.0s to 61.2s, a person with unknown color stays mostly still near the left baseline/bench area.\n[2] event_id=2 | video=basketball_1.mp4 | distance=0.0 | summary=From 0.0s to 16.1s, a person with unknown color remains mostly still near the left-center baseline area.\n[3] event_id=3 | video=basketball_1.mp4 | distance=0.0 | summary=From 0.0s to 12.0s, a person with unknown color remains mostly still near the left-center baseline area.\n[4] event_id=4 | video=basketball_1.mp4 | distance=0.0 | summary=From 0.0s to 143.1s, a person with unknown color stays mostly still near the lower-left court/bench area.\n[5] event_id=5 | video=basketball_1.mp4 | distance=0.0 | summary=From 0.0s to 17.5s, a person with unknown color remains mostly still near the left-center baseline area."
}
```
- LLM Final Output:
```json
{
  "llm_final_output": "In the video, a person (color unspecified) is seen staying mostly still near the left baseline or bench area. This occurs in multiple short clips, with the longest lasting about 61 seconds and others ranging from 12 to 17 seconds—all within the first few minutes of the footage.\nSources: [sql] basketball_1.mp4 | event_id=1 | 0.0-61.208333333333336; [sql] basketball_1.mp4 | event_id=2 | 0.0-16.083333333333332; [sql] basketball_1.mp4 | event_id=3 | 0.0-12.041666666666666"
}
```
- Assertions:
```json
[
  {
    "name": "no_runtime_exception",
    "passed": true,
    "actual": [],
    "expected": null,
    "severity": "hard"
  },
  {
    "name": "label_matches",
    "passed": true,
    "actual": "structured",
    "expected": "structured",
    "severity": "hard"
  },
  {
    "name": "route_in_expected",
    "passed": true,
    "actual": "pure_sql",
    "expected": [
      "pure_sql"
    ],
    "severity": "hard"
  },
  {
    "name": "final_answer_present",
    "passed": true,
    "actual": "In the video, a person (color unspecified) is seen staying mostly still near the left baseline or bench area. This occurs in multiple short clips, with the longest lasting about 61 seconds and others ranging from 12 to 17 seconds—all within the first few minutes of the footage.\nSources: [sql] basketball_1.mp4 | event_id=1 | 0.0-61.208333333333336; [sql] basketball_1.mp4 | event_id=2 | 0.0-16.083333333333332; [sql] basketball_1.mp4 | event_id=3 | 0.0-12.041666666666666",
    "expected": "non-empty string",
    "severity": "hard"
  },
  {
    "name": "citation_present",
    "passed": true,
    "actual": "In the video, a person (color unspecified) is seen staying mostly still near the left baseline or bench area. This occurs in multiple short clips, with the longest lasting about 61 seconds and others ranging from 12 to 17 seconds—all within the first few minutes of the footage.\nSources: [sql] basketball_1.mp4 | event_id=1 | 0.0-61.208333333333336; [sql] basketball_1.mp4 | event_id=2 | 0.0-16.083333333333332; [sql] basketball_1.mp4 | event_id=3 | 0.0-12.041666666666666",
    "expected": "final answer contains Sources:",
    "severity": "soft"
  },
  {
    "name": "grounding_coverage",
    "passed": true,
    "actual": {
      "summary": "In the video, a person (color unspecified) is seen staying mostly still near the left baseline or bench area. This occurs in multiple short clips, with the longest lasting about 61 seconds and others ranging from 12 to 17 seconds—all within the first few minutes of the footage.",
      "style": "llm_summary",
      "confidence": 0.8,
      "citations": [
        {
          "source_type": "sql",
          "video_id": "basketball_1.mp4",
          "event_id": 1,
          "start_time": 0.0,
          "end_time": 61.208333333333336
        },
        {
          "source_type": "sql",
          "video_id": "basketball_1.mp4",
          "event_id": 2,
          "start_time": 0.0,
          "end_time": 16.083333333333332
        },
        {
          "source_type": "sql",
          "video_id": "basketball_1.mp4",
          "event_id": 3,
          "start_time": 0.0,
          "end_time": 12.041666666666666
        }
      ]
    },
    "expected": "summary_result.citations is non-empty",
    "severity": "soft"
  },
  {
    "name": "rewritten_query_present",
    "passed": true,
    "actual": "person",
    "expected": "non-empty rewritten query",
    "severity": "soft"
  },
  {
    "name": "user_need_identified",
    "passed": true,
    "actual": {
      "rewritten_query": "person",
      "user_need": "Retrieve basketball video results that satisfy: person",
      "intent_label": "structured",
      "retrieval_focus": "structured",
      "key_constraints": [
        "person"
      ],
      "ambiguities": [],
      "reasoning_summary": "Fast-path preprocessing kept the original meaning and only normalized surface noise.",
      "confidence": 0.8,
      "original_user_query": "person"
    },
    "expected": "structured self-query result with user_need",
    "severity": "soft"
  },
  {
    "name": "trace_has_required_nodes",
    "passed": true,
    "actual": [
      "self_query_node",
      "query_classification_node",
      "parallel_retrieval_fusion_node",
      "final_answer_node",
      "summary_node"
    ],
    "expected": [
      "self_query_node",
      "final_answer_node",
      "summary_node"
    ],
    "severity": "soft"
  },
  {
    "name": "routing_metrics_present",
    "passed": true,
    "actual": {
      "execution_mode": "parallel_fusion",
      "label": "structured",
      "query": "person",
      "sql_rows_count": 27,
      "hybrid_rows_count": 26,
      "sql_error": null,
      "hybrid_error": null
    },
    "expected": "non-empty routing_metrics",
    "severity": "soft"
  },
  {
    "name": "search_config_present",
    "passed": true,
    "actual": {
      "candidate_limit": 80,
      "top_k_per_event": 20,
      "rerank_top_k": 5,
      "distance_threshold": null,
      "hybrid_alpha": 0.7,
      "hybrid_fallback_alpha": 0.9,
      "hybrid_limit": 50,
      "sql_limit": 80
    },
    "expected": "non-empty search_config",
    "severity": "soft"
  },
  {
    "name": "sql_plan_present",
    "passed": true,
    "actual": {
      "table": "episodic_events",
      "fields": [
        "event_id",
        "video_id",
        "track_id",
        "start_time",
        "end_time",
        "object_type",
        "object_color_en",
        "scene_zone_en",
        "appearance_notes_en",
        "event_summary_en"
      ],
      "where": [
        {
          "field": "object_type",
          "op": "=",
          "value": "person"
        }
      ],
      "order_by": "start_time ASC",
      "limit": 80
    },
    "expected": "non-empty sql_plan",
    "severity": "soft"
  },
  {
    "name": "no_tool_error",
    "passed": true,
    "actual": null,
    "expected": null,
    "severity": "soft"
  },
  {
    "name": "min_results",
    "passed": true,
    "actual": 50,
    "expected": 1,
    "severity": "hard"
  },
  {
    "name": "min_sql_rows",
    "passed": true,
    "actual": 27,
    "expected": 1,
    "severity": "hard"
  }
]
```
- Last Iteration:
```json
{
  "elapsed_ms": 6419.02,
  "route_mode": "pure_sql",
  "label": "structured",
  "llm_final_output": "In the video, a person (color unspecified) is seen staying mostly still near the left baseline or bench area. This occurs in multiple short clips, with the longest lasting about 61 seconds and others ranging from 12 to 17 seconds—all within the first few minutes of the footage.\nSources: [sql] basketball_1.mp4 | event_id=1 | 0.0-61.208333333333336; [sql] basketball_1.mp4 | event_id=2 | 0.0-16.083333333333332; [sql] basketball_1.mp4 | event_id=3 | 0.0-12.041666666666666",
  "raw_final_answer": "Retrieval complete. Most relevant results:\n[1] event_id=1 | video=basketball_1.mp4 | distance=0.0 | summary=From 0.0s to 61.2s, a person with unknown color stays mostly still near the left baseline/bench area.\n[2] event_id=2 | video=basketball_1.mp4 | distance=0.0 | summary=From 0.0s to 16.1s, a person with unknown color remains mostly still near the left-center baseline area.\n[3] event_id=3 | video=basketball_1.mp4 | distance=0.0 | summary=From 0.0s to 12.0s, a person with unknown color remains mostly still near the left-center baseline area.\n[4] event_id=4 | video=basketball_1.mp4 | distance=0.0 | summary=From 0.0s to 143.1s, a person with unknown color stays mostly still near the lower-left court/bench area.\n[5] event_id=5 | video=basketball_1.mp4 | distance=0.0 | summary=From 0.0s to 17.5s, a person with unknown color remains mostly still near the left-center baseline area.",
  "rewritten_query": "person",
  "original_user_query": "person",
  "self_query_result": {
    "rewritten_query": "person",
    "user_need": "Retrieve basketball video results that satisfy: person",
    "intent_label": "structured",
    "retrieval_focus": "structured",
    "key_constraints": [
      "person"
    ],
    "ambiguities": [],
    "reasoning_summary": "Fast-path preprocessing kept the original meaning and only normalized surface noise.",
    "confidence": 0.8,
    "original_user_query": "person"
  },
  "summary_result": {
    "summary": "In the video, a person (color unspecified) is seen staying mostly still near the left baseline or bench area. This occurs in multiple short clips, with the longest lasting about 61 seconds and others ranging from 12 to 17 seconds—all within the first few minutes of the footage.",
    "style": "llm_summary",
    "confidence": 0.8,
    "citations": [
      {
        "source_type": "sql",
        "video_id": "basketball_1.mp4",
        "event_id": 1,
        "start_time": 0.0,
        "end_time": 61.208333333333336
      },
      {
        "source_type": "sql",
        "video_id": "basketball_1.mp4",
        "event_id": 2,
        "start_time": 0.0,
        "end_time": 16.083333333333332
      },
      {
        "source_type": "sql",
        "video_id": "basketball_1.mp4",
        "event_id": 3,
        "start_time": 0.0,
        "end_time": 12.041666666666666
      }
    ]
  },
  "routing_metrics": {
    "execution_mode": "parallel_fusion",
    "label": "structured",
    "query": "person",
    "sql_rows_count": 27,
    "hybrid_rows_count": 26,
    "sql_error": null,
    "hybrid_error": null
  },
  "search_config": {
    "candidate_limit": 80,
    "top_k_per_event": 20,
    "rerank_top_k": 5,
    "distance_threshold": null,
    "hybrid_alpha": 0.7,
    "hybrid_fallback_alpha": 0.9,
    "hybrid_limit": 50,
    "sql_limit": 80
  },
  "sql_plan": {
    "table": "episodic_events",
    "fields": [
      "event_id",
      "video_id",
      "track_id",
      "start_time",
      "end_time",
      "object_type",
      "object_color_en",
      "scene_zone_en",
      "appearance_notes_en",
      "event_summary_en"
    ],
    "where": [
      {
        "field": "object_type",
        "op": "=",
        "value": "person"
      }
    ],
    "order_by": "start_time ASC",
    "limit": 80
  },
  "node_trace": [
    "self_query_node",
    "query_classification_node",
    "parallel_retrieval_fusion_node",
    "final_answer_node",
    "summary_node"
  ],
  "final_answer": "In the video, a person (color unspecified) is seen staying mostly still near the left baseline or bench area. This occurs in multiple short clips, with the longest lasting about 61 seconds and others ranging from 12 to 17 seconds—all within the first few minutes of the footage.\nSources: [sql] basketball_1.mp4 | event_id=1 | 0.0-61.208333333333336; [sql] basketball_1.mp4 | event_id=2 | 0.0-16.083333333333332; [sql] basketball_1.mp4 | event_id=3 | 0.0-12.041666666666666",
  "tool_error": null,
  "error": null,
  "current_node": "summary_node",
  "top5": [
    {
      "event_id": 1,
      "video_id": "basketball_1.mp4",
      "event_text": "From 0.0s to 61.2s, a person with unknown color stays mostly still near the left baseline/bench area.",
      "distance": 0.0
    },
    {
      "event_id": 2,
      "video_id": "basketball_1.mp4",
      "event_text": "From 0.0s to 16.1s, a person with unknown color remains mostly still near the left-center baseline area.",
      "distance": 0.0
    },
    {
      "event_id": 3,
      "video_id": "basketball_1.mp4",
      "event_text": "From 0.0s to 12.0s, a person with unknown color remains mostly still near the left-center baseline area.",
      "distance": 0.0
    },
    {
      "event_id": 4,
      "video_id": "basketball_1.mp4",
      "event_text": "From 0.0s to 143.1s, a person with unknown color stays mostly still near the lower-left court/bench area.",
      "distance": 0.0
    },
    {
      "event_id": 5,
      "video_id": "basketball_1.mp4",
      "event_text": "From 0.0s to 17.5s, a person with unknown color remains mostly still near the left-center baseline area.",
      "distance": 0.0
    }
  ],
  "merged_count": 50,
  "sql_rows_count": 27,
  "hybrid_rows_count": 26,
  "degraded": false,
  "hybrid_summary": "Hybrid direct retrieval complete",
  "sql_summary": "SQL direct retrieval rows=27",
  "hybrid_error": null,
  "sql_error": null,
  "sql_debug": {
    "duration": 1.4413644239975838,
    "sql_summary": "SQL direct retrieval rows=27",
    "hybrid_summary": "Hybrid direct retrieval complete",
    "sql_error": null,
    "hybrid_error": null,
    "fusion_meta": {
      "label": "structured",
      "weights": {
        "sql": 0.8,
        "hybrid": 0.2
      },
      "rrf_k": 60.0,
      "sql_count": 27,
      "hybrid_count": 26,
      "fused_count": 50,
      "method": "weighted_rrf",
      "degraded": false
    }
  }
}
```

## RES_INPUT_001
- Suite: `resilience_inputs`
- Priority: `P1`
- Dimensions: `resilience, semantic`
- Description: Noisy punctuation and mixed casing should still preserve semantic routing intent.
- Query: `!!! Find A PERSON near the LEFT BLEACHERS ???`
- Status: `PASS`
- Avg Latency: `8463.01 ms`
- P95 Latency: `8463.01 ms`
- Node Trace:
```json
[
  "self_query_node",
  "query_classification_node",
  "parallel_retrieval_fusion_node",
  "final_answer_node",
  "summary_node"
]
```
- Routing Metrics:
```json
{
  "execution_mode": "parallel_fusion",
  "label": "semantic",
  "query": "Find A PERSON near the LEFT BLEACHERS",
  "sql_rows_count": 1,
  "hybrid_rows_count": 26,
  "sql_error": null,
  "hybrid_error": null
}
```
- Search Config:
```json
{
  "candidate_limit": 80,
  "top_k_per_event": 20,
  "rerank_top_k": 5,
  "distance_threshold": null,
  "hybrid_alpha": 0.7,
  "hybrid_fallback_alpha": 0.9,
  "hybrid_limit": 50,
  "sql_limit": 80
}
```
- SQL Plan:
```json
{
  "table": "episodic_events",
  "fields": [
    "event_id",
    "video_id",
    "track_id",
    "start_time",
    "end_time",
    "object_type",
    "object_color_en",
    "scene_zone_en",
    "appearance_notes_en",
    "event_summary_en"
  ],
  "where": [
    {
      "field": "object_type",
      "op": "=",
      "value": "person"
    },
    {
      "field": "scene_zone_en",
      "op": "contains",
      "value": "left bleachers"
    }
  ],
  "order_by": "start_time ASC",
  "limit": 80
}
```
- Self Query Result:
```json
{
  "rewritten_query": "Find A PERSON near the LEFT BLEACHERS",
  "user_need": "Retrieve basketball video results that satisfy: Find A PERSON near the LEFT BLEACHERS",
  "intent_label": "semantic",
  "retrieval_focus": "semantic",
  "key_constraints": [
    "find",
    "a",
    "person",
    "near",
    "the",
    "left"
  ],
  "ambiguities": [],
  "reasoning_summary": "Fast-path preprocessing kept the original meaning and only normalized surface noise.",
  "confidence": 0.8,
  "original_user_query": "!!! Find A PERSON near the LEFT BLEACHERS ???"
}
```
- Raw Final Answer:
```json
{
  "raw_final_answer": "Retrieval complete. Most relevant results:\n[1] event_id=basketball_2.mp4_track_id_1 | video=basketball_2.mp4 | distance=0.23945021629333496 | summary=standing near left bleachers with little motion Located in left bleachers. From 0.00s to 30.84s, a dark-clothed person stands near the left bleachers with little motion.\n[2] event_id=basketball_1.mp4_track_1 | video=basketball_1.mp4 | distance=0.33325302600860596 | summary=Little motion; standing near the left baseline/bench area. Located in sidewalk. From 0.0s to 61.2s, a person with unknown color stays mostly still near the left baseline/bench area.\n[3] event_id=basketball_2.mp4_track_id_5 | video=basketball_2.mp4 | distance=0.35027164220809937 | summary=standing near left side with little motion Located in left side. From 0.00s to 9.96s, a dark-clothed person stands near the left side with little motion.\n[4] event_id=basketball_1.mp4_track_29 | video=basketball_1.mp4 | distance=0.3522948622703552 | summary=Little motion; standing near the left side of the court. Located in sidewalk. From 43.8s to 125.7s, a person with unknown color remains mostly still near the left side of the court.\n[5] event_id=basketball_1.mp4_track_30 | video=basketball_1.mp4 | distance=0.3453550934791565 | summary=Little motion; standing near the left-center court area. Located in sidewalk. From 47.8s to 48.8s, a person with unknown color remains mostly still near the left-center court area."
}
```
- LLM Final Output:
```json
{
  "llm_final_output": "A dark-clothed person is seen standing near the left bleachers with little motion from 0.00s to 30.84s in *basketball_2.mp4*. Another person remains mostly still near the left baseline/bench area from 0.0s to 61.2s in *basketball_1.mp4*. Additional similar sightings occur on the left side of the court in both videos.\nSources: [hybrid] basketball_2.mp4 | event_id=basketball_2.mp4_track_id_1 | 0.0-30.84; [hybrid] basketball_1.mp4 | event_id=basketball_1.mp4_track_1 | 0.0-61.208333333333336; [hybrid] basketball_2.mp4 | event_id=basketball_2.mp4_track_id_5 | 0.0-9.96"
}
```
- Assertions:
```json
[
  {
    "name": "no_runtime_exception",
    "passed": true,
    "actual": [],
    "expected": null,
    "severity": "hard"
  },
  {
    "name": "route_in_expected",
    "passed": true,
    "actual": "hybrid_search",
    "expected": [
      "hybrid_search"
    ],
    "severity": "hard"
  },
  {
    "name": "final_answer_present",
    "passed": true,
    "actual": "A dark-clothed person is seen standing near the left bleachers with little motion from 0.00s to 30.84s in *basketball_2.mp4*. Another person remains mostly still near the left baseline/bench area from 0.0s to 61.2s in *basketball_1.mp4*. Additional similar sightings occur on the left side of the court in both videos.\nSources: [hybrid] basketball_2.mp4 | event_id=basketball_2.mp4_track_id_1 | 0.0-30.84; [hybrid] basketball_1.mp4 | event_id=basketball_1.mp4_track_1 | 0.0-61.208333333333336; [hybrid] basketball_2.mp4 | event_id=basketball_2.mp4_track_id_5 | 0.0-9.96",
    "expected": "non-empty string",
    "severity": "hard"
  },
  {
    "name": "citation_present",
    "passed": true,
    "actual": "A dark-clothed person is seen standing near the left bleachers with little motion from 0.00s to 30.84s in *basketball_2.mp4*. Another person remains mostly still near the left baseline/bench area from 0.0s to 61.2s in *basketball_1.mp4*. Additional similar sightings occur on the left side of the court in both videos.\nSources: [hybrid] basketball_2.mp4 | event_id=basketball_2.mp4_track_id_1 | 0.0-30.84; [hybrid] basketball_1.mp4 | event_id=basketball_1.mp4_track_1 | 0.0-61.208333333333336; [hybrid] basketball_2.mp4 | event_id=basketball_2.mp4_track_id_5 | 0.0-9.96",
    "expected": "final answer contains Sources:",
    "severity": "soft"
  },
  {
    "name": "grounding_coverage",
    "passed": true,
    "actual": {
      "summary": "A dark-clothed person is seen standing near the left bleachers with little motion from 0.00s to 30.84s in *basketball_2.mp4*. Another person remains mostly still near the left baseline/bench area from 0.0s to 61.2s in *basketball_1.mp4*. Additional similar sightings occur on the left side of the court in both videos.",
      "style": "llm_summary",
      "confidence": 0.8,
      "citations": [
        {
          "source_type": "hybrid",
          "video_id": "basketball_2.mp4",
          "event_id": "basketball_2.mp4_track_id_1",
          "start_time": 0.0,
          "end_time": 30.84
        },
        {
          "source_type": "hybrid",
          "video_id": "basketball_1.mp4",
          "event_id": "basketball_1.mp4_track_1",
          "start_time": 0.0,
          "end_time": 61.208333333333336
        },
        {
          "source_type": "hybrid",
          "video_id": "basketball_2.mp4",
          "event_id": "basketball_2.mp4_track_id_5",
          "start_time": 0.0,
          "end_time": 9.96
        }
      ]
    },
    "expected": "summary_result.citations is non-empty",
    "severity": "soft"
  },
  {
    "name": "rewritten_query_present",
    "passed": true,
    "actual": "Find A PERSON near the LEFT BLEACHERS",
    "expected": "non-empty rewritten query",
    "severity": "soft"
  },
  {
    "name": "user_need_identified",
    "passed": true,
    "actual": {
      "rewritten_query": "Find A PERSON near the LEFT BLEACHERS",
      "user_need": "Retrieve basketball video results that satisfy: Find A PERSON near the LEFT BLEACHERS",
      "intent_label": "semantic",
      "retrieval_focus": "semantic",
      "key_constraints": [
        "find",
        "a",
        "person",
        "near",
        "the",
        "left"
      ],
      "ambiguities": [],
      "reasoning_summary": "Fast-path preprocessing kept the original meaning and only normalized surface noise.",
      "confidence": 0.8,
      "original_user_query": "!!! Find A PERSON near the LEFT BLEACHERS ???"
    },
    "expected": "structured self-query result with user_need",
    "severity": "soft"
  },
  {
    "name": "trace_has_required_nodes",
    "passed": true,
    "actual": [
      "self_query_node",
      "query_classification_node",
      "parallel_retrieval_fusion_node",
      "final_answer_node",
      "summary_node"
    ],
    "expected": [
      "self_query_node",
      "final_answer_node",
      "summary_node"
    ],
    "severity": "soft"
  },
  {
    "name": "routing_metrics_present",
    "passed": true,
    "actual": {
      "execution_mode": "parallel_fusion",
      "label": "semantic",
      "query": "Find A PERSON near the LEFT BLEACHERS",
      "sql_rows_count": 1,
      "hybrid_rows_count": 26,
      "sql_error": null,
      "hybrid_error": null
    },
    "expected": "non-empty routing_metrics",
    "severity": "soft"
  },
  {
    "name": "search_config_present",
    "passed": true,
    "actual": {
      "candidate_limit": 80,
      "top_k_per_event": 20,
      "rerank_top_k": 5,
      "distance_threshold": null,
      "hybrid_alpha": 0.7,
      "hybrid_fallback_alpha": 0.9,
      "hybrid_limit": 50,
      "sql_limit": 80
    },
    "expected": "non-empty search_config",
    "severity": "soft"
  },
  {
    "name": "no_tool_error",
    "passed": true,
    "actual": null,
    "expected": null,
    "severity": "soft"
  },
  {
    "name": "min_results",
    "passed": true,
    "actual": 27,
    "expected": 1,
    "severity": "hard"
  },
  {
    "name": "semantic_backend_effective",
    "passed": true,
    "actual": {
      "hybrid_rows_count": 26,
      "hybrid_error": null,
      "degraded": false
    },
    "expected": "hybrid rows > 0 or explicit degradation/error",
    "severity": "hard"
  },
  {
    "name": "hybrid_health_consistency",
    "passed": true,
    "actual": {
      "hybrid_summary": "Hybrid direct retrieval complete",
      "hybrid_error": null,
      "degraded": false
    },
    "expected": "hybrid failure should be reflected by degraded flag or hybrid_error",
    "severity": "hard"
  }
]
```
- Last Iteration:
```json
{
  "elapsed_ms": 8463.01,
  "route_mode": "hybrid_search",
  "label": "semantic",
  "llm_final_output": "A dark-clothed person is seen standing near the left bleachers with little motion from 0.00s to 30.84s in *basketball_2.mp4*. Another person remains mostly still near the left baseline/bench area from 0.0s to 61.2s in *basketball_1.mp4*. Additional similar sightings occur on the left side of the court in both videos.\nSources: [hybrid] basketball_2.mp4 | event_id=basketball_2.mp4_track_id_1 | 0.0-30.84; [hybrid] basketball_1.mp4 | event_id=basketball_1.mp4_track_1 | 0.0-61.208333333333336; [hybrid] basketball_2.mp4 | event_id=basketball_2.mp4_track_id_5 | 0.0-9.96",
  "raw_final_answer": "Retrieval complete. Most relevant results:\n[1] event_id=basketball_2.mp4_track_id_1 | video=basketball_2.mp4 | distance=0.23945021629333496 | summary=standing near left bleachers with little motion Located in left bleachers. From 0.00s to 30.84s, a dark-clothed person stands near the left bleachers with little motion.\n[2] event_id=basketball_1.mp4_track_1 | video=basketball_1.mp4 | distance=0.33325302600860596 | summary=Little motion; standing near the left baseline/bench area. Located in sidewalk. From 0.0s to 61.2s, a person with unknown color stays mostly still near the left baseline/bench area.\n[3] event_id=basketball_2.mp4_track_id_5 | video=basketball_2.mp4 | distance=0.35027164220809937 | summary=standing near left side with little motion Located in left side. From 0.00s to 9.96s, a dark-clothed person stands near the left side with little motion.\n[4] event_id=basketball_1.mp4_track_29 | video=basketball_1.mp4 | distance=0.3522948622703552 | summary=Little motion; standing near the left side of the court. Located in sidewalk. From 43.8s to 125.7s, a person with unknown color remains mostly still near the left side of the court.\n[5] event_id=basketball_1.mp4_track_30 | video=basketball_1.mp4 | distance=0.3453550934791565 | summary=Little motion; standing near the left-center court area. Located in sidewalk. From 47.8s to 48.8s, a person with unknown color remains mostly still near the left-center court area.",
  "rewritten_query": "Find A PERSON near the LEFT BLEACHERS",
  "original_user_query": "!!! Find A PERSON near the LEFT BLEACHERS ???",
  "self_query_result": {
    "rewritten_query": "Find A PERSON near the LEFT BLEACHERS",
    "user_need": "Retrieve basketball video results that satisfy: Find A PERSON near the LEFT BLEACHERS",
    "intent_label": "semantic",
    "retrieval_focus": "semantic",
    "key_constraints": [
      "find",
      "a",
      "person",
      "near",
      "the",
      "left"
    ],
    "ambiguities": [],
    "reasoning_summary": "Fast-path preprocessing kept the original meaning and only normalized surface noise.",
    "confidence": 0.8,
    "original_user_query": "!!! Find A PERSON near the LEFT BLEACHERS ???"
  },
  "summary_result": {
    "summary": "A dark-clothed person is seen standing near the left bleachers with little motion from 0.00s to 30.84s in *basketball_2.mp4*. Another person remains mostly still near the left baseline/bench area from 0.0s to 61.2s in *basketball_1.mp4*. Additional similar sightings occur on the left side of the court in both videos.",
    "style": "llm_summary",
    "confidence": 0.8,
    "citations": [
      {
        "source_type": "hybrid",
        "video_id": "basketball_2.mp4",
        "event_id": "basketball_2.mp4_track_id_1",
        "start_time": 0.0,
        "end_time": 30.84
      },
      {
        "source_type": "hybrid",
        "video_id": "basketball_1.mp4",
        "event_id": "basketball_1.mp4_track_1",
        "start_time": 0.0,
        "end_time": 61.208333333333336
      },
      {
        "source_type": "hybrid",
        "video_id": "basketball_2.mp4",
        "event_id": "basketball_2.mp4_track_id_5",
        "start_time": 0.0,
        "end_time": 9.96
      }
    ]
  },
  "routing_metrics": {
    "execution_mode": "parallel_fusion",
    "label": "semantic",
    "query": "Find A PERSON near the LEFT BLEACHERS",
    "sql_rows_count": 1,
    "hybrid_rows_count": 26,
    "sql_error": null,
    "hybrid_error": null
  },
  "search_config": {
    "candidate_limit": 80,
    "top_k_per_event": 20,
    "rerank_top_k": 5,
    "distance_threshold": null,
    "hybrid_alpha": 0.7,
    "hybrid_fallback_alpha": 0.9,
    "hybrid_limit": 50,
    "sql_limit": 80
  },
  "sql_plan": {
    "table": "episodic_events",
    "fields": [
      "event_id",
      "video_id",
      "track_id",
      "start_time",
      "end_time",
      "object_type",
      "object_color_en",
      "scene_zone_en",
      "appearance_notes_en",
      "event_summary_en"
    ],
    "where": [
      {
        "field": "object_type",
        "op": "=",
        "value": "person"
      },
      {
        "field": "scene_zone_en",
        "op": "contains",
        "value": "left bleachers"
      }
    ],
    "order_by": "start_time ASC",
    "limit": 80
  },
  "node_trace": [
    "self_query_node",
    "query_classification_node",
    "parallel_retrieval_fusion_node",
    "final_answer_node",
    "summary_node"
  ],
  "final_answer": "A dark-clothed person is seen standing near the left bleachers with little motion from 0.00s to 30.84s in *basketball_2.mp4*. Another person remains mostly still near the left baseline/bench area from 0.0s to 61.2s in *basketball_1.mp4*. Additional similar sightings occur on the left side of the court in both videos.\nSources: [hybrid] basketball_2.mp4 | event_id=basketball_2.mp4_track_id_1 | 0.0-30.84; [hybrid] basketball_1.mp4 | event_id=basketball_1.mp4_track_1 | 0.0-61.208333333333336; [hybrid] basketball_2.mp4 | event_id=basketball_2.mp4_track_id_5 | 0.0-9.96",
  "tool_error": null,
  "error": null,
  "current_node": "summary_node",
  "top5": [
    {
      "event_id": "basketball_2.mp4_track_id_1",
      "video_id": "basketball_2.mp4",
      "event_text": "standing near left bleachers with little motion Located in left bleachers. From 0.00s to 30.84s, a dark-clothed person stands near the left bleachers with little motion.",
      "distance": 0.23945021629333496
    },
    {
      "event_id": "basketball_1.mp4_track_1",
      "video_id": "basketball_1.mp4",
      "event_text": "Little motion; standing near the left baseline/bench area. Located in sidewalk. From 0.0s to 61.2s, a person with unknown color stays mostly still near the left baseline/bench area.",
      "distance": 0.33325302600860596
    },
    {
      "event_id": "basketball_2.mp4_track_id_5",
      "video_id": "basketball_2.mp4",
      "event_text": "standing near left side with little motion Located in left side. From 0.00s to 9.96s, a dark-clothed person stands near the left side with little motion.",
      "distance": 0.35027164220809937
    },
    {
      "event_id": "basketball_1.mp4_track_29",
      "video_id": "basketball_1.mp4",
      "event_text": "Little motion; standing near the left side of the court. Located in sidewalk. From 43.8s to 125.7s, a person with unknown color remains mostly still near the left side of the court.",
      "distance": 0.3522948622703552
    },
    {
      "event_id": "basketball_1.mp4_track_30",
      "video_id": "basketball_1.mp4",
      "event_text": "Little motion; standing near the left-center court area. Located in sidewalk. From 47.8s to 48.8s, a person with unknown color remains mostly still near the left-center court area.",
      "distance": 0.3453550934791565
    }
  ],
  "merged_count": 27,
  "sql_rows_count": 1,
  "hybrid_rows_count": 26,
  "degraded": false,
  "hybrid_summary": "Hybrid direct retrieval complete",
  "sql_summary": "SQL direct retrieval rows=1",
  "hybrid_error": null,
  "sql_error": null,
  "sql_debug": {
    "duration": 2.8325650000006135,
    "sql_summary": "SQL direct retrieval rows=1",
    "hybrid_summary": "Hybrid direct retrieval complete",
    "sql_error": null,
    "hybrid_error": null,
    "fusion_meta": {
      "label": "semantic",
      "weights": {
        "sql": 0.2,
        "hybrid": 0.8
      },
      "rrf_k": 60.0,
      "sql_count": 1,
      "hybrid_count": 26,
      "fused_count": 27,
      "method": "weighted_rrf",
      "degraded": false
    }
  }
}
```

## FNC_SQL_003
- Suite: `filter_regression`
- Priority: `P1`
- Dimensions: `functional, filtering`
- Description: Parking-area query should surface parking-related evidence in top results.
- Query: `Show me a person in the parking area.`
- Status: `PASS`
- Avg Latency: `5651.2 ms`
- P95 Latency: `5651.2 ms`
- Node Trace:
```json
[
  "self_query_node",
  "query_classification_node",
  "parallel_retrieval_fusion_node",
  "final_answer_node",
  "summary_node"
]
```
- Routing Metrics:
```json
{
  "execution_mode": "parallel_fusion",
  "label": "structured",
  "query": "Show me a person in the parking area",
  "sql_rows_count": 2,
  "hybrid_rows_count": 26,
  "sql_error": null,
  "hybrid_error": null
}
```
- Search Config:
```json
{
  "candidate_limit": 80,
  "top_k_per_event": 20,
  "rerank_top_k": 5,
  "distance_threshold": null,
  "hybrid_alpha": 0.7,
  "hybrid_fallback_alpha": 0.9,
  "hybrid_limit": 50,
  "sql_limit": 80
}
```
- SQL Plan:
```json
{
  "table": "episodic_events",
  "fields": [
    "event_id",
    "video_id",
    "track_id",
    "start_time",
    "end_time",
    "object_type",
    "object_color_en",
    "scene_zone_en",
    "appearance_notes_en",
    "event_summary_en"
  ],
  "where": [
    {
      "field": "object_type",
      "op": "=",
      "value": "person"
    },
    {
      "field": "scene_zone_en",
      "op": "contains",
      "value": "parking"
    }
  ],
  "order_by": "start_time ASC",
  "limit": 80
}
```
- Self Query Result:
```json
{
  "rewritten_query": "Show me a person in the parking area",
  "user_need": "Retrieve basketball video results that satisfy: Show me a person in the parking area",
  "intent_label": "structured",
  "retrieval_focus": "structured",
  "key_constraints": [
    "show",
    "me",
    "a",
    "person",
    "in",
    "the"
  ],
  "ambiguities": [],
  "reasoning_summary": "Fast-path preprocessing kept the original meaning and only normalized surface noise.",
  "confidence": 0.8,
  "original_user_query": "Show me a person in the parking area."
}
```
- Raw Final Answer:
```json
{
  "raw_final_answer": "Retrieval complete. Most relevant results:\n[1] event_id=4 | video=basketball_1.mp4 | distance=0.0 | summary=From 0.0s to 143.1s, a person with unknown color stays mostly still near the lower-left court/bench area.\n[2] event_id=8 | video=basketball_1.mp4 | distance=0.0 | summary=From 0.0s to 270.3s, a person with unknown color stays mostly still near the center-left baseline area.\n[3] event_id=basketball_1.mp4_track_4 | video=basketball_1.mp4 | distance=0.2897026538848877 | summary=Little motion; standing near the lower-left court/bench area. Located in parking. From 0.0s to 143.1s, a person with unknown color stays mostly still near the lower-left court/bench area.\n[4] event_id=basketball_1.mp4_track_9 | video=basketball_1.mp4 | distance=0.30628281831741333 | summary=Little motion; standing near the center-left baseline area. Located in parking. From 0.0s to 270.3s, a person with unknown color stays mostly still near the center-left baseline area.\n[5] event_id=basketball_1.mp4_track_30 | video=basketball_1.mp4 | distance=0.36482810974121094 | summary=Little motion; standing near the left-center court area. Located in sidewalk. From 47.8s to 48.8s, a person with unknown color remains mostly still near the left-center court area."
}
```
- LLM Final Output:
```json
{
  "llm_final_output": "A person is visible in the parking area near the lower-left court/bench and center-left baseline regions of the basketball court. They remain mostly still during the clips, with appearances from 0.0s to 143.1s and 0.0s to 270.3s in video *basketball_1.mp4*.\nSources: [sql] basketball_1.mp4 | event_id=4 | 0.0-143.125; [sql] basketball_1.mp4 | event_id=8 | 0.0-270.2916666666667; [hybrid] basketball_1.mp4 | event_id=basketball_1.mp4_track_4 | 0.0-143.125"
}
```
- Assertions:
```json
[
  {
    "name": "no_runtime_exception",
    "passed": true,
    "actual": [],
    "expected": null,
    "severity": "hard"
  },
  {
    "name": "label_matches",
    "passed": true,
    "actual": "structured",
    "expected": "structured",
    "severity": "hard"
  },
  {
    "name": "route_in_expected",
    "passed": true,
    "actual": "pure_sql",
    "expected": [
      "pure_sql"
    ],
    "severity": "hard"
  },
  {
    "name": "final_answer_present",
    "passed": true,
    "actual": "A person is visible in the parking area near the lower-left court/bench and center-left baseline regions of the basketball court. They remain mostly still during the clips, with appearances from 0.0s to 143.1s and 0.0s to 270.3s in video *basketball_1.mp4*.\nSources: [sql] basketball_1.mp4 | event_id=4 | 0.0-143.125; [sql] basketball_1.mp4 | event_id=8 | 0.0-270.2916666666667; [hybrid] basketball_1.mp4 | event_id=basketball_1.mp4_track_4 | 0.0-143.125",
    "expected": "non-empty string",
    "severity": "hard"
  },
  {
    "name": "citation_present",
    "passed": true,
    "actual": "A person is visible in the parking area near the lower-left court/bench and center-left baseline regions of the basketball court. They remain mostly still during the clips, with appearances from 0.0s to 143.1s and 0.0s to 270.3s in video *basketball_1.mp4*.\nSources: [sql] basketball_1.mp4 | event_id=4 | 0.0-143.125; [sql] basketball_1.mp4 | event_id=8 | 0.0-270.2916666666667; [hybrid] basketball_1.mp4 | event_id=basketball_1.mp4_track_4 | 0.0-143.125",
    "expected": "final answer contains Sources:",
    "severity": "soft"
  },
  {
    "name": "grounding_coverage",
    "passed": true,
    "actual": {
      "summary": "A person is visible in the parking area near the lower-left court/bench and center-left baseline regions of the basketball court. They remain mostly still during the clips, with appearances from 0.0s to 143.1s and 0.0s to 270.3s in video *basketball_1.mp4*.",
      "style": "llm_summary",
      "confidence": 0.8,
      "citations": [
        {
          "source_type": "sql",
          "video_id": "basketball_1.mp4",
          "event_id": 4,
          "start_time": 0.0,
          "end_time": 143.125
        },
        {
          "source_type": "sql",
          "video_id": "basketball_1.mp4",
          "event_id": 8,
          "start_time": 0.0,
          "end_time": 270.2916666666667
        },
        {
          "source_type": "hybrid",
          "video_id": "basketball_1.mp4",
          "event_id": "basketball_1.mp4_track_4",
          "start_time": 0.0,
          "end_time": 143.125
        }
      ]
    },
    "expected": "summary_result.citations is non-empty",
    "severity": "soft"
  },
  {
    "name": "rewritten_query_present",
    "passed": true,
    "actual": "Show me a person in the parking area",
    "expected": "non-empty rewritten query",
    "severity": "soft"
  },
  {
    "name": "user_need_identified",
    "passed": true,
    "actual": {
      "rewritten_query": "Show me a person in the parking area",
      "user_need": "Retrieve basketball video results that satisfy: Show me a person in the parking area",
      "intent_label": "structured",
      "retrieval_focus": "structured",
      "key_constraints": [
        "show",
        "me",
        "a",
        "person",
        "in",
        "the"
      ],
      "ambiguities": [],
      "reasoning_summary": "Fast-path preprocessing kept the original meaning and only normalized surface noise.",
      "confidence": 0.8,
      "original_user_query": "Show me a person in the parking area."
    },
    "expected": "structured self-query result with user_need",
    "severity": "soft"
  },
  {
    "name": "trace_has_required_nodes",
    "passed": true,
    "actual": [
      "self_query_node",
      "query_classification_node",
      "parallel_retrieval_fusion_node",
      "final_answer_node",
      "summary_node"
    ],
    "expected": [
      "self_query_node",
      "final_answer_node",
      "summary_node"
    ],
    "severity": "soft"
  },
  {
    "name": "routing_metrics_present",
    "passed": true,
    "actual": {
      "execution_mode": "parallel_fusion",
      "label": "structured",
      "query": "Show me a person in the parking area",
      "sql_rows_count": 2,
      "hybrid_rows_count": 26,
      "sql_error": null,
      "hybrid_error": null
    },
    "expected": "non-empty routing_metrics",
    "severity": "soft"
  },
  {
    "name": "search_config_present",
    "passed": true,
    "actual": {
      "candidate_limit": 80,
      "top_k_per_event": 20,
      "rerank_top_k": 5,
      "distance_threshold": null,
      "hybrid_alpha": 0.7,
      "hybrid_fallback_alpha": 0.9,
      "hybrid_limit": 50,
      "sql_limit": 80
    },
    "expected": "non-empty search_config",
    "severity": "soft"
  },
  {
    "name": "sql_plan_present",
    "passed": true,
    "actual": {
      "table": "episodic_events",
      "fields": [
        "event_id",
        "video_id",
        "track_id",
        "start_time",
        "end_time",
        "object_type",
        "object_color_en",
        "scene_zone_en",
        "appearance_notes_en",
        "event_summary_en"
      ],
      "where": [
        {
          "field": "object_type",
          "op": "=",
          "value": "person"
        },
        {
          "field": "scene_zone_en",
          "op": "contains",
          "value": "parking"
        }
      ],
      "order_by": "start_time ASC",
      "limit": 80
    },
    "expected": "non-empty sql_plan",
    "severity": "soft"
  },
  {
    "name": "no_tool_error",
    "passed": true,
    "actual": null,
    "expected": null,
    "severity": "soft"
  },
  {
    "name": "min_results",
    "passed": true,
    "actual": 28,
    "expected": 1,
    "severity": "hard"
  },
  {
    "name": "expected_keywords_any",
    "passed": true,
    "actual": "from 0.0s to 143.1s, a person with unknown color stays mostly still near the lower-left court/bench area. from 0.0s to 270.3s, a person with unknown color stays mostly still near the center-left baseline area. little motion; standing near the lower-left court/bench area. located in parking. from 0.0s to 143.1s, a person with unknown color stays mostly still near the lower-left court/bench area. little motion; standing near the center-left baseline area. located in parking. from 0.0s to 270.3s, a person with unknown color stays mostly still near the center-left baseline area. little motion; standing near the left-center court area. located in sidewalk. from 47.8s to 48.8s, a person with unknown color remains mostly still near the left-center court area.",
    "expected": [
      "parking"
    ],
    "severity": "hard"
  }
]
```
- Last Iteration:
```json
{
  "elapsed_ms": 5651.2,
  "route_mode": "pure_sql",
  "label": "structured",
  "llm_final_output": "A person is visible in the parking area near the lower-left court/bench and center-left baseline regions of the basketball court. They remain mostly still during the clips, with appearances from 0.0s to 143.1s and 0.0s to 270.3s in video *basketball_1.mp4*.\nSources: [sql] basketball_1.mp4 | event_id=4 | 0.0-143.125; [sql] basketball_1.mp4 | event_id=8 | 0.0-270.2916666666667; [hybrid] basketball_1.mp4 | event_id=basketball_1.mp4_track_4 | 0.0-143.125",
  "raw_final_answer": "Retrieval complete. Most relevant results:\n[1] event_id=4 | video=basketball_1.mp4 | distance=0.0 | summary=From 0.0s to 143.1s, a person with unknown color stays mostly still near the lower-left court/bench area.\n[2] event_id=8 | video=basketball_1.mp4 | distance=0.0 | summary=From 0.0s to 270.3s, a person with unknown color stays mostly still near the center-left baseline area.\n[3] event_id=basketball_1.mp4_track_4 | video=basketball_1.mp4 | distance=0.2897026538848877 | summary=Little motion; standing near the lower-left court/bench area. Located in parking. From 0.0s to 143.1s, a person with unknown color stays mostly still near the lower-left court/bench area.\n[4] event_id=basketball_1.mp4_track_9 | video=basketball_1.mp4 | distance=0.30628281831741333 | summary=Little motion; standing near the center-left baseline area. Located in parking. From 0.0s to 270.3s, a person with unknown color stays mostly still near the center-left baseline area.\n[5] event_id=basketball_1.mp4_track_30 | video=basketball_1.mp4 | distance=0.36482810974121094 | summary=Little motion; standing near the left-center court area. Located in sidewalk. From 47.8s to 48.8s, a person with unknown color remains mostly still near the left-center court area.",
  "rewritten_query": "Show me a person in the parking area",
  "original_user_query": "Show me a person in the parking area.",
  "self_query_result": {
    "rewritten_query": "Show me a person in the parking area",
    "user_need": "Retrieve basketball video results that satisfy: Show me a person in the parking area",
    "intent_label": "structured",
    "retrieval_focus": "structured",
    "key_constraints": [
      "show",
      "me",
      "a",
      "person",
      "in",
      "the"
    ],
    "ambiguities": [],
    "reasoning_summary": "Fast-path preprocessing kept the original meaning and only normalized surface noise.",
    "confidence": 0.8,
    "original_user_query": "Show me a person in the parking area."
  },
  "summary_result": {
    "summary": "A person is visible in the parking area near the lower-left court/bench and center-left baseline regions of the basketball court. They remain mostly still during the clips, with appearances from 0.0s to 143.1s and 0.0s to 270.3s in video *basketball_1.mp4*.",
    "style": "llm_summary",
    "confidence": 0.8,
    "citations": [
      {
        "source_type": "sql",
        "video_id": "basketball_1.mp4",
        "event_id": 4,
        "start_time": 0.0,
        "end_time": 143.125
      },
      {
        "source_type": "sql",
        "video_id": "basketball_1.mp4",
        "event_id": 8,
        "start_time": 0.0,
        "end_time": 270.2916666666667
      },
      {
        "source_type": "hybrid",
        "video_id": "basketball_1.mp4",
        "event_id": "basketball_1.mp4_track_4",
        "start_time": 0.0,
        "end_time": 143.125
      }
    ]
  },
  "routing_metrics": {
    "execution_mode": "parallel_fusion",
    "label": "structured",
    "query": "Show me a person in the parking area",
    "sql_rows_count": 2,
    "hybrid_rows_count": 26,
    "sql_error": null,
    "hybrid_error": null
  },
  "search_config": {
    "candidate_limit": 80,
    "top_k_per_event": 20,
    "rerank_top_k": 5,
    "distance_threshold": null,
    "hybrid_alpha": 0.7,
    "hybrid_fallback_alpha": 0.9,
    "hybrid_limit": 50,
    "sql_limit": 80
  },
  "sql_plan": {
    "table": "episodic_events",
    "fields": [
      "event_id",
      "video_id",
      "track_id",
      "start_time",
      "end_time",
      "object_type",
      "object_color_en",
      "scene_zone_en",
      "appearance_notes_en",
      "event_summary_en"
    ],
    "where": [
      {
        "field": "object_type",
        "op": "=",
        "value": "person"
      },
      {
        "field": "scene_zone_en",
        "op": "contains",
        "value": "parking"
      }
    ],
    "order_by": "start_time ASC",
    "limit": 80
  },
  "node_trace": [
    "self_query_node",
    "query_classification_node",
    "parallel_retrieval_fusion_node",
    "final_answer_node",
    "summary_node"
  ],
  "final_answer": "A person is visible in the parking area near the lower-left court/bench and center-left baseline regions of the basketball court. They remain mostly still during the clips, with appearances from 0.0s to 143.1s and 0.0s to 270.3s in video *basketball_1.mp4*.\nSources: [sql] basketball_1.mp4 | event_id=4 | 0.0-143.125; [sql] basketball_1.mp4 | event_id=8 | 0.0-270.2916666666667; [hybrid] basketball_1.mp4 | event_id=basketball_1.mp4_track_4 | 0.0-143.125",
  "tool_error": null,
  "error": null,
  "current_node": "summary_node",
  "top5": [
    {
      "event_id": 4,
      "video_id": "basketball_1.mp4",
      "event_text": "From 0.0s to 143.1s, a person with unknown color stays mostly still near the lower-left court/bench area.",
      "distance": 0.0
    },
    {
      "event_id": 8,
      "video_id": "basketball_1.mp4",
      "event_text": "From 0.0s to 270.3s, a person with unknown color stays mostly still near the center-left baseline area.",
      "distance": 0.0
    },
    {
      "event_id": "basketball_1.mp4_track_4",
      "video_id": "basketball_1.mp4",
      "event_text": "Little motion; standing near the lower-left court/bench area. Located in parking. From 0.0s to 143.1s, a person with unknown color stays mostly still near the lower-left court/bench area.",
      "distance": 0.2897026538848877
    },
    {
      "event_id": "basketball_1.mp4_track_9",
      "video_id": "basketball_1.mp4",
      "event_text": "Little motion; standing near the center-left baseline area. Located in parking. From 0.0s to 270.3s, a person with unknown color stays mostly still near the center-left baseline area.",
      "distance": 0.30628281831741333
    },
    {
      "event_id": "basketball_1.mp4_track_30",
      "video_id": "basketball_1.mp4",
      "event_text": "Little motion; standing near the left-center court area. Located in sidewalk. From 47.8s to 48.8s, a person with unknown color remains mostly still near the left-center court area.",
      "distance": 0.36482810974121094
    }
  ],
  "merged_count": 28,
  "sql_rows_count": 2,
  "hybrid_rows_count": 26,
  "degraded": false,
  "hybrid_summary": "Hybrid direct retrieval complete",
  "sql_summary": "SQL direct retrieval rows=2",
  "hybrid_error": null,
  "sql_error": null,
  "sql_debug": {
    "duration": 2.9153464779992646,
    "sql_summary": "SQL direct retrieval rows=2",
    "hybrid_summary": "Hybrid direct retrieval complete",
    "sql_error": null,
    "hybrid_error": null,
    "fusion_meta": {
      "label": "structured",
      "weights": {
        "sql": 0.8,
        "hybrid": 0.2
      },
      "rrf_k": 60.0,
      "sql_count": 2,
      "hybrid_count": 26,
      "fused_count": 28,
      "method": "weighted_rrf",
      "degraded": false
    }
  }
}
```

## PERF_SQL_001
- Suite: `performance_smoke`
- Priority: `P1`
- Dimensions: `performance, functional`
- Description: Structured path should stay within an acceptable average latency budget.
- Query: `Did you see any person in the database?`
- Status: `PASS`
- Avg Latency: `6404.6 ms`
- P95 Latency: `6597.96 ms`
- Node Trace:
```json
[
  "self_query_node",
  "query_classification_node",
  "parallel_retrieval_fusion_node",
  "final_answer_node",
  "summary_node"
]
```
- Routing Metrics:
```json
{
  "execution_mode": "parallel_fusion",
  "label": "structured",
  "query": "Did you see any person in the database",
  "sql_rows_count": 27,
  "hybrid_rows_count": 26,
  "sql_error": null,
  "hybrid_error": null
}
```
- Search Config:
```json
{
  "candidate_limit": 80,
  "top_k_per_event": 20,
  "rerank_top_k": 5,
  "distance_threshold": null,
  "hybrid_alpha": 0.7,
  "hybrid_fallback_alpha": 0.9,
  "hybrid_limit": 50,
  "sql_limit": 80
}
```
- SQL Plan:
```json
{
  "table": "episodic_events",
  "fields": [
    "event_id",
    "video_id",
    "track_id",
    "start_time",
    "end_time",
    "object_type",
    "object_color_en",
    "scene_zone_en",
    "appearance_notes_en",
    "event_summary_en"
  ],
  "where": [
    {
      "field": "object_type",
      "op": "=",
      "value": "person"
    }
  ],
  "order_by": "start_time ASC",
  "limit": 80
}
```
- Self Query Result:
```json
{
  "rewritten_query": "Did you see any person in the database",
  "user_need": "Retrieve basketball video results that satisfy: Did you see any person in the database",
  "intent_label": "structured",
  "retrieval_focus": "structured",
  "key_constraints": [
    "did",
    "you",
    "see",
    "any",
    "person",
    "in"
  ],
  "ambiguities": [],
  "reasoning_summary": "Fast-path preprocessing kept the original meaning and only normalized surface noise.",
  "confidence": 0.8,
  "original_user_query": "Did you see any person in the database?"
}
```
- Raw Final Answer:
```json
{
  "raw_final_answer": "Retrieval complete. Most relevant results:\n[1] event_id=1 | video=basketball_1.mp4 | distance=0.0 | summary=From 0.0s to 61.2s, a person with unknown color stays mostly still near the left baseline/bench area.\n[2] event_id=2 | video=basketball_1.mp4 | distance=0.0 | summary=From 0.0s to 16.1s, a person with unknown color remains mostly still near the left-center baseline area.\n[3] event_id=3 | video=basketball_1.mp4 | distance=0.0 | summary=From 0.0s to 12.0s, a person with unknown color remains mostly still near the left-center baseline area.\n[4] event_id=4 | video=basketball_1.mp4 | distance=0.0 | summary=From 0.0s to 143.1s, a person with unknown color stays mostly still near the lower-left court/bench area.\n[5] event_id=5 | video=basketball_1.mp4 | distance=0.0 | summary=From 0.0s to 17.5s, a person with unknown color remains mostly still near the left-center baseline area."
}
```
- LLM Final Output:
```json
{
  "llm_final_output": "Yes, multiple people were detected in the video. In \"basketball_1.mp4,\" individuals (with unknown clothing colors) were seen staying mostly still near the left baseline, left-center baseline, and lower-left court or bench areas, with appearances ranging from 12 to over 140 seconds.\nSources: [sql] basketball_1.mp4 | event_id=1 | 0.0-61.208333333333336; [sql] basketball_1.mp4 | event_id=2 | 0.0-16.083333333333332; [sql] basketball_1.mp4 | event_id=3 | 0.0-12.041666666666666"
}
```
- Assertions:
```json
[
  {
    "name": "no_runtime_exception",
    "passed": true,
    "actual": [],
    "expected": null,
    "severity": "hard"
  },
  {
    "name": "route_in_expected",
    "passed": true,
    "actual": "pure_sql",
    "expected": [
      "pure_sql"
    ],
    "severity": "hard"
  },
  {
    "name": "final_answer_present",
    "passed": true,
    "actual": "Yes, multiple people were detected in the video. In \"basketball_1.mp4,\" individuals (with unknown clothing colors) were seen staying mostly still near the left baseline, left-center baseline, and lower-left court or bench areas, with appearances ranging from 12 to over 140 seconds.\nSources: [sql] basketball_1.mp4 | event_id=1 | 0.0-61.208333333333336; [sql] basketball_1.mp4 | event_id=2 | 0.0-16.083333333333332; [sql] basketball_1.mp4 | event_id=3 | 0.0-12.041666666666666",
    "expected": "non-empty string",
    "severity": "hard"
  },
  {
    "name": "citation_present",
    "passed": true,
    "actual": "Yes, multiple people were detected in the video. In \"basketball_1.mp4,\" individuals (with unknown clothing colors) were seen staying mostly still near the left baseline, left-center baseline, and lower-left court or bench areas, with appearances ranging from 12 to over 140 seconds.\nSources: [sql] basketball_1.mp4 | event_id=1 | 0.0-61.208333333333336; [sql] basketball_1.mp4 | event_id=2 | 0.0-16.083333333333332; [sql] basketball_1.mp4 | event_id=3 | 0.0-12.041666666666666",
    "expected": "final answer contains Sources:",
    "severity": "soft"
  },
  {
    "name": "grounding_coverage",
    "passed": true,
    "actual": {
      "summary": "Yes, multiple people were detected in the video. In \"basketball_1.mp4,\" individuals (with unknown clothing colors) were seen staying mostly still near the left baseline, left-center baseline, and lower-left court or bench areas, with appearances ranging from 12 to over 140 seconds.",
      "style": "llm_summary",
      "confidence": 0.8,
      "citations": [
        {
          "source_type": "sql",
          "video_id": "basketball_1.mp4",
          "event_id": 1,
          "start_time": 0.0,
          "end_time": 61.208333333333336
        },
        {
          "source_type": "sql",
          "video_id": "basketball_1.mp4",
          "event_id": 2,
          "start_time": 0.0,
          "end_time": 16.083333333333332
        },
        {
          "source_type": "sql",
          "video_id": "basketball_1.mp4",
          "event_id": 3,
          "start_time": 0.0,
          "end_time": 12.041666666666666
        }
      ]
    },
    "expected": "summary_result.citations is non-empty",
    "severity": "soft"
  },
  {
    "name": "rewritten_query_present",
    "passed": true,
    "actual": "Did you see any person in the database",
    "expected": "non-empty rewritten query",
    "severity": "soft"
  },
  {
    "name": "user_need_identified",
    "passed": true,
    "actual": {
      "rewritten_query": "Did you see any person in the database",
      "user_need": "Retrieve basketball video results that satisfy: Did you see any person in the database",
      "intent_label": "structured",
      "retrieval_focus": "structured",
      "key_constraints": [
        "did",
        "you",
        "see",
        "any",
        "person",
        "in"
      ],
      "ambiguities": [],
      "reasoning_summary": "Fast-path preprocessing kept the original meaning and only normalized surface noise.",
      "confidence": 0.8,
      "original_user_query": "Did you see any person in the database?"
    },
    "expected": "structured self-query result with user_need",
    "severity": "soft"
  },
  {
    "name": "trace_has_required_nodes",
    "passed": true,
    "actual": [
      "self_query_node",
      "query_classification_node",
      "parallel_retrieval_fusion_node",
      "final_answer_node",
      "summary_node"
    ],
    "expected": [
      "self_query_node",
      "final_answer_node",
      "summary_node"
    ],
    "severity": "soft"
  },
  {
    "name": "routing_metrics_present",
    "passed": true,
    "actual": {
      "execution_mode": "parallel_fusion",
      "label": "structured",
      "query": "Did you see any person in the database",
      "sql_rows_count": 27,
      "hybrid_rows_count": 26,
      "sql_error": null,
      "hybrid_error": null
    },
    "expected": "non-empty routing_metrics",
    "severity": "soft"
  },
  {
    "name": "search_config_present",
    "passed": true,
    "actual": {
      "candidate_limit": 80,
      "top_k_per_event": 20,
      "rerank_top_k": 5,
      "distance_threshold": null,
      "hybrid_alpha": 0.7,
      "hybrid_fallback_alpha": 0.9,
      "hybrid_limit": 50,
      "sql_limit": 80
    },
    "expected": "non-empty search_config",
    "severity": "soft"
  },
  {
    "name": "sql_plan_present",
    "passed": true,
    "actual": {
      "table": "episodic_events",
      "fields": [
        "event_id",
        "video_id",
        "track_id",
        "start_time",
        "end_time",
        "object_type",
        "object_color_en",
        "scene_zone_en",
        "appearance_notes_en",
        "event_summary_en"
      ],
      "where": [
        {
          "field": "object_type",
          "op": "=",
          "value": "person"
        }
      ],
      "order_by": "start_time ASC",
      "limit": 80
    },
    "expected": "non-empty sql_plan",
    "severity": "soft"
  },
  {
    "name": "no_tool_error",
    "passed": true,
    "actual": null,
    "expected": null,
    "severity": "soft"
  },
  {
    "name": "min_results",
    "passed": true,
    "actual": 50,
    "expected": 1,
    "severity": "hard"
  },
  {
    "name": "min_sql_rows",
    "passed": true,
    "actual": 27,
    "expected": 1,
    "severity": "hard"
  },
  {
    "name": "avg_latency_budget",
    "passed": true,
    "actual": 6404.6,
    "expected": 9000,
    "severity": "soft"
  }
]
```
- Last Iteration:
```json
{
  "elapsed_ms": 6628.81,
  "route_mode": "pure_sql",
  "label": "structured",
  "llm_final_output": "Yes, multiple people were detected in the video. In \"basketball_1.mp4,\" individuals (with unknown clothing colors) were seen staying mostly still near the left baseline, left-center baseline, and lower-left court or bench areas, with appearances ranging from 12 to over 140 seconds.\nSources: [sql] basketball_1.mp4 | event_id=1 | 0.0-61.208333333333336; [sql] basketball_1.mp4 | event_id=2 | 0.0-16.083333333333332; [sql] basketball_1.mp4 | event_id=3 | 0.0-12.041666666666666",
  "raw_final_answer": "Retrieval complete. Most relevant results:\n[1] event_id=1 | video=basketball_1.mp4 | distance=0.0 | summary=From 0.0s to 61.2s, a person with unknown color stays mostly still near the left baseline/bench area.\n[2] event_id=2 | video=basketball_1.mp4 | distance=0.0 | summary=From 0.0s to 16.1s, a person with unknown color remains mostly still near the left-center baseline area.\n[3] event_id=3 | video=basketball_1.mp4 | distance=0.0 | summary=From 0.0s to 12.0s, a person with unknown color remains mostly still near the left-center baseline area.\n[4] event_id=4 | video=basketball_1.mp4 | distance=0.0 | summary=From 0.0s to 143.1s, a person with unknown color stays mostly still near the lower-left court/bench area.\n[5] event_id=5 | video=basketball_1.mp4 | distance=0.0 | summary=From 0.0s to 17.5s, a person with unknown color remains mostly still near the left-center baseline area.",
  "rewritten_query": "Did you see any person in the database",
  "original_user_query": "Did you see any person in the database?",
  "self_query_result": {
    "rewritten_query": "Did you see any person in the database",
    "user_need": "Retrieve basketball video results that satisfy: Did you see any person in the database",
    "intent_label": "structured",
    "retrieval_focus": "structured",
    "key_constraints": [
      "did",
      "you",
      "see",
      "any",
      "person",
      "in"
    ],
    "ambiguities": [],
    "reasoning_summary": "Fast-path preprocessing kept the original meaning and only normalized surface noise.",
    "confidence": 0.8,
    "original_user_query": "Did you see any person in the database?"
  },
  "summary_result": {
    "summary": "Yes, multiple people were detected in the video. In \"basketball_1.mp4,\" individuals (with unknown clothing colors) were seen staying mostly still near the left baseline, left-center baseline, and lower-left court or bench areas, with appearances ranging from 12 to over 140 seconds.",
    "style": "llm_summary",
    "confidence": 0.8,
    "citations": [
      {
        "source_type": "sql",
        "video_id": "basketball_1.mp4",
        "event_id": 1,
        "start_time": 0.0,
        "end_time": 61.208333333333336
      },
      {
        "source_type": "sql",
        "video_id": "basketball_1.mp4",
        "event_id": 2,
        "start_time": 0.0,
        "end_time": 16.083333333333332
      },
      {
        "source_type": "sql",
        "video_id": "basketball_1.mp4",
        "event_id": 3,
        "start_time": 0.0,
        "end_time": 12.041666666666666
      }
    ]
  },
  "routing_metrics": {
    "execution_mode": "parallel_fusion",
    "label": "structured",
    "query": "Did you see any person in the database",
    "sql_rows_count": 27,
    "hybrid_rows_count": 26,
    "sql_error": null,
    "hybrid_error": null
  },
  "search_config": {
    "candidate_limit": 80,
    "top_k_per_event": 20,
    "rerank_top_k": 5,
    "distance_threshold": null,
    "hybrid_alpha": 0.7,
    "hybrid_fallback_alpha": 0.9,
    "hybrid_limit": 50,
    "sql_limit": 80
  },
  "sql_plan": {
    "table": "episodic_events",
    "fields": [
      "event_id",
      "video_id",
      "track_id",
      "start_time",
      "end_time",
      "object_type",
      "object_color_en",
      "scene_zone_en",
      "appearance_notes_en",
      "event_summary_en"
    ],
    "where": [
      {
        "field": "object_type",
        "op": "=",
        "value": "person"
      }
    ],
    "order_by": "start_time ASC",
    "limit": 80
  },
  "node_trace": [
    "self_query_node",
    "query_classification_node",
    "parallel_retrieval_fusion_node",
    "final_answer_node",
    "summary_node"
  ],
  "final_answer": "Yes, multiple people were detected in the video. In \"basketball_1.mp4,\" individuals (with unknown clothing colors) were seen staying mostly still near the left baseline, left-center baseline, and lower-left court or bench areas, with appearances ranging from 12 to over 140 seconds.\nSources: [sql] basketball_1.mp4 | event_id=1 | 0.0-61.208333333333336; [sql] basketball_1.mp4 | event_id=2 | 0.0-16.083333333333332; [sql] basketball_1.mp4 | event_id=3 | 0.0-12.041666666666666",
  "tool_error": null,
  "error": null,
  "current_node": "summary_node",
  "top5": [
    {
      "event_id": 1,
      "video_id": "basketball_1.mp4",
      "event_text": "From 0.0s to 61.2s, a person with unknown color stays mostly still near the left baseline/bench area.",
      "distance": 0.0
    },
    {
      "event_id": 2,
      "video_id": "basketball_1.mp4",
      "event_text": "From 0.0s to 16.1s, a person with unknown color remains mostly still near the left-center baseline area.",
      "distance": 0.0
    },
    {
      "event_id": 3,
      "video_id": "basketball_1.mp4",
      "event_text": "From 0.0s to 12.0s, a person with unknown color remains mostly still near the left-center baseline area.",
      "distance": 0.0
    },
    {
      "event_id": 4,
      "video_id": "basketball_1.mp4",
      "event_text": "From 0.0s to 143.1s, a person with unknown color stays mostly still near the lower-left court/bench area.",
      "distance": 0.0
    },
    {
      "event_id": 5,
      "video_id": "basketball_1.mp4",
      "event_text": "From 0.0s to 17.5s, a person with unknown color remains mostly still near the left-center baseline area.",
      "distance": 0.0
    }
  ],
  "merged_count": 50,
  "sql_rows_count": 27,
  "hybrid_rows_count": 26,
  "degraded": false,
  "hybrid_summary": "Hybrid direct retrieval complete",
  "sql_summary": "SQL direct retrieval rows=27",
  "hybrid_error": null,
  "sql_error": null,
  "sql_debug": {
    "duration": 1.5071352400009346,
    "sql_summary": "SQL direct retrieval rows=27",
    "hybrid_summary": "Hybrid direct retrieval complete",
    "sql_error": null,
    "hybrid_error": null,
    "fusion_meta": {
      "label": "structured",
      "weights": {
        "sql": 0.8,
        "hybrid": 0.2
      },
      "rrf_k": 60.0,
      "sql_count": 27,
      "hybrid_count": 26,
      "fused_count": 50,
      "method": "weighted_rrf",
      "degraded": false
    }
  }
}
```

## PERF_HYB_001
- Suite: `performance_smoke`
- Priority: `P1`
- Dimensions: `performance, semantic`
- Description: Semantic path should stay within an acceptable average latency budget.
- Query: `Find a person near the left bleachers.`
- Status: `PASS`
- Avg Latency: `8638.14 ms`
- P95 Latency: `8471.5 ms`
- Node Trace:
```json
[
  "self_query_node",
  "query_classification_node",
  "parallel_retrieval_fusion_node",
  "final_answer_node",
  "summary_node"
]
```
- Routing Metrics:
```json
{
  "execution_mode": "parallel_fusion",
  "label": "semantic",
  "query": "Find a person near the left bleachers",
  "sql_rows_count": 1,
  "hybrid_rows_count": 26,
  "sql_error": null,
  "hybrid_error": null
}
```
- Search Config:
```json
{
  "candidate_limit": 80,
  "top_k_per_event": 20,
  "rerank_top_k": 5,
  "distance_threshold": null,
  "hybrid_alpha": 0.7,
  "hybrid_fallback_alpha": 0.9,
  "hybrid_limit": 50,
  "sql_limit": 80
}
```
- SQL Plan:
```json
{
  "table": "episodic_events",
  "fields": [
    "event_id",
    "video_id",
    "track_id",
    "start_time",
    "end_time",
    "object_type",
    "object_color_en",
    "scene_zone_en",
    "appearance_notes_en",
    "event_summary_en"
  ],
  "where": [
    {
      "field": "object_type",
      "op": "=",
      "value": "person"
    },
    {
      "field": "scene_zone_en",
      "op": "contains",
      "value": "left bleachers"
    }
  ],
  "order_by": "start_time ASC",
  "limit": 80
}
```
- Self Query Result:
```json
{
  "rewritten_query": "Find a person near the left bleachers",
  "user_need": "Retrieve basketball video results that satisfy: Find a person near the left bleachers",
  "intent_label": "semantic",
  "retrieval_focus": "semantic",
  "key_constraints": [
    "find",
    "a",
    "person",
    "near",
    "the",
    "left"
  ],
  "ambiguities": [],
  "reasoning_summary": "Fast-path preprocessing kept the original meaning and only normalized surface noise.",
  "confidence": 0.8,
  "original_user_query": "Find a person near the left bleachers."
}
```
- Raw Final Answer:
```json
{
  "raw_final_answer": "Retrieval complete. Most relevant results:\n[1] event_id=basketball_2.mp4_track_id_1 | video=basketball_2.mp4 | distance=0.201948881149292 | summary=standing near left bleachers with little motion Located in left bleachers. From 0.00s to 30.84s, a dark-clothed person stands near the left bleachers with little motion.\n[2] event_id=basketball_1.mp4_track_1 | video=basketball_1.mp4 | distance=0.32872921228408813 | summary=Little motion; standing near the left baseline/bench area. Located in sidewalk. From 0.0s to 61.2s, a person with unknown color stays mostly still near the left baseline/bench area.\n[3] event_id=basketball_1.mp4_track_29 | video=basketball_1.mp4 | distance=0.3379225730895996 | summary=Little motion; standing near the left side of the court. Located in sidewalk. From 43.8s to 125.7s, a person with unknown color remains mostly still near the left side of the court.\n[4] event_id=basketball_1.mp4_track_30 | video=basketball_1.mp4 | distance=0.3311508297920227 | summary=Little motion; standing near the left-center court area. Located in sidewalk. From 47.8s to 48.8s, a person with unknown color remains mostly still near the left-center court area.\n[5] event_id=basketball_1.mp4_track_11 | video=basketball_1.mp4 | distance=0.3382689356803894 | summary=Little motion; standing near the left-center baseline area. Located in sidewalk. From 11.5s to 91.8s, a person with unknown color remains mostly still near the left-center baseline area."
}
```
- LLM Final Output:
```json
{
  "llm_final_output": "A dark-clothed person stands near the left bleachers with little motion from 0.00s to 30.84s in *basketball_2.mp4*. In *basketball_1.mp4*, multiple individuals remain mostly still near the left baseline, bench area, or left side of the court at various times.\nSources: [hybrid] basketball_2.mp4 | event_id=basketball_2.mp4_track_id_1 | 0.0-30.84; [hybrid] basketball_1.mp4 | event_id=basketball_1.mp4_track_1 | 0.0-61.208333333333336; [hybrid] basketball_1.mp4 | event_id=basketball_1.mp4_track_29 | 43.791666666666664-125.70833333333331"
}
```
- Assertions:
```json
[
  {
    "name": "no_runtime_exception",
    "passed": true,
    "actual": [],
    "expected": null,
    "severity": "hard"
  },
  {
    "name": "route_in_expected",
    "passed": true,
    "actual": "hybrid_search",
    "expected": [
      "hybrid_search"
    ],
    "severity": "hard"
  },
  {
    "name": "final_answer_present",
    "passed": true,
    "actual": "A dark-clothed person stands near the left bleachers with little motion from 0.00s to 30.84s in *basketball_2.mp4*. In *basketball_1.mp4*, multiple individuals remain mostly still near the left baseline, bench area, or left side of the court at various times.\nSources: [hybrid] basketball_2.mp4 | event_id=basketball_2.mp4_track_id_1 | 0.0-30.84; [hybrid] basketball_1.mp4 | event_id=basketball_1.mp4_track_1 | 0.0-61.208333333333336; [hybrid] basketball_1.mp4 | event_id=basketball_1.mp4_track_29 | 43.791666666666664-125.70833333333331",
    "expected": "non-empty string",
    "severity": "hard"
  },
  {
    "name": "citation_present",
    "passed": true,
    "actual": "A dark-clothed person stands near the left bleachers with little motion from 0.00s to 30.84s in *basketball_2.mp4*. In *basketball_1.mp4*, multiple individuals remain mostly still near the left baseline, bench area, or left side of the court at various times.\nSources: [hybrid] basketball_2.mp4 | event_id=basketball_2.mp4_track_id_1 | 0.0-30.84; [hybrid] basketball_1.mp4 | event_id=basketball_1.mp4_track_1 | 0.0-61.208333333333336; [hybrid] basketball_1.mp4 | event_id=basketball_1.mp4_track_29 | 43.791666666666664-125.70833333333331",
    "expected": "final answer contains Sources:",
    "severity": "soft"
  },
  {
    "name": "grounding_coverage",
    "passed": true,
    "actual": {
      "summary": "A dark-clothed person stands near the left bleachers with little motion from 0.00s to 30.84s in *basketball_2.mp4*. In *basketball_1.mp4*, multiple individuals remain mostly still near the left baseline, bench area, or left side of the court at various times.",
      "style": "llm_summary",
      "confidence": 0.8,
      "citations": [
        {
          "source_type": "hybrid",
          "video_id": "basketball_2.mp4",
          "event_id": "basketball_2.mp4_track_id_1",
          "start_time": 0.0,
          "end_time": 30.84
        },
        {
          "source_type": "hybrid",
          "video_id": "basketball_1.mp4",
          "event_id": "basketball_1.mp4_track_1",
          "start_time": 0.0,
          "end_time": 61.208333333333336
        },
        {
          "source_type": "hybrid",
          "video_id": "basketball_1.mp4",
          "event_id": "basketball_1.mp4_track_29",
          "start_time": 43.791666666666664,
          "end_time": 125.70833333333331
        }
      ]
    },
    "expected": "summary_result.citations is non-empty",
    "severity": "soft"
  },
  {
    "name": "rewritten_query_present",
    "passed": true,
    "actual": "Find a person near the left bleachers",
    "expected": "non-empty rewritten query",
    "severity": "soft"
  },
  {
    "name": "user_need_identified",
    "passed": true,
    "actual": {
      "rewritten_query": "Find a person near the left bleachers",
      "user_need": "Retrieve basketball video results that satisfy: Find a person near the left bleachers",
      "intent_label": "semantic",
      "retrieval_focus": "semantic",
      "key_constraints": [
        "find",
        "a",
        "person",
        "near",
        "the",
        "left"
      ],
      "ambiguities": [],
      "reasoning_summary": "Fast-path preprocessing kept the original meaning and only normalized surface noise.",
      "confidence": 0.8,
      "original_user_query": "Find a person near the left bleachers."
    },
    "expected": "structured self-query result with user_need",
    "severity": "soft"
  },
  {
    "name": "trace_has_required_nodes",
    "passed": true,
    "actual": [
      "self_query_node",
      "query_classification_node",
      "parallel_retrieval_fusion_node",
      "final_answer_node",
      "summary_node"
    ],
    "expected": [
      "self_query_node",
      "final_answer_node",
      "summary_node"
    ],
    "severity": "soft"
  },
  {
    "name": "routing_metrics_present",
    "passed": true,
    "actual": {
      "execution_mode": "parallel_fusion",
      "label": "semantic",
      "query": "Find a person near the left bleachers",
      "sql_rows_count": 1,
      "hybrid_rows_count": 26,
      "sql_error": null,
      "hybrid_error": null
    },
    "expected": "non-empty routing_metrics",
    "severity": "soft"
  },
  {
    "name": "search_config_present",
    "passed": true,
    "actual": {
      "candidate_limit": 80,
      "top_k_per_event": 20,
      "rerank_top_k": 5,
      "distance_threshold": null,
      "hybrid_alpha": 0.7,
      "hybrid_fallback_alpha": 0.9,
      "hybrid_limit": 50,
      "sql_limit": 80
    },
    "expected": "non-empty search_config",
    "severity": "soft"
  },
  {
    "name": "no_tool_error",
    "passed": true,
    "actual": null,
    "expected": null,
    "severity": "soft"
  },
  {
    "name": "min_results",
    "passed": true,
    "actual": 27,
    "expected": 1,
    "severity": "hard"
  },
  {
    "name": "avg_latency_budget",
    "passed": true,
    "actual": 8638.14,
    "expected": 9000,
    "severity": "soft"
  },
  {
    "name": "semantic_backend_effective",
    "passed": true,
    "actual": {
      "hybrid_rows_count": 26,
      "hybrid_error": null,
      "degraded": false
    },
    "expected": "hybrid rows > 0 or explicit degradation/error",
    "severity": "hard"
  },
  {
    "name": "hybrid_health_consistency",
    "passed": true,
    "actual": {
      "hybrid_summary": "Hybrid direct retrieval complete",
      "hybrid_error": null,
      "degraded": false
    },
    "expected": "hybrid failure should be reflected by degraded flag or hybrid_error",
    "severity": "hard"
  }
]
```
- Last Iteration:
```json
{
  "elapsed_ms": 7958.14,
  "route_mode": "hybrid_search",
  "label": "semantic",
  "llm_final_output": "A dark-clothed person stands near the left bleachers with little motion from 0.00s to 30.84s in *basketball_2.mp4*. In *basketball_1.mp4*, multiple individuals remain mostly still near the left baseline, bench area, or left side of the court at various times.\nSources: [hybrid] basketball_2.mp4 | event_id=basketball_2.mp4_track_id_1 | 0.0-30.84; [hybrid] basketball_1.mp4 | event_id=basketball_1.mp4_track_1 | 0.0-61.208333333333336; [hybrid] basketball_1.mp4 | event_id=basketball_1.mp4_track_29 | 43.791666666666664-125.70833333333331",
  "raw_final_answer": "Retrieval complete. Most relevant results:\n[1] event_id=basketball_2.mp4_track_id_1 | video=basketball_2.mp4 | distance=0.201948881149292 | summary=standing near left bleachers with little motion Located in left bleachers. From 0.00s to 30.84s, a dark-clothed person stands near the left bleachers with little motion.\n[2] event_id=basketball_1.mp4_track_1 | video=basketball_1.mp4 | distance=0.32872921228408813 | summary=Little motion; standing near the left baseline/bench area. Located in sidewalk. From 0.0s to 61.2s, a person with unknown color stays mostly still near the left baseline/bench area.\n[3] event_id=basketball_1.mp4_track_29 | video=basketball_1.mp4 | distance=0.3379225730895996 | summary=Little motion; standing near the left side of the court. Located in sidewalk. From 43.8s to 125.7s, a person with unknown color remains mostly still near the left side of the court.\n[4] event_id=basketball_1.mp4_track_30 | video=basketball_1.mp4 | distance=0.3311508297920227 | summary=Little motion; standing near the left-center court area. Located in sidewalk. From 47.8s to 48.8s, a person with unknown color remains mostly still near the left-center court area.\n[5] event_id=basketball_1.mp4_track_11 | video=basketball_1.mp4 | distance=0.3382689356803894 | summary=Little motion; standing near the left-center baseline area. Located in sidewalk. From 11.5s to 91.8s, a person with unknown color remains mostly still near the left-center baseline area.",
  "rewritten_query": "Find a person near the left bleachers",
  "original_user_query": "Find a person near the left bleachers.",
  "self_query_result": {
    "rewritten_query": "Find a person near the left bleachers",
    "user_need": "Retrieve basketball video results that satisfy: Find a person near the left bleachers",
    "intent_label": "semantic",
    "retrieval_focus": "semantic",
    "key_constraints": [
      "find",
      "a",
      "person",
      "near",
      "the",
      "left"
    ],
    "ambiguities": [],
    "reasoning_summary": "Fast-path preprocessing kept the original meaning and only normalized surface noise.",
    "confidence": 0.8,
    "original_user_query": "Find a person near the left bleachers."
  },
  "summary_result": {
    "summary": "A dark-clothed person stands near the left bleachers with little motion from 0.00s to 30.84s in *basketball_2.mp4*. In *basketball_1.mp4*, multiple individuals remain mostly still near the left baseline, bench area, or left side of the court at various times.",
    "style": "llm_summary",
    "confidence": 0.8,
    "citations": [
      {
        "source_type": "hybrid",
        "video_id": "basketball_2.mp4",
        "event_id": "basketball_2.mp4_track_id_1",
        "start_time": 0.0,
        "end_time": 30.84
      },
      {
        "source_type": "hybrid",
        "video_id": "basketball_1.mp4",
        "event_id": "basketball_1.mp4_track_1",
        "start_time": 0.0,
        "end_time": 61.208333333333336
      },
      {
        "source_type": "hybrid",
        "video_id": "basketball_1.mp4",
        "event_id": "basketball_1.mp4_track_29",
        "start_time": 43.791666666666664,
        "end_time": 125.70833333333331
      }
    ]
  },
  "routing_metrics": {
    "execution_mode": "parallel_fusion",
    "label": "semantic",
    "query": "Find a person near the left bleachers",
    "sql_rows_count": 1,
    "hybrid_rows_count": 26,
    "sql_error": null,
    "hybrid_error": null
  },
  "search_config": {
    "candidate_limit": 80,
    "top_k_per_event": 20,
    "rerank_top_k": 5,
    "distance_threshold": null,
    "hybrid_alpha": 0.7,
    "hybrid_fallback_alpha": 0.9,
    "hybrid_limit": 50,
    "sql_limit": 80
  },
  "sql_plan": {
    "table": "episodic_events",
    "fields": [
      "event_id",
      "video_id",
      "track_id",
      "start_time",
      "end_time",
      "object_type",
      "object_color_en",
      "scene_zone_en",
      "appearance_notes_en",
      "event_summary_en"
    ],
    "where": [
      {
        "field": "object_type",
        "op": "=",
        "value": "person"
      },
      {
        "field": "scene_zone_en",
        "op": "contains",
        "value": "left bleachers"
      }
    ],
    "order_by": "start_time ASC",
    "limit": 80
  },
  "node_trace": [
    "self_query_node",
    "query_classification_node",
    "parallel_retrieval_fusion_node",
    "final_answer_node",
    "summary_node"
  ],
  "final_answer": "A dark-clothed person stands near the left bleachers with little motion from 0.00s to 30.84s in *basketball_2.mp4*. In *basketball_1.mp4*, multiple individuals remain mostly still near the left baseline, bench area, or left side of the court at various times.\nSources: [hybrid] basketball_2.mp4 | event_id=basketball_2.mp4_track_id_1 | 0.0-30.84; [hybrid] basketball_1.mp4 | event_id=basketball_1.mp4_track_1 | 0.0-61.208333333333336; [hybrid] basketball_1.mp4 | event_id=basketball_1.mp4_track_29 | 43.791666666666664-125.70833333333331",
  "tool_error": null,
  "error": null,
  "current_node": "summary_node",
  "top5": [
    {
      "event_id": "basketball_2.mp4_track_id_1",
      "video_id": "basketball_2.mp4",
      "event_text": "standing near left bleachers with little motion Located in left bleachers. From 0.00s to 30.84s, a dark-clothed person stands near the left bleachers with little motion.",
      "distance": 0.201948881149292
    },
    {
      "event_id": "basketball_1.mp4_track_1",
      "video_id": "basketball_1.mp4",
      "event_text": "Little motion; standing near the left baseline/bench area. Located in sidewalk. From 0.0s to 61.2s, a person with unknown color stays mostly still near the left baseline/bench area.",
      "distance": 0.32872921228408813
    },
    {
      "event_id": "basketball_1.mp4_track_29",
      "video_id": "basketball_1.mp4",
      "event_text": "Little motion; standing near the left side of the court. Located in sidewalk. From 43.8s to 125.7s, a person with unknown color remains mostly still near the left side of the court.",
      "distance": 0.3379225730895996
    },
    {
      "event_id": "basketball_1.mp4_track_30",
      "video_id": "basketball_1.mp4",
      "event_text": "Little motion; standing near the left-center court area. Located in sidewalk. From 47.8s to 48.8s, a person with unknown color remains mostly still near the left-center court area.",
      "distance": 0.3311508297920227
    },
    {
      "event_id": "basketball_1.mp4_track_11",
      "video_id": "basketball_1.mp4",
      "event_text": "Little motion; standing near the left-center baseline area. Located in sidewalk. From 11.5s to 91.8s, a person with unknown color remains mostly still near the left-center baseline area.",
      "distance": 0.3382689356803894
    }
  ],
  "merged_count": 27,
  "sql_rows_count": 1,
  "hybrid_rows_count": 26,
  "degraded": false,
  "hybrid_summary": "Hybrid direct retrieval complete",
  "sql_summary": "SQL direct retrieval rows=1",
  "hybrid_error": null,
  "sql_error": null,
  "sql_debug": {
    "duration": 2.8506075980003516,
    "sql_summary": "SQL direct retrieval rows=1",
    "hybrid_summary": "Hybrid direct retrieval complete",
    "sql_error": null,
    "hybrid_error": null,
    "fusion_meta": {
      "label": "semantic",
      "weights": {
        "sql": 0.2,
        "hybrid": 0.8
      },
      "rrf_k": 60.0,
      "sql_count": 1,
      "hybrid_count": 26,
      "fused_count": 27,
      "method": "weighted_rrf",
      "degraded": false
    }
  }
}
```
