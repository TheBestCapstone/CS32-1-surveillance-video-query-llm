# Comprehensive Agent Test Report

- Generated At: `2026-05-04 00:15:23`
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
  "passed": 6,
  "soft_failed": 2,
  "failed": 3,
  "pass_rate": 0.5455,
  "soft_fail_rate": 0.1818,
  "hard_fail_rate": 0.2727,
  "iterations_total": 15,
  "overall_avg_ms": 7287.22,
  "overall_p95_ms": 9264.93,
  "failure_categories": {
    "runtime_exception": 0,
    "route_mismatch": 0,
    "label_mismatch": 0,
    "tool_error": 0,
    "semantic_backend_failure": 0,
    "keyword_mismatch": 4,
    "result_size_violation": 1,
    "hybrid_health_inconsistency": 0,
    "citation_missing": 0,
    "grounding_gap": 0,
    "trace_gap": 0,
    "routing_metrics_missing": 0
  },
  "dimension_summary": {
    "functional": {
      "PASS": 2,
      "SOFT_FAIL": 2,
      "FAIL": 3
    },
    "routing": {
      "PASS": 2,
      "SOFT_FAIL": 1,
      "FAIL": 0
    },
    "filtering": {
      "PASS": 0,
      "SOFT_FAIL": 0,
      "FAIL": 2
    },
    "semantic": {
      "PASS": 2,
      "SOFT_FAIL": 2,
      "FAIL": 0
    },
    "behavior": {
      "PASS": 0,
      "SOFT_FAIL": 1,
      "FAIL": 0
    },
    "negative": {
      "PASS": 0,
      "SOFT_FAIL": 0,
      "FAIL": 1
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
      "PASS": 1,
      "SOFT_FAIL": 2,
      "FAIL": 2
    },
    "P1": {
      "PASS": 5,
      "SOFT_FAIL": 0,
      "FAIL": 1
    }
  },
  "metrics_summary": {
    "sql_branch_non_empty_rate": 1.0,
    "hybrid_branch_non_empty_rate": 0.0,
    "dual_branch_non_empty_rate": 0.0,
    "degraded_rate": 0.9091,
    "sql_error_rate": 0.0,
    "hybrid_error_rate": 0.9091,
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
  "sql_branch_non_empty_rate": 1.0,
  "hybrid_branch_non_empty_rate": 0.0,
  "dual_branch_non_empty_rate": 0.0,
  "degraded_rate": 0.9091,
  "sql_error_rate": 0.0,
  "hybrid_error_rate": 0.9091,
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
  "baseline": {},
  "actual": {
    "pure_sql_avg_ms": 9321.06,
    "hybrid_search_avg_ms": 5136.06,
    "semantic_label_cases_with_zero_hybrid_rows": 4,
    "semantic_label_cases_total": 4
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
- Avg Latency: `20744.55 ms`
- P95 Latency: `20744.55 ms`
- Node Trace:

```json
[
  "self_query_node",
  "query_classification_node",
  "parallel_retrieval_fusion_node",
  "match_verifier_node",
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
  "sql_rows_count": 1,
  "hybrid_rows_count": 0,
  "sql_error": null,
  "hybrid_error": "Collection expecting embedding with dimension of 1024, got 3072"
}
```

- Search Config:

```json
{
  "candidate_limit": 80,
  "top_k_per_event": 20,
  "rerank_top_k": 5,
  "rerank_candidate_limit": 20,
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
  "user_need": "Retrieve video results that satisfy: Did you see any person in the database",
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
  "expansion_terms": [],
  "base_rewritten_query": "Did you see any person in the database",
  "scene_constraints": [],
  "original_user_query": "Did you see any person in the database?"
}
```

- Raw Final Answer:

```json
{
  "raw_final_answer": "Retrieval complete. Most relevant results:\n[1] event_id=6 | video=Abuse038_x264 | distance=0.0 | summary=From 0.3s to 10.4s, several adults were talking on the side of the road. There were many vehicles on the road. Later, two puppies appeared on the road. A black car hit the two puppies."
}
```

- LLM Final Output:

```json
{
  "llm_final_output": "Yes. The relevant clip is in Abuse038_x264, around 0:00:00 - 0:00:10.\nSources: [hybrid] Abuse038_x264 | event_id=6 | 0.3-10.4"
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
    "actual": "Yes. The relevant clip is in Abuse038_x264, around 0:00:00 - 0:00:10.\nSources: [hybrid] Abuse038_x264 | event_id=6 | 0.3-10.4",
    "expected": "non-empty string",
    "severity": "hard"
  },
  {
    "name": "citation_present",
    "passed": true,
    "actual": "Yes. The relevant clip is in Abuse038_x264, around 0:00:00 - 0:00:10.\nSources: [hybrid] Abuse038_x264 | event_id=6 | 0.3-10.4",
    "expected": "final answer contains Sources:",
    "severity": "soft"
  },
  {
    "name": "grounding_coverage",
    "passed": true,
    "actual": {
      "summary": "Yes. The relevant clip is in Abuse038_x264, around 0:00:00 - 0:00:10.",
      "style": "llm_summary",
      "confidence": 0.8,
      "citations": [
        {
          "source_type": "hybrid",
          "video_id": "Abuse038_x264",
          "event_id": 6,
          "start_time": 0.3,
          "end_time": 10.4,
          "record_level": "child"
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
      "user_need": "Retrieve video results that satisfy: Did you see any person in the database",
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
      "expansion_terms": [],
      "base_rewritten_query": "Did you see any person in the database",
      "scene_constraints": [],
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
      "match_verifier_node",
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
      "sql_rows_count": 1,
      "hybrid_rows_count": 0,
      "sql_error": null,
      "hybrid_error": "Collection expecting embedding with dimension of 1024, got 3072"
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
      "rerank_candidate_limit": 20,
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
    "actual": 1,
    "expected": 1,
    "severity": "hard"
  },
  {
    "name": "min_sql_rows",
    "passed": true,
    "actual": 1,
    "expected": 1,
    "severity": "hard"
  },
  {
    "name": "top_field_video_id",
    "passed": true,
    "actual": [
      "Abuse038_x264"
    ],
    "expected": "non-empty",
    "severity": "soft"
  },
  {
    "name": "top_field_event_text",
    "passed": true,
    "actual": [
      "From 0.3s to 10.4s, several adults were talking on the side of the road. There were many vehicles on the road. Later, two puppies appeared on the road. A black car hit the two puppies."
    ],
    "expected": "non-empty",
    "severity": "soft"
  }
]
```

- Last Iteration:

```json
{
  "elapsed_ms": 20744.55,
  "route_mode": "pure_sql",
  "label": "structured",
  "llm_final_output": "Yes. The relevant clip is in Abuse038_x264, around 0:00:00 - 0:00:10.\nSources: [hybrid] Abuse038_x264 | event_id=6 | 0.3-10.4",
  "raw_final_answer": "Retrieval complete. Most relevant results:\n[1] event_id=6 | video=Abuse038_x264 | distance=0.0 | summary=From 0.3s to 10.4s, several adults were talking on the side of the road. There were many vehicles on the road. Later, two puppies appeared on the road. A black car hit the two puppies.",
  "rewritten_query": "Did you see any person in the database",
  "original_user_query": "Did you see any person in the database?",
  "self_query_result": {
    "rewritten_query": "Did you see any person in the database",
    "user_need": "Retrieve video results that satisfy: Did you see any person in the database",
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
    "expansion_terms": [],
    "base_rewritten_query": "Did you see any person in the database",
    "scene_constraints": [],
    "original_user_query": "Did you see any person in the database?"
  },
  "summary_result": {
    "summary": "Yes. The relevant clip is in Abuse038_x264, around 0:00:00 - 0:00:10.",
    "style": "llm_summary",
    "confidence": 0.8,
    "citations": [
      {
        "source_type": "hybrid",
        "video_id": "Abuse038_x264",
        "event_id": 6,
        "start_time": 0.3,
        "end_time": 10.4,
        "record_level": "child"
      }
    ]
  },
  "routing_metrics": {
    "execution_mode": "parallel_fusion",
    "label": "structured",
    "query": "Did you see any person in the database",
    "sql_rows_count": 1,
    "hybrid_rows_count": 0,
    "sql_error": null,
    "hybrid_error": "Collection expecting embedding with dimension of 1024, got 3072"
  },
  "search_config": {
    "candidate_limit": 80,
    "top_k_per_event": 20,
    "rerank_top_k": 5,
    "rerank_candidate_limit": 20,
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
    "match_verifier_node",
    "final_answer_node",
    "summary_node"
  ],
  "final_answer": "Yes. The relevant clip is in Abuse038_x264, around 0:00:00 - 0:00:10.\nSources: [hybrid] Abuse038_x264 | event_id=6 | 0.3-10.4",
  "tool_error": null,
  "error": null,
  "current_node": "summary_node",
  "top5": [
    {
      "event_id": 6,
      "video_id": "Abuse038_x264",
      "event_text": "From 0.3s to 10.4s, several adults were talking on the side of the road. There were many vehicles on the road. Later, two puppies appeared on the road. A black car hit the two puppies.",
      "distance": 0.0
    }
  ],
  "merged_count": 1,
  "sql_rows_count": 1,
  "hybrid_rows_count": 0,
  "degraded": true,
  "hybrid_summary": "",
  "sql_summary": "Deterministic SQL planner retrieval complete rows=1 stage=guided",
  "hybrid_error": "Collection expecting embedding with dimension of 1024, got 3072",
  "sql_error": null,
  "sql_debug": {
    "duration": 10.523084176995326,
    "sql_summary": "Deterministic SQL planner retrieval complete rows=1 stage=guided",
    "hybrid_summary": "",
    "sql_error": null,
    "hybrid_error": "Collection expecting embedding with dimension of 1024, got 3072",
    "fusion_meta": {
      "label": "structured",
      "degraded": true,
      "degraded_reason": "hybrid_failed",
      "method": "fallback_sql_only"
    },
    "rerank_meta": {
      "enabled": true,
      "model": "cross-encoder/ms-marco-MiniLM-L-6-v2",
      "input_count": 1,
      "candidate_count": 1,
      "output_count": 1
    },
    "parent_rows_count": 1,
    "result_mode": "child_only",
    "parent_context": [
      {
        "video_id": "Abuse038_x264",
        "child_hit_count": 1,
        "start_time": 0.3,
        "end_time": 10.4,
        "best_distance": 0.0,
        "best_hybrid_score": null,
        "track_ids": [],
        "object_types": [
          "car"
        ],
        "object_colors": [
          "black"
        ],
        "scene_zones": [
          "road"
        ],
        "parent_rank": 1
      }
    ]
  }
}
```

## FNC_SQL_002

- Suite: `core_regression`
- Priority: `P0`
- Dimensions: `functional, filtering`
- Description: Color filtering should surface dark-clothed results for a structured query.
- Query: `Show me dark-clothed persons.`
- Status: `FAIL`
- Avg Latency: `7483.32 ms`
- P95 Latency: `7483.32 ms`
- Node Trace:

```json
[
  "self_query_node",
  "query_classification_node",
  "parallel_retrieval_fusion_node",
  "match_verifier_node",
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
  "sql_rows_count": 9,
  "hybrid_rows_count": 0,
  "sql_error": null,
  "hybrid_error": "Collection expecting embedding with dimension of 1024, got 3072"
}
```

- Search Config:

```json
{
  "candidate_limit": 80,
  "top_k_per_event": 20,
  "rerank_top_k": 5,
  "rerank_candidate_limit": 20,
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
  "user_need": "Retrieve video results that satisfy: Show me dark-clothed persons",
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
  "expansion_terms": [],
  "base_rewritten_query": "Show me dark-clothed persons",
  "scene_constraints": [],
  "original_user_query": "Show me dark-clothed persons."
}
```

- Raw Final Answer:

```json
{
  "raw_final_answer": "Retrieval complete. Most relevant results:\n[1] event_id=6 | video=Abuse038_x264 | distance=0.0 | summary=From 0.3s to 10.4s, several adults were talking on the side of the road. There were many vehicles on the road. Later, two puppies appeared on the road. A black car hit the two puppies.\n[2] event_id=3 | video=Abuse037_x264 | distance=0.0 | summary=From 25.3s to 48.5s, there was a black dog left on the road. It walked to the middle of the road next to the dog that had just been crushed.\n[3] event_id=4 | video=Abuse037_x264 | distance=0.0 | summary=From 48.5s to 59.1s, the black dog walked away and left the middle of the road.\n[4] event_id=1 | video=Abuse037_x264 | distance=0.0 | summary=From 1.2s to 8.2s, a white car with double flashes slowly appeared on the screen, crushing the black dog walking in the middle of the road.\n[5] event_id=5 | video=Abuse037_x264 | distance=0.0 | summary=From 40.4s to 47.6s, the gray dog pulled out the tail of the dog that had just been run over by the car, then stayed for a few minutes and left."
}
```

- LLM Final Output:

```json
{
  "llm_final_output": "The most relevant clip is in Abuse038_x264, around 0:00:00 - 0:00:10.\nSources: [hybrid] Abuse038_x264 | event_id=6 | 0.3-10.4; [hybrid] Abuse037_x264 | event_id=3 | 25.3-48.5; [hybrid] Abuse037_x264 | event_id=4 | 48.5-59.1"
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
    "actual": "The most relevant clip is in Abuse038_x264, around 0:00:00 - 0:00:10.\nSources: [hybrid] Abuse038_x264 | event_id=6 | 0.3-10.4; [hybrid] Abuse037_x264 | event_id=3 | 25.3-48.5; [hybrid] Abuse037_x264 | event_id=4 | 48.5-59.1",
    "expected": "non-empty string",
    "severity": "hard"
  },
  {
    "name": "citation_present",
    "passed": true,
    "actual": "The most relevant clip is in Abuse038_x264, around 0:00:00 - 0:00:10.\nSources: [hybrid] Abuse038_x264 | event_id=6 | 0.3-10.4; [hybrid] Abuse037_x264 | event_id=3 | 25.3-48.5; [hybrid] Abuse037_x264 | event_id=4 | 48.5-59.1",
    "expected": "final answer contains Sources:",
    "severity": "soft"
  },
  {
    "name": "grounding_coverage",
    "passed": true,
    "actual": {
      "summary": "The most relevant clip is in Abuse038_x264, around 0:00:00 - 0:00:10.",
      "style": "llm_summary",
      "confidence": 0.8,
      "citations": [
        {
          "source_type": "hybrid",
          "video_id": "Abuse038_x264",
          "event_id": 6,
          "start_time": 0.3,
          "end_time": 10.4,
          "record_level": "child"
        },
        {
          "source_type": "hybrid",
          "video_id": "Abuse037_x264",
          "event_id": 3,
          "start_time": 25.3,
          "end_time": 48.5,
          "record_level": "child"
        },
        {
          "source_type": "hybrid",
          "video_id": "Abuse037_x264",
          "event_id": 4,
          "start_time": 48.5,
          "end_time": 59.1,
          "record_level": "child"
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
      "user_need": "Retrieve video results that satisfy: Show me dark-clothed persons",
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
      "expansion_terms": [],
      "base_rewritten_query": "Show me dark-clothed persons",
      "scene_constraints": [],
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
      "match_verifier_node",
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
      "sql_rows_count": 9,
      "hybrid_rows_count": 0,
      "sql_error": null,
      "hybrid_error": "Collection expecting embedding with dimension of 1024, got 3072"
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
      "rerank_candidate_limit": 20,
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
    "actual": 5,
    "expected": 1,
    "severity": "hard"
  },
  {
    "name": "min_sql_rows",
    "passed": true,
    "actual": 9,
    "expected": 1,
    "severity": "hard"
  },
  {
    "name": "expected_keywords_any",
    "passed": false,
    "actual": "from 0.3s to 10.4s, several adults were talking on the side of the road. there were many vehicles on the road. later, two puppies appeared on the road. a black car hit the two puppies. from 25.3s to 48.5s, there was a black dog left on the road. it walked to the middle of the road next to the dog that had just been crushed. from 48.5s to 59.1s, the black dog walked away and left the middle of the road. from 1.2s to 8.2s, a white car with double flashes slowly appeared on the screen, crushing the black dog walking in the middle of the road. from 40.4s to 47.6s, the gray dog pulled out the tail of the dog that had just been run over by the car, then stayed for a few minutes and left.",
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
  "elapsed_ms": 7483.32,
  "route_mode": "pure_sql",
  "label": "structured",
  "llm_final_output": "The most relevant clip is in Abuse038_x264, around 0:00:00 - 0:00:10.\nSources: [hybrid] Abuse038_x264 | event_id=6 | 0.3-10.4; [hybrid] Abuse037_x264 | event_id=3 | 25.3-48.5; [hybrid] Abuse037_x264 | event_id=4 | 48.5-59.1",
  "raw_final_answer": "Retrieval complete. Most relevant results:\n[1] event_id=6 | video=Abuse038_x264 | distance=0.0 | summary=From 0.3s to 10.4s, several adults were talking on the side of the road. There were many vehicles on the road. Later, two puppies appeared on the road. A black car hit the two puppies.\n[2] event_id=3 | video=Abuse037_x264 | distance=0.0 | summary=From 25.3s to 48.5s, there was a black dog left on the road. It walked to the middle of the road next to the dog that had just been crushed.\n[3] event_id=4 | video=Abuse037_x264 | distance=0.0 | summary=From 48.5s to 59.1s, the black dog walked away and left the middle of the road.\n[4] event_id=1 | video=Abuse037_x264 | distance=0.0 | summary=From 1.2s to 8.2s, a white car with double flashes slowly appeared on the screen, crushing the black dog walking in the middle of the road.\n[5] event_id=5 | video=Abuse037_x264 | distance=0.0 | summary=From 40.4s to 47.6s, the gray dog pulled out the tail of the dog that had just been run over by the car, then stayed for a few minutes and left.",
  "rewritten_query": "Show me dark-clothed persons",
  "original_user_query": "Show me dark-clothed persons.",
  "self_query_result": {
    "rewritten_query": "Show me dark-clothed persons",
    "user_need": "Retrieve video results that satisfy: Show me dark-clothed persons",
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
    "expansion_terms": [],
    "base_rewritten_query": "Show me dark-clothed persons",
    "scene_constraints": [],
    "original_user_query": "Show me dark-clothed persons."
  },
  "summary_result": {
    "summary": "The most relevant clip is in Abuse038_x264, around 0:00:00 - 0:00:10.",
    "style": "llm_summary",
    "confidence": 0.8,
    "citations": [
      {
        "source_type": "hybrid",
        "video_id": "Abuse038_x264",
        "event_id": 6,
        "start_time": 0.3,
        "end_time": 10.4,
        "record_level": "child"
      },
      {
        "source_type": "hybrid",
        "video_id": "Abuse037_x264",
        "event_id": 3,
        "start_time": 25.3,
        "end_time": 48.5,
        "record_level": "child"
      },
      {
        "source_type": "hybrid",
        "video_id": "Abuse037_x264",
        "event_id": 4,
        "start_time": 48.5,
        "end_time": 59.1,
        "record_level": "child"
      }
    ]
  },
  "routing_metrics": {
    "execution_mode": "parallel_fusion",
    "label": "structured",
    "query": "Show me dark-clothed persons",
    "sql_rows_count": 9,
    "hybrid_rows_count": 0,
    "sql_error": null,
    "hybrid_error": "Collection expecting embedding with dimension of 1024, got 3072"
  },
  "search_config": {
    "candidate_limit": 80,
    "top_k_per_event": 20,
    "rerank_top_k": 5,
    "rerank_candidate_limit": 20,
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
    "match_verifier_node",
    "final_answer_node",
    "summary_node"
  ],
  "final_answer": "The most relevant clip is in Abuse038_x264, around 0:00:00 - 0:00:10.\nSources: [hybrid] Abuse038_x264 | event_id=6 | 0.3-10.4; [hybrid] Abuse037_x264 | event_id=3 | 25.3-48.5; [hybrid] Abuse037_x264 | event_id=4 | 48.5-59.1",
  "tool_error": null,
  "error": null,
  "current_node": "summary_node",
  "top5": [
    {
      "event_id": 6,
      "video_id": "Abuse038_x264",
      "event_text": "From 0.3s to 10.4s, several adults were talking on the side of the road. There were many vehicles on the road. Later, two puppies appeared on the road. A black car hit the two puppies.",
      "distance": 0.0
    },
    {
      "event_id": 3,
      "video_id": "Abuse037_x264",
      "event_text": "From 25.3s to 48.5s, there was a black dog left on the road. It walked to the middle of the road next to the dog that had just been crushed.",
      "distance": 0.0
    },
    {
      "event_id": 4,
      "video_id": "Abuse037_x264",
      "event_text": "From 48.5s to 59.1s, the black dog walked away and left the middle of the road.",
      "distance": 0.0
    },
    {
      "event_id": 1,
      "video_id": "Abuse037_x264",
      "event_text": "From 1.2s to 8.2s, a white car with double flashes slowly appeared on the screen, crushing the black dog walking in the middle of the road.",
      "distance": 0.0
    },
    {
      "event_id": 5,
      "video_id": "Abuse037_x264",
      "event_text": "From 40.4s to 47.6s, the gray dog pulled out the tail of the dog that had just been run over by the car, then stayed for a few minutes and left.",
      "distance": 0.0
    }
  ],
  "merged_count": 5,
  "sql_rows_count": 9,
  "hybrid_rows_count": 0,
  "degraded": true,
  "hybrid_summary": "",
  "sql_summary": "Deterministic SQL planner retrieval complete rows=9 stage=guided",
  "hybrid_error": "Collection expecting embedding with dimension of 1024, got 3072",
  "sql_error": null,
  "sql_debug": {
    "duration": 1.6410078629851341,
    "sql_summary": "Deterministic SQL planner retrieval complete rows=9 stage=guided",
    "hybrid_summary": "",
    "sql_error": null,
    "hybrid_error": "Collection expecting embedding with dimension of 1024, got 3072",
    "fusion_meta": {
      "label": "structured",
      "degraded": true,
      "degraded_reason": "hybrid_failed",
      "method": "fallback_sql_only"
    },
    "rerank_meta": {
      "enabled": true,
      "model": "cross-encoder/ms-marco-MiniLM-L-6-v2",
      "input_count": 9,
      "candidate_count": 9,
      "output_count": 9
    },
    "parent_rows_count": 5,
    "result_mode": "child_only",
    "parent_context": [
      {
        "video_id": "Abuse038_x264",
        "child_hit_count": 5,
        "start_time": 0.3,
        "end_time": 28.0,
        "best_distance": 0.0,
        "best_hybrid_score": null,
        "track_ids": [],
        "object_types": [
          "car",
          "dog"
        ],
        "object_colors": [
          "black",
          "unknown"
        ],
        "scene_zones": [
          "road"
        ],
        "parent_rank": 1
      },
      {
        "video_id": "Abuse037_x264",
        "child_hit_count": 4,
        "start_time": 1.2,
        "end_time": 59.1,
        "best_distance": 0.0,
        "best_hybrid_score": null,
        "track_ids": [],
        "object_types": [
          "dog",
          "car"
        ],
        "object_colors": [
          "black",
          "gray"
        ],
        "scene_zones": [
          "road",
          "unknown"
        ],
        "parent_rank": 2
      }
    ]
  }
}
```

## FNC_HYB_001

- Suite: `semantic_regression`
- Priority: `P0`
- Dimensions: `functional, semantic, routing`
- Description: Semantic location query should route to hybrid_search and activate semantic retrieval.
- Query: `Find a person near the left bleachers.`
- Status: `SOFT_FAIL`
- Avg Latency: `5751.64 ms`
- P95 Latency: `5751.64 ms`
- Node Trace:

```json
[
  "self_query_node",
  "query_classification_node",
  "parallel_retrieval_fusion_node",
  "match_verifier_node",
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
  "sql_rows_count": 5,
  "hybrid_rows_count": 0,
  "sql_error": null,
  "hybrid_error": "Collection expecting embedding with dimension of 1024, got 3072"
}
```

- Search Config:

```json
{
  "candidate_limit": 80,
  "top_k_per_event": 20,
  "rerank_top_k": 5,
  "rerank_candidate_limit": 20,
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
  "user_need": "Retrieve video results that satisfy: Find a person near the left bleachers",
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
  "expansion_terms": [],
  "base_rewritten_query": "Find a person near the left bleachers",
  "scene_constraints": [],
  "original_user_query": "Find a person near the left bleachers."
}
```

- Raw Final Answer:

```json
{
  "raw_final_answer": "Retrieval complete. Most relevant results:\n[1] event_id=3 | video=Abuse037_x264 | distance=0.0 | summary=From 25.3s to 48.5s, there was a black dog left on the road. It walked to the middle of the road next to the dog that had just been crushed.\n[2] event_id=4 | video=Abuse037_x264 | distance=0.0 | summary=From 48.5s to 59.1s, the black dog walked away and left the middle of the road.\n[3] event_id=5 | video=Abuse037_x264 | distance=0.0 | summary=From 40.4s to 47.6s, the gray dog pulled out the tail of the dog that had just been run over by the car, then stayed for a few minutes and left.\n[4] event_id=7 | video=Abuse038_x264 | distance=0.0 | summary=From 11.5s to 17.2s, two puppies rolled on the road, then one of the dogs left the road and the other stopped in the middle of the road.\n[5] event_id=6 | video=Abuse038_x264 | distance=0.0 | summary=From 0.3s to 10.4s, several adults were talking on the side of the road. There were many vehicles on the road. Later, two puppies appeared on the road. A black car hit the two puppies."
}
```

- LLM Final Output:

```json
{
  "llm_final_output": "The most relevant clip is in Abuse037_x264, around 0:00:25 - 0:00:48.\nSources: [hybrid] Abuse037_x264 | event_id=3 | 25.3-48.5; [hybrid] Abuse037_x264 | event_id=4 | 48.5-59.1; [hybrid] Abuse037_x264 | event_id=5 | 40.4-47.6"
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
    "actual": "The most relevant clip is in Abuse037_x264, around 0:00:25 - 0:00:48.\nSources: [hybrid] Abuse037_x264 | event_id=3 | 25.3-48.5; [hybrid] Abuse037_x264 | event_id=4 | 48.5-59.1; [hybrid] Abuse037_x264 | event_id=5 | 40.4-47.6",
    "expected": "non-empty string",
    "severity": "hard"
  },
  {
    "name": "citation_present",
    "passed": true,
    "actual": "The most relevant clip is in Abuse037_x264, around 0:00:25 - 0:00:48.\nSources: [hybrid] Abuse037_x264 | event_id=3 | 25.3-48.5; [hybrid] Abuse037_x264 | event_id=4 | 48.5-59.1; [hybrid] Abuse037_x264 | event_id=5 | 40.4-47.6",
    "expected": "final answer contains Sources:",
    "severity": "soft"
  },
  {
    "name": "grounding_coverage",
    "passed": true,
    "actual": {
      "summary": "The most relevant clip is in Abuse037_x264, around 0:00:25 - 0:00:48.",
      "style": "llm_summary",
      "confidence": 0.8,
      "citations": [
        {
          "source_type": "hybrid",
          "video_id": "Abuse037_x264",
          "event_id": 3,
          "start_time": 25.3,
          "end_time": 48.5,
          "record_level": "child"
        },
        {
          "source_type": "hybrid",
          "video_id": "Abuse037_x264",
          "event_id": 4,
          "start_time": 48.5,
          "end_time": 59.1,
          "record_level": "child"
        },
        {
          "source_type": "hybrid",
          "video_id": "Abuse037_x264",
          "event_id": 5,
          "start_time": 40.4,
          "end_time": 47.6,
          "record_level": "child"
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
      "user_need": "Retrieve video results that satisfy: Find a person near the left bleachers",
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
      "expansion_terms": [],
      "base_rewritten_query": "Find a person near the left bleachers",
      "scene_constraints": [],
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
      "match_verifier_node",
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
      "sql_rows_count": 5,
      "hybrid_rows_count": 0,
      "sql_error": null,
      "hybrid_error": "Collection expecting embedding with dimension of 1024, got 3072"
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
      "rerank_candidate_limit": 20,
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
    "actual": 5,
    "expected": 1,
    "severity": "hard"
  },
  {
    "name": "expected_keywords_any",
    "passed": false,
    "actual": "from 25.3s to 48.5s, there was a black dog left on the road. it walked to the middle of the road next to the dog that had just been crushed. from 48.5s to 59.1s, the black dog walked away and left the middle of the road. from 40.4s to 47.6s, the gray dog pulled out the tail of the dog that had just been run over by the car, then stayed for a few minutes and left. from 11.5s to 17.2s, two puppies rolled on the road, then one of the dogs left the road and the other stopped in the middle of the road. from 0.3s to 10.4s, several adults were talking on the side of the road. there were many vehicles on the road. later, two puppies appeared on the road. a black car hit the two puppies.",
    "expected": [
      "bleachers"
    ],
    "severity": "soft"
  },
  {
    "name": "semantic_backend_effective",
    "passed": true,
    "actual": {
      "hybrid_rows_count": 0,
      "hybrid_error": "Collection expecting embedding with dimension of 1024, got 3072",
      "degraded": true
    },
    "expected": "hybrid rows > 0 or explicit degradation/error",
    "severity": "hard"
  },
  {
    "name": "hybrid_health_consistency",
    "passed": true,
    "actual": {
      "hybrid_summary": "",
      "hybrid_error": "Collection expecting embedding with dimension of 1024, got 3072",
      "degraded": true
    },
    "expected": "hybrid failure should be reflected by degraded flag or hybrid_error",
    "severity": "hard"
  }
]
```

- Last Iteration:

```json
{
  "elapsed_ms": 5751.64,
  "route_mode": "hybrid_search",
  "label": "semantic",
  "llm_final_output": "The most relevant clip is in Abuse037_x264, around 0:00:25 - 0:00:48.\nSources: [hybrid] Abuse037_x264 | event_id=3 | 25.3-48.5; [hybrid] Abuse037_x264 | event_id=4 | 48.5-59.1; [hybrid] Abuse037_x264 | event_id=5 | 40.4-47.6",
  "raw_final_answer": "Retrieval complete. Most relevant results:\n[1] event_id=3 | video=Abuse037_x264 | distance=0.0 | summary=From 25.3s to 48.5s, there was a black dog left on the road. It walked to the middle of the road next to the dog that had just been crushed.\n[2] event_id=4 | video=Abuse037_x264 | distance=0.0 | summary=From 48.5s to 59.1s, the black dog walked away and left the middle of the road.\n[3] event_id=5 | video=Abuse037_x264 | distance=0.0 | summary=From 40.4s to 47.6s, the gray dog pulled out the tail of the dog that had just been run over by the car, then stayed for a few minutes and left.\n[4] event_id=7 | video=Abuse038_x264 | distance=0.0 | summary=From 11.5s to 17.2s, two puppies rolled on the road, then one of the dogs left the road and the other stopped in the middle of the road.\n[5] event_id=6 | video=Abuse038_x264 | distance=0.0 | summary=From 0.3s to 10.4s, several adults were talking on the side of the road. There were many vehicles on the road. Later, two puppies appeared on the road. A black car hit the two puppies.",
  "rewritten_query": "Find a person near the left bleachers",
  "original_user_query": "Find a person near the left bleachers.",
  "self_query_result": {
    "rewritten_query": "Find a person near the left bleachers",
    "user_need": "Retrieve video results that satisfy: Find a person near the left bleachers",
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
    "expansion_terms": [],
    "base_rewritten_query": "Find a person near the left bleachers",
    "scene_constraints": [],
    "original_user_query": "Find a person near the left bleachers."
  },
  "summary_result": {
    "summary": "The most relevant clip is in Abuse037_x264, around 0:00:25 - 0:00:48.",
    "style": "llm_summary",
    "confidence": 0.8,
    "citations": [
      {
        "source_type": "hybrid",
        "video_id": "Abuse037_x264",
        "event_id": 3,
        "start_time": 25.3,
        "end_time": 48.5,
        "record_level": "child"
      },
      {
        "source_type": "hybrid",
        "video_id": "Abuse037_x264",
        "event_id": 4,
        "start_time": 48.5,
        "end_time": 59.1,
        "record_level": "child"
      },
      {
        "source_type": "hybrid",
        "video_id": "Abuse037_x264",
        "event_id": 5,
        "start_time": 40.4,
        "end_time": 47.6,
        "record_level": "child"
      }
    ]
  },
  "routing_metrics": {
    "execution_mode": "parallel_fusion",
    "label": "semantic",
    "query": "Find a person near the left bleachers",
    "sql_rows_count": 5,
    "hybrid_rows_count": 0,
    "sql_error": null,
    "hybrid_error": "Collection expecting embedding with dimension of 1024, got 3072"
  },
  "search_config": {
    "candidate_limit": 80,
    "top_k_per_event": 20,
    "rerank_top_k": 5,
    "rerank_candidate_limit": 20,
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
    "match_verifier_node",
    "final_answer_node",
    "summary_node"
  ],
  "final_answer": "The most relevant clip is in Abuse037_x264, around 0:00:25 - 0:00:48.\nSources: [hybrid] Abuse037_x264 | event_id=3 | 25.3-48.5; [hybrid] Abuse037_x264 | event_id=4 | 48.5-59.1; [hybrid] Abuse037_x264 | event_id=5 | 40.4-47.6",
  "tool_error": null,
  "error": null,
  "current_node": "summary_node",
  "top5": [
    {
      "event_id": 3,
      "video_id": "Abuse037_x264",
      "event_text": "From 25.3s to 48.5s, there was a black dog left on the road. It walked to the middle of the road next to the dog that had just been crushed.",
      "distance": 0.0
    },
    {
      "event_id": 4,
      "video_id": "Abuse037_x264",
      "event_text": "From 48.5s to 59.1s, the black dog walked away and left the middle of the road.",
      "distance": 0.0
    },
    {
      "event_id": 5,
      "video_id": "Abuse037_x264",
      "event_text": "From 40.4s to 47.6s, the gray dog pulled out the tail of the dog that had just been run over by the car, then stayed for a few minutes and left.",
      "distance": 0.0
    },
    {
      "event_id": 7,
      "video_id": "Abuse038_x264",
      "event_text": "From 11.5s to 17.2s, two puppies rolled on the road, then one of the dogs left the road and the other stopped in the middle of the road.",
      "distance": 0.0
    },
    {
      "event_id": 6,
      "video_id": "Abuse038_x264",
      "event_text": "From 0.3s to 10.4s, several adults were talking on the side of the road. There were many vehicles on the road. Later, two puppies appeared on the road. A black car hit the two puppies.",
      "distance": 0.0
    }
  ],
  "merged_count": 5,
  "sql_rows_count": 5,
  "hybrid_rows_count": 0,
  "degraded": true,
  "hybrid_summary": "",
  "sql_summary": "Deterministic SQL planner retrieval complete rows=5 stage=guided",
  "hybrid_error": "Collection expecting embedding with dimension of 1024, got 3072",
  "sql_error": null,
  "sql_debug": {
    "duration": 0.17856294100056402,
    "sql_summary": "Deterministic SQL planner retrieval complete rows=5 stage=guided",
    "hybrid_summary": "",
    "sql_error": null,
    "hybrid_error": "Collection expecting embedding with dimension of 1024, got 3072",
    "fusion_meta": {
      "label": "semantic",
      "degraded": true,
      "degraded_reason": "hybrid_failed",
      "method": "fallback_sql_only"
    },
    "rerank_meta": {
      "enabled": true,
      "model": "cross-encoder/ms-marco-MiniLM-L-6-v2",
      "input_count": 5,
      "candidate_count": 5,
      "output_count": 5
    },
    "parent_rows_count": 5,
    "result_mode": "child_only",
    "parent_context": [
      {
        "video_id": "Abuse037_x264",
        "child_hit_count": 3,
        "start_time": 25.3,
        "end_time": 59.1,
        "best_distance": 0.0,
        "best_hybrid_score": null,
        "track_ids": [],
        "object_types": [
          "dog",
          "car"
        ],
        "object_colors": [
          "black",
          "gray"
        ],
        "scene_zones": [
          "road",
          "unknown"
        ],
        "parent_rank": 1
      },
      {
        "video_id": "Abuse038_x264",
        "child_hit_count": 2,
        "start_time": 0.3,
        "end_time": 17.2,
        "best_distance": 0.0,
        "best_hybrid_score": null,
        "track_ids": [],
        "object_types": [
          "dog",
          "car"
        ],
        "object_colors": [
          "unknown",
          "black"
        ],
        "scene_zones": [
          "road"
        ],
        "parent_rank": 2
      }
    ]
  }
}
```

## FNC_HYB_002

- Suite: `semantic_regression`
- Priority: `P0`
- Dimensions: `functional, semantic, behavior`
- Description: Behavior + location query should route to hybrid_search and preserve semantic capability.
- Query: `Look for a person moving on the sidewalk.`
- Status: `SOFT_FAIL`
- Avg Latency: `5454.23 ms`
- P95 Latency: `5454.23 ms`
- Node Trace:

```json
[
  "self_query_node",
  "query_classification_node",
  "parallel_retrieval_fusion_node",
  "match_verifier_node",
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
  "sql_rows_count": 2,
  "hybrid_rows_count": 0,
  "sql_error": null,
  "hybrid_error": "Collection expecting embedding with dimension of 1024, got 3072"
}
```

- Search Config:

```json
{
  "candidate_limit": 80,
  "top_k_per_event": 20,
  "rerank_top_k": 5,
  "rerank_candidate_limit": 20,
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
  "user_need": "Retrieve video results that satisfy: Look for a person moving on the sidewalk",
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
  "expansion_terms": [],
  "base_rewritten_query": "Look for a person moving on the sidewalk",
  "scene_constraints": [],
  "original_user_query": "Look for a person moving on the sidewalk."
}
```

- Raw Final Answer:

```json
{
  "raw_final_answer": "Retrieval complete. Most relevant results:\n[1] event_id=6 | video=Abuse038_x264 | distance=0.0 | summary=From 0.3s to 10.4s, several adults were talking on the side of the road. There were many vehicles on the road. Later, two puppies appeared on the road. A black car hit the two puppies.\n[2] event_id=10 | video=Abuse038_x264 | distance=0.0 | summary=From 20.6s to 28.0s, the cars on the road continue to move forward slowly."
}
```

- LLM Final Output:

```json
{
  "llm_final_output": "The most relevant clip is in Abuse038_x264, around 0:00:00 - 0:00:10.\nSources: [hybrid] Abuse038_x264 | event_id=6 | 0.3-10.4; [hybrid] Abuse038_x264 | event_id=10 | 20.6-28.0"
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
    "actual": "The most relevant clip is in Abuse038_x264, around 0:00:00 - 0:00:10.\nSources: [hybrid] Abuse038_x264 | event_id=6 | 0.3-10.4; [hybrid] Abuse038_x264 | event_id=10 | 20.6-28.0",
    "expected": "non-empty string",
    "severity": "hard"
  },
  {
    "name": "citation_present",
    "passed": true,
    "actual": "The most relevant clip is in Abuse038_x264, around 0:00:00 - 0:00:10.\nSources: [hybrid] Abuse038_x264 | event_id=6 | 0.3-10.4; [hybrid] Abuse038_x264 | event_id=10 | 20.6-28.0",
    "expected": "final answer contains Sources:",
    "severity": "soft"
  },
  {
    "name": "grounding_coverage",
    "passed": true,
    "actual": {
      "summary": "The most relevant clip is in Abuse038_x264, around 0:00:00 - 0:00:10.",
      "style": "llm_summary",
      "confidence": 0.8,
      "citations": [
        {
          "source_type": "hybrid",
          "video_id": "Abuse038_x264",
          "event_id": 6,
          "start_time": 0.3,
          "end_time": 10.4,
          "record_level": "child"
        },
        {
          "source_type": "hybrid",
          "video_id": "Abuse038_x264",
          "event_id": 10,
          "start_time": 20.6,
          "end_time": 28.0,
          "record_level": "child"
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
      "user_need": "Retrieve video results that satisfy: Look for a person moving on the sidewalk",
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
      "expansion_terms": [],
      "base_rewritten_query": "Look for a person moving on the sidewalk",
      "scene_constraints": [],
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
      "match_verifier_node",
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
      "sql_rows_count": 2,
      "hybrid_rows_count": 0,
      "sql_error": null,
      "hybrid_error": "Collection expecting embedding with dimension of 1024, got 3072"
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
      "rerank_candidate_limit": 20,
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
    "actual": 2,
    "expected": 1,
    "severity": "hard"
  },
  {
    "name": "expected_keywords_any",
    "passed": false,
    "actual": "from 0.3s to 10.4s, several adults were talking on the side of the road. there were many vehicles on the road. later, two puppies appeared on the road. a black car hit the two puppies. from 20.6s to 28.0s, the cars on the road continue to move forward slowly.",
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
      "hybrid_rows_count": 0,
      "hybrid_error": "Collection expecting embedding with dimension of 1024, got 3072",
      "degraded": true
    },
    "expected": "hybrid rows > 0 or explicit degradation/error",
    "severity": "hard"
  },
  {
    "name": "hybrid_health_consistency",
    "passed": true,
    "actual": {
      "hybrid_summary": "",
      "hybrid_error": "Collection expecting embedding with dimension of 1024, got 3072",
      "degraded": true
    },
    "expected": "hybrid failure should be reflected by degraded flag or hybrid_error",
    "severity": "hard"
  }
]
```

- Last Iteration:

```json
{
  "elapsed_ms": 5454.23,
  "route_mode": "hybrid_search",
  "label": "semantic",
  "llm_final_output": "The most relevant clip is in Abuse038_x264, around 0:00:00 - 0:00:10.\nSources: [hybrid] Abuse038_x264 | event_id=6 | 0.3-10.4; [hybrid] Abuse038_x264 | event_id=10 | 20.6-28.0",
  "raw_final_answer": "Retrieval complete. Most relevant results:\n[1] event_id=6 | video=Abuse038_x264 | distance=0.0 | summary=From 0.3s to 10.4s, several adults were talking on the side of the road. There were many vehicles on the road. Later, two puppies appeared on the road. A black car hit the two puppies.\n[2] event_id=10 | video=Abuse038_x264 | distance=0.0 | summary=From 20.6s to 28.0s, the cars on the road continue to move forward slowly.",
  "rewritten_query": "Look for a person moving on the sidewalk",
  "original_user_query": "Look for a person moving on the sidewalk.",
  "self_query_result": {
    "rewritten_query": "Look for a person moving on the sidewalk",
    "user_need": "Retrieve video results that satisfy: Look for a person moving on the sidewalk",
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
    "expansion_terms": [],
    "base_rewritten_query": "Look for a person moving on the sidewalk",
    "scene_constraints": [],
    "original_user_query": "Look for a person moving on the sidewalk."
  },
  "summary_result": {
    "summary": "The most relevant clip is in Abuse038_x264, around 0:00:00 - 0:00:10.",
    "style": "llm_summary",
    "confidence": 0.8,
    "citations": [
      {
        "source_type": "hybrid",
        "video_id": "Abuse038_x264",
        "event_id": 6,
        "start_time": 0.3,
        "end_time": 10.4,
        "record_level": "child"
      },
      {
        "source_type": "hybrid",
        "video_id": "Abuse038_x264",
        "event_id": 10,
        "start_time": 20.6,
        "end_time": 28.0,
        "record_level": "child"
      }
    ]
  },
  "routing_metrics": {
    "execution_mode": "parallel_fusion",
    "label": "semantic",
    "query": "Look for a person moving on the sidewalk",
    "sql_rows_count": 2,
    "hybrid_rows_count": 0,
    "sql_error": null,
    "hybrid_error": "Collection expecting embedding with dimension of 1024, got 3072"
  },
  "search_config": {
    "candidate_limit": 80,
    "top_k_per_event": 20,
    "rerank_top_k": 5,
    "rerank_candidate_limit": 20,
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
    "match_verifier_node",
    "final_answer_node",
    "summary_node"
  ],
  "final_answer": "The most relevant clip is in Abuse038_x264, around 0:00:00 - 0:00:10.\nSources: [hybrid] Abuse038_x264 | event_id=6 | 0.3-10.4; [hybrid] Abuse038_x264 | event_id=10 | 20.6-28.0",
  "tool_error": null,
  "error": null,
  "current_node": "summary_node",
  "top5": [
    {
      "event_id": 6,
      "video_id": "Abuse038_x264",
      "event_text": "From 0.3s to 10.4s, several adults were talking on the side of the road. There were many vehicles on the road. Later, two puppies appeared on the road. A black car hit the two puppies.",
      "distance": 0.0
    },
    {
      "event_id": 10,
      "video_id": "Abuse038_x264",
      "event_text": "From 20.6s to 28.0s, the cars on the road continue to move forward slowly.",
      "distance": 0.0
    }
  ],
  "merged_count": 2,
  "sql_rows_count": 2,
  "hybrid_rows_count": 0,
  "degraded": true,
  "hybrid_summary": "",
  "sql_summary": "Deterministic SQL planner retrieval complete rows=2 stage=guided",
  "hybrid_error": "Collection expecting embedding with dimension of 1024, got 3072",
  "sql_error": null,
  "sql_debug": {
    "duration": 0.19009524601278827,
    "sql_summary": "Deterministic SQL planner retrieval complete rows=2 stage=guided",
    "hybrid_summary": "",
    "sql_error": null,
    "hybrid_error": "Collection expecting embedding with dimension of 1024, got 3072",
    "fusion_meta": {
      "label": "semantic",
      "degraded": true,
      "degraded_reason": "hybrid_failed",
      "method": "fallback_sql_only"
    },
    "rerank_meta": {
      "enabled": true,
      "model": "cross-encoder/ms-marco-MiniLM-L-6-v2",
      "input_count": 2,
      "candidate_count": 2,
      "output_count": 2
    },
    "parent_rows_count": 2,
    "result_mode": "child_only",
    "parent_context": [
      {
        "video_id": "Abuse038_x264",
        "child_hit_count": 2,
        "start_time": 0.3,
        "end_time": 28.0,
        "best_distance": 0.0,
        "best_hybrid_score": null,
        "track_ids": [],
        "object_types": [
          "car"
        ],
        "object_colors": [
          "black",
          "unknown"
        ],
        "scene_zones": [
          "road"
        ],
        "parent_rank": 1
      }
    ]
  }
}
```

## NEG_SQL_001

- Suite: `negative_regression`
- Priority: `P0`
- Dimensions: `functional, negative`
- Description: Absent object query should not return unrelated rows.
- Query: `Are there any cars in the database?`
- Status: `FAIL`
- Avg Latency: `8764.57 ms`
- P95 Latency: `8764.57 ms`
- Node Trace:

```json
[
  "self_query_node",
  "query_classification_node",
  "parallel_retrieval_fusion_node",
  "match_verifier_node",
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
  "sql_rows_count": 1,
  "hybrid_rows_count": 0,
  "sql_error": null,
  "hybrid_error": "Collection expecting embedding with dimension of 1024, got 3072"
}
```

- Search Config:

```json
{
  "candidate_limit": 80,
  "top_k_per_event": 20,
  "rerank_top_k": 5,
  "rerank_candidate_limit": 20,
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
  "user_need": "Retrieve video results that satisfy: Are there any cars in the database",
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
  "expansion_terms": [],
  "base_rewritten_query": "Are there any cars in the database",
  "scene_constraints": [],
  "original_user_query": "Are there any cars in the database?"
}
```

- Raw Final Answer:

```json
{
  "raw_final_answer": "Retrieval complete. Most relevant results:\n[1] event_id=10 | video=Abuse038_x264 | distance=0.0 | summary=From 20.6s to 28.0s, the cars on the road continue to move forward slowly."
}
```

- LLM Final Output:

```json
{
  "llm_final_output": "Yes. The relevant clip is in Abuse038_x264, around 0:00:21 - 0:00:28.\nSources: [hybrid] Abuse038_x264 | event_id=10 | 20.6-28.0"
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
    "actual": "Yes. The relevant clip is in Abuse038_x264, around 0:00:21 - 0:00:28.\nSources: [hybrid] Abuse038_x264 | event_id=10 | 20.6-28.0",
    "expected": "non-empty string",
    "severity": "hard"
  },
  {
    "name": "citation_present",
    "passed": true,
    "actual": "Yes. The relevant clip is in Abuse038_x264, around 0:00:21 - 0:00:28.\nSources: [hybrid] Abuse038_x264 | event_id=10 | 20.6-28.0",
    "expected": "final answer contains Sources:",
    "severity": "soft"
  },
  {
    "name": "grounding_coverage",
    "passed": true,
    "actual": {
      "summary": "Yes. The relevant clip is in Abuse038_x264, around 0:00:21 - 0:00:28.",
      "style": "llm_summary",
      "confidence": 0.8,
      "citations": [
        {
          "source_type": "hybrid",
          "video_id": "Abuse038_x264",
          "event_id": 10,
          "start_time": 20.6,
          "end_time": 28.0,
          "record_level": "child"
        }
      ]
    },
    "expected": "summary_result.citations is non-empty",
    "severity": "soft"
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
      "user_need": "Retrieve video results that satisfy: Are there any cars in the database",
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
      "expansion_terms": [],
      "base_rewritten_query": "Are there any cars in the database",
      "scene_constraints": [],
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
      "match_verifier_node",
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
      "sql_rows_count": 1,
      "hybrid_rows_count": 0,
      "sql_error": null,
      "hybrid_error": "Collection expecting embedding with dimension of 1024, got 3072"
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
      "rerank_candidate_limit": 20,
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
    "passed": false,
    "actual": 1,
    "expected": 0,
    "severity": "hard"
  }
]
```

- Last Iteration:

```json
{
  "elapsed_ms": 8764.57,
  "route_mode": "pure_sql",
  "label": "structured",
  "llm_final_output": "Yes. The relevant clip is in Abuse038_x264, around 0:00:21 - 0:00:28.\nSources: [hybrid] Abuse038_x264 | event_id=10 | 20.6-28.0",
  "raw_final_answer": "Retrieval complete. Most relevant results:\n[1] event_id=10 | video=Abuse038_x264 | distance=0.0 | summary=From 20.6s to 28.0s, the cars on the road continue to move forward slowly.",
  "rewritten_query": "Are there any cars in the database",
  "original_user_query": "Are there any cars in the database?",
  "self_query_result": {
    "rewritten_query": "Are there any cars in the database",
    "user_need": "Retrieve video results that satisfy: Are there any cars in the database",
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
    "expansion_terms": [],
    "base_rewritten_query": "Are there any cars in the database",
    "scene_constraints": [],
    "original_user_query": "Are there any cars in the database?"
  },
  "summary_result": {
    "summary": "Yes. The relevant clip is in Abuse038_x264, around 0:00:21 - 0:00:28.",
    "style": "llm_summary",
    "confidence": 0.8,
    "citations": [
      {
        "source_type": "hybrid",
        "video_id": "Abuse038_x264",
        "event_id": 10,
        "start_time": 20.6,
        "end_time": 28.0,
        "record_level": "child"
      }
    ]
  },
  "routing_metrics": {
    "execution_mode": "parallel_fusion",
    "label": "structured",
    "query": "Are there any cars in the database",
    "sql_rows_count": 1,
    "hybrid_rows_count": 0,
    "sql_error": null,
    "hybrid_error": "Collection expecting embedding with dimension of 1024, got 3072"
  },
  "search_config": {
    "candidate_limit": 80,
    "top_k_per_event": 20,
    "rerank_top_k": 5,
    "rerank_candidate_limit": 20,
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
    "match_verifier_node",
    "final_answer_node",
    "summary_node"
  ],
  "final_answer": "Yes. The relevant clip is in Abuse038_x264, around 0:00:21 - 0:00:28.\nSources: [hybrid] Abuse038_x264 | event_id=10 | 20.6-28.0",
  "tool_error": null,
  "error": null,
  "current_node": "summary_node",
  "top5": [
    {
      "event_id": 10,
      "video_id": "Abuse038_x264",
      "event_text": "From 20.6s to 28.0s, the cars on the road continue to move forward slowly.",
      "distance": 0.0
    }
  ],
  "merged_count": 1,
  "sql_rows_count": 1,
  "hybrid_rows_count": 0,
  "degraded": true,
  "hybrid_summary": "",
  "sql_summary": "Deterministic SQL planner retrieval complete rows=1 stage=guided",
  "hybrid_error": "Collection expecting embedding with dimension of 1024, got 3072",
  "sql_error": null,
  "sql_debug": {
    "duration": 0.19158820001757704,
    "sql_summary": "Deterministic SQL planner retrieval complete rows=1 stage=guided",
    "hybrid_summary": "",
    "sql_error": null,
    "hybrid_error": "Collection expecting embedding with dimension of 1024, got 3072",
    "fusion_meta": {
      "label": "structured",
      "degraded": true,
      "degraded_reason": "hybrid_failed",
      "method": "fallback_sql_only"
    },
    "rerank_meta": {
      "enabled": true,
      "model": "cross-encoder/ms-marco-MiniLM-L-6-v2",
      "input_count": 1,
      "candidate_count": 1,
      "output_count": 1
    },
    "parent_rows_count": 1,
    "result_mode": "child_only",
    "parent_context": [
      {
        "video_id": "Abuse038_x264",
        "child_hit_count": 1,
        "start_time": 20.6,
        "end_time": 28.0,
        "best_distance": 0.0,
        "best_hybrid_score": null,
        "track_ids": [],
        "object_types": [
          "car"
        ],
        "object_colors": [
          "unknown"
        ],
        "scene_zones": [
          "road"
        ],
        "parent_rank": 1
      }
    ]
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
- Avg Latency: `1980.05 ms`
- P95 Latency: `1980.05 ms`
- Node Trace:

```json
[
  "self_query_node",
  "query_classification_node",
  "parallel_retrieval_fusion_node",
  "match_verifier_node",
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
  "sql_rows_count": 10,
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
  "rerank_candidate_limit": 20,
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
  "user_need": "Find relevant retrieval results from the user's request.",
  "intent_label": "mixed",
  "retrieval_focus": "mixed",
  "key_constraints": [],
  "ambiguities": [],
  "reasoning_summary": "Fallback to the original query because self-query preprocessing was unavailable.",
  "confidence": 0.35,
  "expansion_terms": [],
  "scene_constraints": [],
  "base_rewritten_query": "",
  "original_user_query": ""
}
```

- Raw Final Answer:

```json
{
  "raw_final_answer": "Retrieval complete. Most relevant results:\n[1] event_id=10 | video=Abuse038_x264 | distance=0.0 | summary=From 20.6s to 28.0s, the cars on the road continue to move forward slowly.\n[2] event_id=6 | video=Abuse038_x264 | distance=0.0 | summary=From 0.3s to 10.4s, several adults were talking on the side of the road. There were many vehicles on the road. Later, two puppies appeared on the road. A black car hit the two puppies.\n[3] event_id=9 | video=Abuse038_x264 | distance=0.0 | summary=From 14.5s to 20.6s, in the middle of the road on one side, a car with lights on stopped driving, and the lights shone on the puppy on the road in front.\n[4] event_id=2 | video=Abuse037_x264 | distance=0.0 | summary=From 8.4s to 25.3s, the white car was driving in the middle of the road, and several dogs ran onto the road.\n[5] event_id=1 | video=Abuse037_x264 | distance=0.0 | summary=From 1.2s to 8.2s, a white car with double flashes slowly appeared on the screen, crushing the black dog walking in the middle of the road."
}
```

- LLM Final Output:

```json
{
  "llm_final_output": "The most relevant clip is in Abuse038_x264, around 0:00:21 - 0:00:28.\nSources: [sql] Abuse038_x264 | event_id=10 | 20.6-28.0; [sql] Abuse038_x264 | event_id=6 | 0.3-10.4; [sql] Abuse038_x264 | event_id=9 | 14.5-20.6"
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
    "actual": "The most relevant clip is in Abuse038_x264, around 0:00:21 - 0:00:28.\nSources: [sql] Abuse038_x264 | event_id=10 | 20.6-28.0; [sql] Abuse038_x264 | event_id=6 | 0.3-10.4; [sql] Abuse038_x264 | event_id=9 | 14.5-20.6",
    "expected": "non-empty string",
    "severity": "hard"
  },
  {
    "name": "citation_present",
    "passed": true,
    "actual": "The most relevant clip is in Abuse038_x264, around 0:00:21 - 0:00:28.\nSources: [sql] Abuse038_x264 | event_id=10 | 20.6-28.0; [sql] Abuse038_x264 | event_id=6 | 0.3-10.4; [sql] Abuse038_x264 | event_id=9 | 14.5-20.6",
    "expected": "final answer contains Sources:",
    "severity": "soft"
  },
  {
    "name": "grounding_coverage",
    "passed": true,
    "actual": {
      "summary": "The most relevant clip is in Abuse038_x264, around 0:00:21 - 0:00:28.",
      "style": "llm_summary",
      "confidence": 0.8,
      "citations": [
        {
          "source_type": "sql",
          "video_id": "Abuse038_x264",
          "event_id": 10,
          "start_time": 20.6,
          "end_time": 28.0,
          "record_level": "child"
        },
        {
          "source_type": "sql",
          "video_id": "Abuse038_x264",
          "event_id": 6,
          "start_time": 0.3,
          "end_time": 10.4,
          "record_level": "child"
        },
        {
          "source_type": "sql",
          "video_id": "Abuse038_x264",
          "event_id": 9,
          "start_time": 14.5,
          "end_time": 20.6,
          "record_level": "child"
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
      "match_verifier_node",
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
      "sql_rows_count": 10,
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
      "rerank_candidate_limit": 20,
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
  "elapsed_ms": 1980.05,
  "route_mode": "hybrid_search",
  "label": "mixed",
  "llm_final_output": "The most relevant clip is in Abuse038_x264, around 0:00:21 - 0:00:28.\nSources: [sql] Abuse038_x264 | event_id=10 | 20.6-28.0; [sql] Abuse038_x264 | event_id=6 | 0.3-10.4; [sql] Abuse038_x264 | event_id=9 | 14.5-20.6",
  "raw_final_answer": "Retrieval complete. Most relevant results:\n[1] event_id=10 | video=Abuse038_x264 | distance=0.0 | summary=From 20.6s to 28.0s, the cars on the road continue to move forward slowly.\n[2] event_id=6 | video=Abuse038_x264 | distance=0.0 | summary=From 0.3s to 10.4s, several adults were talking on the side of the road. There were many vehicles on the road. Later, two puppies appeared on the road. A black car hit the two puppies.\n[3] event_id=9 | video=Abuse038_x264 | distance=0.0 | summary=From 14.5s to 20.6s, in the middle of the road on one side, a car with lights on stopped driving, and the lights shone on the puppy on the road in front.\n[4] event_id=2 | video=Abuse037_x264 | distance=0.0 | summary=From 8.4s to 25.3s, the white car was driving in the middle of the road, and several dogs ran onto the road.\n[5] event_id=1 | video=Abuse037_x264 | distance=0.0 | summary=From 1.2s to 8.2s, a white car with double flashes slowly appeared on the screen, crushing the black dog walking in the middle of the road.",
  "rewritten_query": "",
  "original_user_query": "",
  "self_query_result": {
    "rewritten_query": "",
    "user_need": "Find relevant retrieval results from the user's request.",
    "intent_label": "mixed",
    "retrieval_focus": "mixed",
    "key_constraints": [],
    "ambiguities": [],
    "reasoning_summary": "Fallback to the original query because self-query preprocessing was unavailable.",
    "confidence": 0.35,
    "expansion_terms": [],
    "scene_constraints": [],
    "base_rewritten_query": "",
    "original_user_query": ""
  },
  "summary_result": {
    "summary": "The most relevant clip is in Abuse038_x264, around 0:00:21 - 0:00:28.",
    "style": "llm_summary",
    "confidence": 0.8,
    "citations": [
      {
        "source_type": "sql",
        "video_id": "Abuse038_x264",
        "event_id": 10,
        "start_time": 20.6,
        "end_time": 28.0,
        "record_level": "child"
      },
      {
        "source_type": "sql",
        "video_id": "Abuse038_x264",
        "event_id": 6,
        "start_time": 0.3,
        "end_time": 10.4,
        "record_level": "child"
      },
      {
        "source_type": "sql",
        "video_id": "Abuse038_x264",
        "event_id": 9,
        "start_time": 14.5,
        "end_time": 20.6,
        "record_level": "child"
      }
    ]
  },
  "routing_metrics": {
    "execution_mode": "parallel_fusion",
    "label": "mixed",
    "query": "",
    "sql_rows_count": 10,
    "hybrid_rows_count": 0,
    "sql_error": null,
    "hybrid_error": null
  },
  "search_config": {
    "candidate_limit": 80,
    "top_k_per_event": 20,
    "rerank_top_k": 5,
    "rerank_candidate_limit": 20,
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
    "match_verifier_node",
    "final_answer_node",
    "summary_node"
  ],
  "final_answer": "The most relevant clip is in Abuse038_x264, around 0:00:21 - 0:00:28.\nSources: [sql] Abuse038_x264 | event_id=10 | 20.6-28.0; [sql] Abuse038_x264 | event_id=6 | 0.3-10.4; [sql] Abuse038_x264 | event_id=9 | 14.5-20.6",
  "tool_error": null,
  "error": null,
  "current_node": "summary_node",
  "top5": [
    {
      "event_id": 10,
      "video_id": "Abuse038_x264",
      "event_text": "From 20.6s to 28.0s, the cars on the road continue to move forward slowly.",
      "distance": 0.0
    },
    {
      "event_id": 6,
      "video_id": "Abuse038_x264",
      "event_text": "From 0.3s to 10.4s, several adults were talking on the side of the road. There were many vehicles on the road. Later, two puppies appeared on the road. A black car hit the two puppies.",
      "distance": 0.0
    },
    {
      "event_id": 9,
      "video_id": "Abuse038_x264",
      "event_text": "From 14.5s to 20.6s, in the middle of the road on one side, a car with lights on stopped driving, and the lights shone on the puppy on the road in front.",
      "distance": 0.0
    },
    {
      "event_id": 2,
      "video_id": "Abuse037_x264",
      "event_text": "From 8.4s to 25.3s, the white car was driving in the middle of the road, and several dogs ran onto the road.",
      "distance": 0.0
    },
    {
      "event_id": 1,
      "video_id": "Abuse037_x264",
      "event_text": "From 1.2s to 8.2s, a white car with double flashes slowly appeared on the screen, crushing the black dog walking in the middle of the road.",
      "distance": 0.0
    }
  ],
  "merged_count": 5,
  "sql_rows_count": 10,
  "hybrid_rows_count": 0,
  "degraded": false,
  "hybrid_summary": "Hybrid retrieval skipped: empty query",
  "sql_summary": "Deterministic SQL planner retrieval complete rows=10 stage=guided",
  "hybrid_error": null,
  "sql_error": null,
  "sql_debug": {
    "duration": 0.004611356998793781,
    "sql_summary": "Deterministic SQL planner retrieval complete rows=10 stage=guided",
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
      "sql_count": 10,
      "hybrid_count": 0,
      "fused_count": 10,
      "overlap_count": 0,
      "method": "weighted_rrf",
      "signal_bias": {
        "applied": true,
        "metadata_hits": 0,
        "relation_cues": 0,
        "multi_step_cues": 0,
        "sql_bias": 0.0,
        "hybrid_bias": 0.0,
        "base_sql": 0.5,
        "base_hybrid": 0.5
      },
      "degraded": false,
      "signals": {
        "metadata_hits": [],
        "relation_cues": [],
        "multi_step_cues": [],
        "existence_cues": [],
        "structured": 1,
        "semantic": 1
      }
    },
    "rerank_meta": {
      "enabled": true,
      "model": "cross-encoder/ms-marco-MiniLM-L-6-v2",
      "input_count": 10,
      "candidate_count": 10,
      "output_count": 10
    },
    "parent_rows_count": 5,
    "result_mode": "child_only",
    "parent_context": [
      {
        "video_id": "Abuse038_x264",
        "child_hit_count": 5,
        "start_time": 0.3,
        "end_time": 28.0,
        "best_distance": 0.0,
        "best_hybrid_score": null,
        "track_ids": [],
        "object_types": [
          "car",
          "dog"
        ],
        "object_colors": [
          "unknown",
          "black"
        ],
        "scene_zones": [
          "road"
        ],
        "parent_rank": 1
      },
      {
        "video_id": "Abuse037_x264",
        "child_hit_count": 5,
        "start_time": 1.2,
        "end_time": 59.1,
        "best_distance": 0.0,
        "best_hybrid_score": null,
        "track_ids": [],
        "object_types": [
          "car",
          "dog"
        ],
        "object_colors": [
          "white",
          "black",
          "gray"
        ],
        "scene_zones": [
          "road",
          "unknown"
        ],
        "parent_rank": 2
      }
    ]
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
- Avg Latency: `6528.77 ms`
- P95 Latency: `6528.77 ms`
- Node Trace:

```json
[
  "self_query_node",
  "query_classification_node",
  "parallel_retrieval_fusion_node",
  "match_verifier_node",
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
  "sql_rows_count": 1,
  "hybrid_rows_count": 0,
  "sql_error": null,
  "hybrid_error": "Collection expecting embedding with dimension of 1024, got 3072"
}
```

- Search Config:

```json
{
  "candidate_limit": 80,
  "top_k_per_event": 20,
  "rerank_top_k": 5,
  "rerank_candidate_limit": 20,
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
  "user_need": "Retrieve video results that satisfy: person",
  "intent_label": "structured",
  "retrieval_focus": "structured",
  "key_constraints": [
    "person"
  ],
  "ambiguities": [],
  "reasoning_summary": "Fast-path preprocessing kept the original meaning and only normalized surface noise.",
  "confidence": 0.8,
  "expansion_terms": [],
  "base_rewritten_query": "person",
  "scene_constraints": [],
  "original_user_query": "person"
}
```

- Raw Final Answer:

```json
{
  "raw_final_answer": "Retrieval complete. Most relevant results:\n[1] event_id=6 | video=Abuse038_x264 | distance=0.0 | summary=From 0.3s to 10.4s, several adults were talking on the side of the road. There were many vehicles on the road. Later, two puppies appeared on the road. A black car hit the two puppies."
}
```

- LLM Final Output:

```json
{
  "llm_final_output": "The most relevant clip is in Abuse038_x264, around 0:00:00 - 0:00:10.\nSources: [hybrid] Abuse038_x264 | event_id=6 | 0.3-10.4"
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
    "actual": "The most relevant clip is in Abuse038_x264, around 0:00:00 - 0:00:10.\nSources: [hybrid] Abuse038_x264 | event_id=6 | 0.3-10.4",
    "expected": "non-empty string",
    "severity": "hard"
  },
  {
    "name": "citation_present",
    "passed": true,
    "actual": "The most relevant clip is in Abuse038_x264, around 0:00:00 - 0:00:10.\nSources: [hybrid] Abuse038_x264 | event_id=6 | 0.3-10.4",
    "expected": "final answer contains Sources:",
    "severity": "soft"
  },
  {
    "name": "grounding_coverage",
    "passed": true,
    "actual": {
      "summary": "The most relevant clip is in Abuse038_x264, around 0:00:00 - 0:00:10.",
      "style": "llm_summary",
      "confidence": 0.8,
      "citations": [
        {
          "source_type": "hybrid",
          "video_id": "Abuse038_x264",
          "event_id": 6,
          "start_time": 0.3,
          "end_time": 10.4,
          "record_level": "child"
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
      "user_need": "Retrieve video results that satisfy: person",
      "intent_label": "structured",
      "retrieval_focus": "structured",
      "key_constraints": [
        "person"
      ],
      "ambiguities": [],
      "reasoning_summary": "Fast-path preprocessing kept the original meaning and only normalized surface noise.",
      "confidence": 0.8,
      "expansion_terms": [],
      "base_rewritten_query": "person",
      "scene_constraints": [],
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
      "match_verifier_node",
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
      "sql_rows_count": 1,
      "hybrid_rows_count": 0,
      "sql_error": null,
      "hybrid_error": "Collection expecting embedding with dimension of 1024, got 3072"
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
      "rerank_candidate_limit": 20,
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
    "actual": 1,
    "expected": 1,
    "severity": "hard"
  },
  {
    "name": "min_sql_rows",
    "passed": true,
    "actual": 1,
    "expected": 1,
    "severity": "hard"
  }
]
```

- Last Iteration:

```json
{
  "elapsed_ms": 6528.77,
  "route_mode": "pure_sql",
  "label": "structured",
  "llm_final_output": "The most relevant clip is in Abuse038_x264, around 0:00:00 - 0:00:10.\nSources: [hybrid] Abuse038_x264 | event_id=6 | 0.3-10.4",
  "raw_final_answer": "Retrieval complete. Most relevant results:\n[1] event_id=6 | video=Abuse038_x264 | distance=0.0 | summary=From 0.3s to 10.4s, several adults were talking on the side of the road. There were many vehicles on the road. Later, two puppies appeared on the road. A black car hit the two puppies.",
  "rewritten_query": "person",
  "original_user_query": "person",
  "self_query_result": {
    "rewritten_query": "person",
    "user_need": "Retrieve video results that satisfy: person",
    "intent_label": "structured",
    "retrieval_focus": "structured",
    "key_constraints": [
      "person"
    ],
    "ambiguities": [],
    "reasoning_summary": "Fast-path preprocessing kept the original meaning and only normalized surface noise.",
    "confidence": 0.8,
    "expansion_terms": [],
    "base_rewritten_query": "person",
    "scene_constraints": [],
    "original_user_query": "person"
  },
  "summary_result": {
    "summary": "The most relevant clip is in Abuse038_x264, around 0:00:00 - 0:00:10.",
    "style": "llm_summary",
    "confidence": 0.8,
    "citations": [
      {
        "source_type": "hybrid",
        "video_id": "Abuse038_x264",
        "event_id": 6,
        "start_time": 0.3,
        "end_time": 10.4,
        "record_level": "child"
      }
    ]
  },
  "routing_metrics": {
    "execution_mode": "parallel_fusion",
    "label": "structured",
    "query": "person",
    "sql_rows_count": 1,
    "hybrid_rows_count": 0,
    "sql_error": null,
    "hybrid_error": "Collection expecting embedding with dimension of 1024, got 3072"
  },
  "search_config": {
    "candidate_limit": 80,
    "top_k_per_event": 20,
    "rerank_top_k": 5,
    "rerank_candidate_limit": 20,
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
    "match_verifier_node",
    "final_answer_node",
    "summary_node"
  ],
  "final_answer": "The most relevant clip is in Abuse038_x264, around 0:00:00 - 0:00:10.\nSources: [hybrid] Abuse038_x264 | event_id=6 | 0.3-10.4",
  "tool_error": null,
  "error": null,
  "current_node": "summary_node",
  "top5": [
    {
      "event_id": 6,
      "video_id": "Abuse038_x264",
      "event_text": "From 0.3s to 10.4s, several adults were talking on the side of the road. There were many vehicles on the road. Later, two puppies appeared on the road. A black car hit the two puppies.",
      "distance": 0.0
    }
  ],
  "merged_count": 1,
  "sql_rows_count": 1,
  "hybrid_rows_count": 0,
  "degraded": true,
  "hybrid_summary": "",
  "sql_summary": "Deterministic SQL planner retrieval complete rows=1 stage=guided",
  "hybrid_error": "Collection expecting embedding with dimension of 1024, got 3072",
  "sql_error": null,
  "sql_debug": {
    "duration": 0.19651093299034983,
    "sql_summary": "Deterministic SQL planner retrieval complete rows=1 stage=guided",
    "hybrid_summary": "",
    "sql_error": null,
    "hybrid_error": "Collection expecting embedding with dimension of 1024, got 3072",
    "fusion_meta": {
      "label": "structured",
      "degraded": true,
      "degraded_reason": "hybrid_failed",
      "method": "fallback_sql_only"
    },
    "rerank_meta": {
      "enabled": true,
      "model": "cross-encoder/ms-marco-MiniLM-L-6-v2",
      "input_count": 1,
      "candidate_count": 1,
      "output_count": 1
    },
    "parent_rows_count": 1,
    "result_mode": "child_only",
    "parent_context": [
      {
        "video_id": "Abuse038_x264",
        "child_hit_count": 1,
        "start_time": 0.3,
        "end_time": 10.4,
        "best_distance": 0.0,
        "best_hybrid_score": null,
        "track_ids": [],
        "object_types": [
          "car"
        ],
        "object_colors": [
          "black"
        ],
        "scene_zones": [
          "road"
        ],
        "parent_rank": 1
      }
    ]
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
- Avg Latency: `7123.62 ms`
- P95 Latency: `7123.62 ms`
- Node Trace:

```json
[
  "self_query_node",
  "query_classification_node",
  "parallel_retrieval_fusion_node",
  "match_verifier_node",
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
  "sql_rows_count": 5,
  "hybrid_rows_count": 0,
  "sql_error": null,
  "hybrid_error": "Collection expecting embedding with dimension of 1024, got 3072"
}
```

- Search Config:

```json
{
  "candidate_limit": 80,
  "top_k_per_event": 20,
  "rerank_top_k": 5,
  "rerank_candidate_limit": 20,
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
  "user_need": "Retrieve video results that satisfy: Find A PERSON near the LEFT BLEACHERS",
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
  "expansion_terms": [],
  "base_rewritten_query": "Find A PERSON near the LEFT BLEACHERS",
  "scene_constraints": [],
  "original_user_query": "!!! Find A PERSON near the LEFT BLEACHERS ???"
}
```

- Raw Final Answer:

```json
{
  "raw_final_answer": "Retrieval complete. Most relevant results:\n[1] event_id=3 | video=Abuse037_x264 | distance=0.0 | summary=From 25.3s to 48.5s, there was a black dog left on the road. It walked to the middle of the road next to the dog that had just been crushed.\n[2] event_id=4 | video=Abuse037_x264 | distance=0.0 | summary=From 48.5s to 59.1s, the black dog walked away and left the middle of the road.\n[3] event_id=5 | video=Abuse037_x264 | distance=0.0 | summary=From 40.4s to 47.6s, the gray dog pulled out the tail of the dog that had just been run over by the car, then stayed for a few minutes and left.\n[4] event_id=7 | video=Abuse038_x264 | distance=0.0 | summary=From 11.5s to 17.2s, two puppies rolled on the road, then one of the dogs left the road and the other stopped in the middle of the road.\n[5] event_id=6 | video=Abuse038_x264 | distance=0.0 | summary=From 0.3s to 10.4s, several adults were talking on the side of the road. There were many vehicles on the road. Later, two puppies appeared on the road. A black car hit the two puppies."
}
```

- LLM Final Output:

```json
{
  "llm_final_output": "Yes. The relevant clip is in Abuse038_x264, around 0:00:00 - 0:00:10.\nSources: [hybrid] Abuse037_x264 | event_id=3 | 25.3-48.5; [hybrid] Abuse037_x264 | event_id=4 | 48.5-59.1; [hybrid] Abuse037_x264 | event_id=5 | 40.4-47.6"
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
    "actual": "Yes. The relevant clip is in Abuse038_x264, around 0:00:00 - 0:00:10.\nSources: [hybrid] Abuse037_x264 | event_id=3 | 25.3-48.5; [hybrid] Abuse037_x264 | event_id=4 | 48.5-59.1; [hybrid] Abuse037_x264 | event_id=5 | 40.4-47.6",
    "expected": "non-empty string",
    "severity": "hard"
  },
  {
    "name": "citation_present",
    "passed": true,
    "actual": "Yes. The relevant clip is in Abuse038_x264, around 0:00:00 - 0:00:10.\nSources: [hybrid] Abuse037_x264 | event_id=3 | 25.3-48.5; [hybrid] Abuse037_x264 | event_id=4 | 48.5-59.1; [hybrid] Abuse037_x264 | event_id=5 | 40.4-47.6",
    "expected": "final answer contains Sources:",
    "severity": "soft"
  },
  {
    "name": "grounding_coverage",
    "passed": true,
    "actual": {
      "summary": "Yes. The relevant clip is in Abuse038_x264, around 0:00:00 - 0:00:10.",
      "style": "llm_summary",
      "confidence": 0.8,
      "citations": [
        {
          "source_type": "hybrid",
          "video_id": "Abuse037_x264",
          "event_id": 3,
          "start_time": 25.3,
          "end_time": 48.5,
          "record_level": "child"
        },
        {
          "source_type": "hybrid",
          "video_id": "Abuse037_x264",
          "event_id": 4,
          "start_time": 48.5,
          "end_time": 59.1,
          "record_level": "child"
        },
        {
          "source_type": "hybrid",
          "video_id": "Abuse037_x264",
          "event_id": 5,
          "start_time": 40.4,
          "end_time": 47.6,
          "record_level": "child"
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
      "user_need": "Retrieve video results that satisfy: Find A PERSON near the LEFT BLEACHERS",
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
      "expansion_terms": [],
      "base_rewritten_query": "Find A PERSON near the LEFT BLEACHERS",
      "scene_constraints": [],
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
      "match_verifier_node",
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
      "sql_rows_count": 5,
      "hybrid_rows_count": 0,
      "sql_error": null,
      "hybrid_error": "Collection expecting embedding with dimension of 1024, got 3072"
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
      "rerank_candidate_limit": 20,
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
    "actual": 5,
    "expected": 1,
    "severity": "hard"
  },
  {
    "name": "semantic_backend_effective",
    "passed": true,
    "actual": {
      "hybrid_rows_count": 0,
      "hybrid_error": "Collection expecting embedding with dimension of 1024, got 3072",
      "degraded": true
    },
    "expected": "hybrid rows > 0 or explicit degradation/error",
    "severity": "hard"
  },
  {
    "name": "hybrid_health_consistency",
    "passed": true,
    "actual": {
      "hybrid_summary": "",
      "hybrid_error": "Collection expecting embedding with dimension of 1024, got 3072",
      "degraded": true
    },
    "expected": "hybrid failure should be reflected by degraded flag or hybrid_error",
    "severity": "hard"
  }
]
```

- Last Iteration:

```json
{
  "elapsed_ms": 7123.62,
  "route_mode": "hybrid_search",
  "label": "semantic",
  "llm_final_output": "Yes. The relevant clip is in Abuse038_x264, around 0:00:00 - 0:00:10.\nSources: [hybrid] Abuse037_x264 | event_id=3 | 25.3-48.5; [hybrid] Abuse037_x264 | event_id=4 | 48.5-59.1; [hybrid] Abuse037_x264 | event_id=5 | 40.4-47.6",
  "raw_final_answer": "Retrieval complete. Most relevant results:\n[1] event_id=3 | video=Abuse037_x264 | distance=0.0 | summary=From 25.3s to 48.5s, there was a black dog left on the road. It walked to the middle of the road next to the dog that had just been crushed.\n[2] event_id=4 | video=Abuse037_x264 | distance=0.0 | summary=From 48.5s to 59.1s, the black dog walked away and left the middle of the road.\n[3] event_id=5 | video=Abuse037_x264 | distance=0.0 | summary=From 40.4s to 47.6s, the gray dog pulled out the tail of the dog that had just been run over by the car, then stayed for a few minutes and left.\n[4] event_id=7 | video=Abuse038_x264 | distance=0.0 | summary=From 11.5s to 17.2s, two puppies rolled on the road, then one of the dogs left the road and the other stopped in the middle of the road.\n[5] event_id=6 | video=Abuse038_x264 | distance=0.0 | summary=From 0.3s to 10.4s, several adults were talking on the side of the road. There were many vehicles on the road. Later, two puppies appeared on the road. A black car hit the two puppies.",
  "rewritten_query": "Find A PERSON near the LEFT BLEACHERS",
  "original_user_query": "!!! Find A PERSON near the LEFT BLEACHERS ???",
  "self_query_result": {
    "rewritten_query": "Find A PERSON near the LEFT BLEACHERS",
    "user_need": "Retrieve video results that satisfy: Find A PERSON near the LEFT BLEACHERS",
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
    "expansion_terms": [],
    "base_rewritten_query": "Find A PERSON near the LEFT BLEACHERS",
    "scene_constraints": [],
    "original_user_query": "!!! Find A PERSON near the LEFT BLEACHERS ???"
  },
  "summary_result": {
    "summary": "Yes. The relevant clip is in Abuse038_x264, around 0:00:00 - 0:00:10.",
    "style": "llm_summary",
    "confidence": 0.8,
    "citations": [
      {
        "source_type": "hybrid",
        "video_id": "Abuse037_x264",
        "event_id": 3,
        "start_time": 25.3,
        "end_time": 48.5,
        "record_level": "child"
      },
      {
        "source_type": "hybrid",
        "video_id": "Abuse037_x264",
        "event_id": 4,
        "start_time": 48.5,
        "end_time": 59.1,
        "record_level": "child"
      },
      {
        "source_type": "hybrid",
        "video_id": "Abuse037_x264",
        "event_id": 5,
        "start_time": 40.4,
        "end_time": 47.6,
        "record_level": "child"
      }
    ]
  },
  "routing_metrics": {
    "execution_mode": "parallel_fusion",
    "label": "semantic",
    "query": "Find A PERSON near the LEFT BLEACHERS",
    "sql_rows_count": 5,
    "hybrid_rows_count": 0,
    "sql_error": null,
    "hybrid_error": "Collection expecting embedding with dimension of 1024, got 3072"
  },
  "search_config": {
    "candidate_limit": 80,
    "top_k_per_event": 20,
    "rerank_top_k": 5,
    "rerank_candidate_limit": 20,
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
    "match_verifier_node",
    "final_answer_node",
    "summary_node"
  ],
  "final_answer": "Yes. The relevant clip is in Abuse038_x264, around 0:00:00 - 0:00:10.\nSources: [hybrid] Abuse037_x264 | event_id=3 | 25.3-48.5; [hybrid] Abuse037_x264 | event_id=4 | 48.5-59.1; [hybrid] Abuse037_x264 | event_id=5 | 40.4-47.6",
  "tool_error": null,
  "error": null,
  "current_node": "summary_node",
  "top5": [
    {
      "event_id": 3,
      "video_id": "Abuse037_x264",
      "event_text": "From 25.3s to 48.5s, there was a black dog left on the road. It walked to the middle of the road next to the dog that had just been crushed.",
      "distance": 0.0
    },
    {
      "event_id": 4,
      "video_id": "Abuse037_x264",
      "event_text": "From 48.5s to 59.1s, the black dog walked away and left the middle of the road.",
      "distance": 0.0
    },
    {
      "event_id": 5,
      "video_id": "Abuse037_x264",
      "event_text": "From 40.4s to 47.6s, the gray dog pulled out the tail of the dog that had just been run over by the car, then stayed for a few minutes and left.",
      "distance": 0.0
    },
    {
      "event_id": 7,
      "video_id": "Abuse038_x264",
      "event_text": "From 11.5s to 17.2s, two puppies rolled on the road, then one of the dogs left the road and the other stopped in the middle of the road.",
      "distance": 0.0
    },
    {
      "event_id": 6,
      "video_id": "Abuse038_x264",
      "event_text": "From 0.3s to 10.4s, several adults were talking on the side of the road. There were many vehicles on the road. Later, two puppies appeared on the road. A black car hit the two puppies.",
      "distance": 0.0
    }
  ],
  "merged_count": 5,
  "sql_rows_count": 5,
  "hybrid_rows_count": 0,
  "degraded": true,
  "hybrid_summary": "",
  "sql_summary": "Deterministic SQL planner retrieval complete rows=5 stage=guided",
  "hybrid_error": "Collection expecting embedding with dimension of 1024, got 3072",
  "sql_error": null,
  "sql_debug": {
    "duration": 0.18492197600426152,
    "sql_summary": "Deterministic SQL planner retrieval complete rows=5 stage=guided",
    "hybrid_summary": "",
    "sql_error": null,
    "hybrid_error": "Collection expecting embedding with dimension of 1024, got 3072",
    "fusion_meta": {
      "label": "semantic",
      "degraded": true,
      "degraded_reason": "hybrid_failed",
      "method": "fallback_sql_only"
    },
    "rerank_meta": {
      "enabled": true,
      "model": "cross-encoder/ms-marco-MiniLM-L-6-v2",
      "input_count": 5,
      "candidate_count": 5,
      "output_count": 5
    },
    "parent_rows_count": 5,
    "result_mode": "child_only",
    "parent_context": [
      {
        "video_id": "Abuse037_x264",
        "child_hit_count": 3,
        "start_time": 25.3,
        "end_time": 59.1,
        "best_distance": 0.0,
        "best_hybrid_score": null,
        "track_ids": [],
        "object_types": [
          "dog",
          "car"
        ],
        "object_colors": [
          "black",
          "gray"
        ],
        "scene_zones": [
          "road",
          "unknown"
        ],
        "parent_rank": 1
      },
      {
        "video_id": "Abuse038_x264",
        "child_hit_count": 2,
        "start_time": 0.3,
        "end_time": 17.2,
        "best_distance": 0.0,
        "best_hybrid_score": null,
        "track_ids": [],
        "object_types": [
          "dog",
          "car"
        ],
        "object_colors": [
          "unknown",
          "black"
        ],
        "scene_zones": [
          "road"
        ],
        "parent_rank": 2
      }
    ]
  }
}
```

## FNC_SQL_003

- Suite: `filter_regression`
- Priority: `P1`
- Dimensions: `functional, filtering`
- Description: Parking-area query should surface parking-related evidence in top results.
- Query: `Show me a person in the parking area.`
- Status: `FAIL`
- Avg Latency: `3925.07 ms`
- P95 Latency: `3925.07 ms`
- Node Trace:

```json
[
  "self_query_node",
  "query_classification_node",
  "parallel_retrieval_fusion_node",
  "match_verifier_node",
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
  "sql_rows_count": 1,
  "hybrid_rows_count": 0,
  "sql_error": null,
  "hybrid_error": "Collection expecting embedding with dimension of 1024, got 3072"
}
```

- Search Config:

```json
{
  "candidate_limit": 80,
  "top_k_per_event": 20,
  "rerank_top_k": 5,
  "rerank_candidate_limit": 20,
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
  "user_need": "Retrieve video results that satisfy: Show me a person in the parking area",
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
  "expansion_terms": [],
  "base_rewritten_query": "Show me a person in the parking area",
  "scene_constraints": [],
  "original_user_query": "Show me a person in the parking area."
}
```

- Raw Final Answer:

```json
{
  "raw_final_answer": "Retrieval complete. Most relevant results:\n[1] event_id=6 | video=Abuse038_x264 | distance=0.0 | summary=From 0.3s to 10.4s, several adults were talking on the side of the road. There were many vehicles on the road. Later, two puppies appeared on the road. A black car hit the two puppies."
}
```

- LLM Final Output:

```json
{
  "llm_final_output": "The most relevant clip is in Abuse038_x264, around 0:00:00 - 0:00:10.\nSources: [hybrid] Abuse038_x264 | event_id=6 | 0.3-10.4"
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
    "actual": "The most relevant clip is in Abuse038_x264, around 0:00:00 - 0:00:10.\nSources: [hybrid] Abuse038_x264 | event_id=6 | 0.3-10.4",
    "expected": "non-empty string",
    "severity": "hard"
  },
  {
    "name": "citation_present",
    "passed": true,
    "actual": "The most relevant clip is in Abuse038_x264, around 0:00:00 - 0:00:10.\nSources: [hybrid] Abuse038_x264 | event_id=6 | 0.3-10.4",
    "expected": "final answer contains Sources:",
    "severity": "soft"
  },
  {
    "name": "grounding_coverage",
    "passed": true,
    "actual": {
      "summary": "The most relevant clip is in Abuse038_x264, around 0:00:00 - 0:00:10.",
      "style": "llm_summary",
      "confidence": 0.8,
      "citations": [
        {
          "source_type": "hybrid",
          "video_id": "Abuse038_x264",
          "event_id": 6,
          "start_time": 0.3,
          "end_time": 10.4,
          "record_level": "child"
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
      "user_need": "Retrieve video results that satisfy: Show me a person in the parking area",
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
      "expansion_terms": [],
      "base_rewritten_query": "Show me a person in the parking area",
      "scene_constraints": [],
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
      "match_verifier_node",
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
      "sql_rows_count": 1,
      "hybrid_rows_count": 0,
      "sql_error": null,
      "hybrid_error": "Collection expecting embedding with dimension of 1024, got 3072"
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
      "rerank_candidate_limit": 20,
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
    "actual": 1,
    "expected": 1,
    "severity": "hard"
  },
  {
    "name": "expected_keywords_any",
    "passed": false,
    "actual": "from 0.3s to 10.4s, several adults were talking on the side of the road. there were many vehicles on the road. later, two puppies appeared on the road. a black car hit the two puppies.",
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
  "elapsed_ms": 3925.07,
  "route_mode": "pure_sql",
  "label": "structured",
  "llm_final_output": "The most relevant clip is in Abuse038_x264, around 0:00:00 - 0:00:10.\nSources: [hybrid] Abuse038_x264 | event_id=6 | 0.3-10.4",
  "raw_final_answer": "Retrieval complete. Most relevant results:\n[1] event_id=6 | video=Abuse038_x264 | distance=0.0 | summary=From 0.3s to 10.4s, several adults were talking on the side of the road. There were many vehicles on the road. Later, two puppies appeared on the road. A black car hit the two puppies.",
  "rewritten_query": "Show me a person in the parking area",
  "original_user_query": "Show me a person in the parking area.",
  "self_query_result": {
    "rewritten_query": "Show me a person in the parking area",
    "user_need": "Retrieve video results that satisfy: Show me a person in the parking area",
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
    "expansion_terms": [],
    "base_rewritten_query": "Show me a person in the parking area",
    "scene_constraints": [],
    "original_user_query": "Show me a person in the parking area."
  },
  "summary_result": {
    "summary": "The most relevant clip is in Abuse038_x264, around 0:00:00 - 0:00:10.",
    "style": "llm_summary",
    "confidence": 0.8,
    "citations": [
      {
        "source_type": "hybrid",
        "video_id": "Abuse038_x264",
        "event_id": 6,
        "start_time": 0.3,
        "end_time": 10.4,
        "record_level": "child"
      }
    ]
  },
  "routing_metrics": {
    "execution_mode": "parallel_fusion",
    "label": "structured",
    "query": "Show me a person in the parking area",
    "sql_rows_count": 1,
    "hybrid_rows_count": 0,
    "sql_error": null,
    "hybrid_error": "Collection expecting embedding with dimension of 1024, got 3072"
  },
  "search_config": {
    "candidate_limit": 80,
    "top_k_per_event": 20,
    "rerank_top_k": 5,
    "rerank_candidate_limit": 20,
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
    "match_verifier_node",
    "final_answer_node",
    "summary_node"
  ],
  "final_answer": "The most relevant clip is in Abuse038_x264, around 0:00:00 - 0:00:10.\nSources: [hybrid] Abuse038_x264 | event_id=6 | 0.3-10.4",
  "tool_error": null,
  "error": null,
  "current_node": "summary_node",
  "top5": [
    {
      "event_id": 6,
      "video_id": "Abuse038_x264",
      "event_text": "From 0.3s to 10.4s, several adults were talking on the side of the road. There were many vehicles on the road. Later, two puppies appeared on the road. A black car hit the two puppies.",
      "distance": 0.0
    }
  ],
  "merged_count": 1,
  "sql_rows_count": 1,
  "hybrid_rows_count": 0,
  "degraded": true,
  "hybrid_summary": "",
  "sql_summary": "Deterministic SQL planner retrieval complete rows=1 stage=guided",
  "hybrid_error": "Collection expecting embedding with dimension of 1024, got 3072",
  "sql_error": null,
  "sql_debug": {
    "duration": 0.1711885139811784,
    "sql_summary": "Deterministic SQL planner retrieval complete rows=1 stage=guided",
    "hybrid_summary": "",
    "sql_error": null,
    "hybrid_error": "Collection expecting embedding with dimension of 1024, got 3072",
    "fusion_meta": {
      "label": "structured",
      "degraded": true,
      "degraded_reason": "hybrid_failed",
      "method": "fallback_sql_only"
    },
    "rerank_meta": {
      "enabled": true,
      "model": "cross-encoder/ms-marco-MiniLM-L-6-v2",
      "input_count": 1,
      "candidate_count": 1,
      "output_count": 1
    },
    "parent_rows_count": 1,
    "result_mode": "child_only",
    "parent_context": [
      {
        "video_id": "Abuse038_x264",
        "child_hit_count": 1,
        "start_time": 0.3,
        "end_time": 10.4,
        "best_distance": 0.0,
        "best_hybrid_score": null,
        "track_ids": [],
        "object_types": [
          "car"
        ],
        "object_colors": [
          "black"
        ],
        "scene_zones": [
          "road"
        ],
        "parent_rank": 1
      }
    ]
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
- Avg Latency: `8480.09 ms`
- P95 Latency: `8279.08 ms`
- Node Trace:

```json
[
  "self_query_node",
  "query_classification_node",
  "parallel_retrieval_fusion_node",
  "match_verifier_node",
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
  "sql_rows_count": 1,
  "hybrid_rows_count": 0,
  "sql_error": null,
  "hybrid_error": "Collection expecting embedding with dimension of 1024, got 3072"
}
```

- Search Config:

```json
{
  "candidate_limit": 80,
  "top_k_per_event": 20,
  "rerank_top_k": 5,
  "rerank_candidate_limit": 20,
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
  "user_need": "Retrieve video results that satisfy: Did you see any person in the database",
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
  "expansion_terms": [],
  "base_rewritten_query": "Did you see any person in the database",
  "scene_constraints": [],
  "original_user_query": "Did you see any person in the database?"
}
```

- Raw Final Answer:

```json
{
  "raw_final_answer": "Retrieval complete. Most relevant results:\n[1] event_id=6 | video=Abuse038_x264 | distance=0.0 | summary=From 0.3s to 10.4s, several adults were talking on the side of the road. There were many vehicles on the road. Later, two puppies appeared on the road. A black car hit the two puppies."
}
```

- LLM Final Output:

```json
{
  "llm_final_output": "Yes. The relevant clip is in Abuse038_x264, around 0:00:00 - 0:00:10.\nSources: [hybrid] Abuse038_x264 | event_id=6 | 0.3-10.4"
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
    "actual": "Yes. The relevant clip is in Abuse038_x264, around 0:00:00 - 0:00:10.\nSources: [hybrid] Abuse038_x264 | event_id=6 | 0.3-10.4",
    "expected": "non-empty string",
    "severity": "hard"
  },
  {
    "name": "citation_present",
    "passed": true,
    "actual": "Yes. The relevant clip is in Abuse038_x264, around 0:00:00 - 0:00:10.\nSources: [hybrid] Abuse038_x264 | event_id=6 | 0.3-10.4",
    "expected": "final answer contains Sources:",
    "severity": "soft"
  },
  {
    "name": "grounding_coverage",
    "passed": true,
    "actual": {
      "summary": "Yes. The relevant clip is in Abuse038_x264, around 0:00:00 - 0:00:10.",
      "style": "llm_summary",
      "confidence": 0.8,
      "citations": [
        {
          "source_type": "hybrid",
          "video_id": "Abuse038_x264",
          "event_id": 6,
          "start_time": 0.3,
          "end_time": 10.4,
          "record_level": "child"
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
      "user_need": "Retrieve video results that satisfy: Did you see any person in the database",
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
      "expansion_terms": [],
      "base_rewritten_query": "Did you see any person in the database",
      "scene_constraints": [],
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
      "match_verifier_node",
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
      "sql_rows_count": 1,
      "hybrid_rows_count": 0,
      "sql_error": null,
      "hybrid_error": "Collection expecting embedding with dimension of 1024, got 3072"
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
      "rerank_candidate_limit": 20,
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
    "actual": 1,
    "expected": 1,
    "severity": "hard"
  },
  {
    "name": "min_sql_rows",
    "passed": true,
    "actual": 1,
    "expected": 1,
    "severity": "hard"
  },
  {
    "name": "avg_latency_budget",
    "passed": true,
    "actual": 8480.09,
    "expected": 9000,
    "severity": "soft"
  }
]
```

- Last Iteration:

```json
{
  "elapsed_ms": 8279.08,
  "route_mode": "pure_sql",
  "label": "structured",
  "llm_final_output": "Yes. The relevant clip is in Abuse038_x264, around 0:00:00 - 0:00:10.\nSources: [hybrid] Abuse038_x264 | event_id=6 | 0.3-10.4",
  "raw_final_answer": "Retrieval complete. Most relevant results:\n[1] event_id=6 | video=Abuse038_x264 | distance=0.0 | summary=From 0.3s to 10.4s, several adults were talking on the side of the road. There were many vehicles on the road. Later, two puppies appeared on the road. A black car hit the two puppies.",
  "rewritten_query": "Did you see any person in the database",
  "original_user_query": "Did you see any person in the database?",
  "self_query_result": {
    "rewritten_query": "Did you see any person in the database",
    "user_need": "Retrieve video results that satisfy: Did you see any person in the database",
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
    "expansion_terms": [],
    "base_rewritten_query": "Did you see any person in the database",
    "scene_constraints": [],
    "original_user_query": "Did you see any person in the database?"
  },
  "summary_result": {
    "summary": "Yes. The relevant clip is in Abuse038_x264, around 0:00:00 - 0:00:10.",
    "style": "llm_summary",
    "confidence": 0.8,
    "citations": [
      {
        "source_type": "hybrid",
        "video_id": "Abuse038_x264",
        "event_id": 6,
        "start_time": 0.3,
        "end_time": 10.4,
        "record_level": "child"
      }
    ]
  },
  "routing_metrics": {
    "execution_mode": "parallel_fusion",
    "label": "structured",
    "query": "Did you see any person in the database",
    "sql_rows_count": 1,
    "hybrid_rows_count": 0,
    "sql_error": null,
    "hybrid_error": "Collection expecting embedding with dimension of 1024, got 3072"
  },
  "search_config": {
    "candidate_limit": 80,
    "top_k_per_event": 20,
    "rerank_top_k": 5,
    "rerank_candidate_limit": 20,
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
    "match_verifier_node",
    "final_answer_node",
    "summary_node"
  ],
  "final_answer": "Yes. The relevant clip is in Abuse038_x264, around 0:00:00 - 0:00:10.\nSources: [hybrid] Abuse038_x264 | event_id=6 | 0.3-10.4",
  "tool_error": null,
  "error": null,
  "current_node": "summary_node",
  "top5": [
    {
      "event_id": 6,
      "video_id": "Abuse038_x264",
      "event_text": "From 0.3s to 10.4s, several adults were talking on the side of the road. There were many vehicles on the road. Later, two puppies appeared on the road. A black car hit the two puppies.",
      "distance": 0.0
    }
  ],
  "merged_count": 1,
  "sql_rows_count": 1,
  "hybrid_rows_count": 0,
  "degraded": true,
  "hybrid_summary": "",
  "sql_summary": "Deterministic SQL planner retrieval complete rows=1 stage=guided",
  "hybrid_error": "Collection expecting embedding with dimension of 1024, got 3072",
  "sql_error": null,
  "sql_debug": {
    "duration": 0.014216990995919332,
    "sql_summary": "Deterministic SQL planner retrieval complete rows=1 stage=guided",
    "hybrid_summary": "",
    "sql_error": null,
    "hybrid_error": "Collection expecting embedding with dimension of 1024, got 3072",
    "fusion_meta": {
      "label": "structured",
      "degraded": true,
      "degraded_reason": "hybrid_failed",
      "method": "fallback_sql_only"
    },
    "rerank_meta": {
      "enabled": true,
      "model": "cross-encoder/ms-marco-MiniLM-L-6-v2",
      "input_count": 1,
      "candidate_count": 1,
      "output_count": 1
    },
    "parent_rows_count": 1,
    "result_mode": "child_only",
    "parent_context": [
      {
        "video_id": "Abuse038_x264",
        "child_hit_count": 1,
        "start_time": 0.3,
        "end_time": 10.4,
        "best_distance": 0.0,
        "best_hybrid_score": null,
        "track_ids": [],
        "object_types": [
          "car"
        ],
        "object_colors": [
          "black"
        ],
        "scene_zones": [
          "road"
        ],
        "parent_rank": 1
      }
    ]
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
- Avg Latency: `5370.75 ms`
- P95 Latency: `5280.25 ms`
- Node Trace:

```json
[
  "self_query_node",
  "query_classification_node",
  "parallel_retrieval_fusion_node",
  "match_verifier_node",
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
  "sql_rows_count": 5,
  "hybrid_rows_count": 0,
  "sql_error": null,
  "hybrid_error": "Collection expecting embedding with dimension of 1024, got 3072"
}
```

- Search Config:

```json
{
  "candidate_limit": 80,
  "top_k_per_event": 20,
  "rerank_top_k": 5,
  "rerank_candidate_limit": 20,
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
  "user_need": "Retrieve video results that satisfy: Find a person near the left bleachers",
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
  "expansion_terms": [],
  "base_rewritten_query": "Find a person near the left bleachers",
  "scene_constraints": [],
  "original_user_query": "Find a person near the left bleachers."
}
```

- Raw Final Answer:

```json
{
  "raw_final_answer": "Retrieval complete. Most relevant results:\n[1] event_id=3 | video=Abuse037_x264 | distance=0.0 | summary=From 25.3s to 48.5s, there was a black dog left on the road. It walked to the middle of the road next to the dog that had just been crushed.\n[2] event_id=4 | video=Abuse037_x264 | distance=0.0 | summary=From 48.5s to 59.1s, the black dog walked away and left the middle of the road.\n[3] event_id=5 | video=Abuse037_x264 | distance=0.0 | summary=From 40.4s to 47.6s, the gray dog pulled out the tail of the dog that had just been run over by the car, then stayed for a few minutes and left.\n[4] event_id=7 | video=Abuse038_x264 | distance=0.0 | summary=From 11.5s to 17.2s, two puppies rolled on the road, then one of the dogs left the road and the other stopped in the middle of the road.\n[5] event_id=6 | video=Abuse038_x264 | distance=0.0 | summary=From 0.3s to 10.4s, several adults were talking on the side of the road. There were many vehicles on the road. Later, two puppies appeared on the road. A black car hit the two puppies."
}
```

- LLM Final Output:

```json
{
  "llm_final_output": "The most relevant clip is in Abuse037_x264, around 0:00:25 - 0:00:48.\nSources: [hybrid] Abuse037_x264 | event_id=3 | 25.3-48.5; [hybrid] Abuse037_x264 | event_id=4 | 48.5-59.1; [hybrid] Abuse037_x264 | event_id=5 | 40.4-47.6"
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
    "actual": "The most relevant clip is in Abuse037_x264, around 0:00:25 - 0:00:48.\nSources: [hybrid] Abuse037_x264 | event_id=3 | 25.3-48.5; [hybrid] Abuse037_x264 | event_id=4 | 48.5-59.1; [hybrid] Abuse037_x264 | event_id=5 | 40.4-47.6",
    "expected": "non-empty string",
    "severity": "hard"
  },
  {
    "name": "citation_present",
    "passed": true,
    "actual": "The most relevant clip is in Abuse037_x264, around 0:00:25 - 0:00:48.\nSources: [hybrid] Abuse037_x264 | event_id=3 | 25.3-48.5; [hybrid] Abuse037_x264 | event_id=4 | 48.5-59.1; [hybrid] Abuse037_x264 | event_id=5 | 40.4-47.6",
    "expected": "final answer contains Sources:",
    "severity": "soft"
  },
  {
    "name": "grounding_coverage",
    "passed": true,
    "actual": {
      "summary": "The most relevant clip is in Abuse037_x264, around 0:00:25 - 0:00:48.",
      "style": "llm_summary",
      "confidence": 0.8,
      "citations": [
        {
          "source_type": "hybrid",
          "video_id": "Abuse037_x264",
          "event_id": 3,
          "start_time": 25.3,
          "end_time": 48.5,
          "record_level": "child"
        },
        {
          "source_type": "hybrid",
          "video_id": "Abuse037_x264",
          "event_id": 4,
          "start_time": 48.5,
          "end_time": 59.1,
          "record_level": "child"
        },
        {
          "source_type": "hybrid",
          "video_id": "Abuse037_x264",
          "event_id": 5,
          "start_time": 40.4,
          "end_time": 47.6,
          "record_level": "child"
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
      "user_need": "Retrieve video results that satisfy: Find a person near the left bleachers",
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
      "expansion_terms": [],
      "base_rewritten_query": "Find a person near the left bleachers",
      "scene_constraints": [],
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
      "match_verifier_node",
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
      "sql_rows_count": 5,
      "hybrid_rows_count": 0,
      "sql_error": null,
      "hybrid_error": "Collection expecting embedding with dimension of 1024, got 3072"
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
      "rerank_candidate_limit": 20,
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
    "actual": 5,
    "expected": 1,
    "severity": "hard"
  },
  {
    "name": "avg_latency_budget",
    "passed": true,
    "actual": 5370.75,
    "expected": 9000,
    "severity": "soft"
  },
  {
    "name": "semantic_backend_effective",
    "passed": true,
    "actual": {
      "hybrid_rows_count": 0,
      "hybrid_error": "Collection expecting embedding with dimension of 1024, got 3072",
      "degraded": true
    },
    "expected": "hybrid rows > 0 or explicit degradation/error",
    "severity": "hard"
  },
  {
    "name": "hybrid_health_consistency",
    "passed": true,
    "actual": {
      "hybrid_summary": "",
      "hybrid_error": "Collection expecting embedding with dimension of 1024, got 3072",
      "degraded": true
    },
    "expected": "hybrid failure should be reflected by degraded flag or hybrid_error",
    "severity": "hard"
  }
]
```

- Last Iteration:

```json
{
  "elapsed_ms": 4259.41,
  "route_mode": "hybrid_search",
  "label": "semantic",
  "llm_final_output": "The most relevant clip is in Abuse037_x264, around 0:00:25 - 0:00:48.\nSources: [hybrid] Abuse037_x264 | event_id=3 | 25.3-48.5; [hybrid] Abuse037_x264 | event_id=4 | 48.5-59.1; [hybrid] Abuse037_x264 | event_id=5 | 40.4-47.6",
  "raw_final_answer": "Retrieval complete. Most relevant results:\n[1] event_id=3 | video=Abuse037_x264 | distance=0.0 | summary=From 25.3s to 48.5s, there was a black dog left on the road. It walked to the middle of the road next to the dog that had just been crushed.\n[2] event_id=4 | video=Abuse037_x264 | distance=0.0 | summary=From 48.5s to 59.1s, the black dog walked away and left the middle of the road.\n[3] event_id=5 | video=Abuse037_x264 | distance=0.0 | summary=From 40.4s to 47.6s, the gray dog pulled out the tail of the dog that had just been run over by the car, then stayed for a few minutes and left.\n[4] event_id=7 | video=Abuse038_x264 | distance=0.0 | summary=From 11.5s to 17.2s, two puppies rolled on the road, then one of the dogs left the road and the other stopped in the middle of the road.\n[5] event_id=6 | video=Abuse038_x264 | distance=0.0 | summary=From 0.3s to 10.4s, several adults were talking on the side of the road. There were many vehicles on the road. Later, two puppies appeared on the road. A black car hit the two puppies.",
  "rewritten_query": "Find a person near the left bleachers",
  "original_user_query": "Find a person near the left bleachers.",
  "self_query_result": {
    "rewritten_query": "Find a person near the left bleachers",
    "user_need": "Retrieve video results that satisfy: Find a person near the left bleachers",
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
    "expansion_terms": [],
    "base_rewritten_query": "Find a person near the left bleachers",
    "scene_constraints": [],
    "original_user_query": "Find a person near the left bleachers."
  },
  "summary_result": {
    "summary": "The most relevant clip is in Abuse037_x264, around 0:00:25 - 0:00:48.",
    "style": "llm_summary",
    "confidence": 0.8,
    "citations": [
      {
        "source_type": "hybrid",
        "video_id": "Abuse037_x264",
        "event_id": 3,
        "start_time": 25.3,
        "end_time": 48.5,
        "record_level": "child"
      },
      {
        "source_type": "hybrid",
        "video_id": "Abuse037_x264",
        "event_id": 4,
        "start_time": 48.5,
        "end_time": 59.1,
        "record_level": "child"
      },
      {
        "source_type": "hybrid",
        "video_id": "Abuse037_x264",
        "event_id": 5,
        "start_time": 40.4,
        "end_time": 47.6,
        "record_level": "child"
      }
    ]
  },
  "routing_metrics": {
    "execution_mode": "parallel_fusion",
    "label": "semantic",
    "query": "Find a person near the left bleachers",
    "sql_rows_count": 5,
    "hybrid_rows_count": 0,
    "sql_error": null,
    "hybrid_error": "Collection expecting embedding with dimension of 1024, got 3072"
  },
  "search_config": {
    "candidate_limit": 80,
    "top_k_per_event": 20,
    "rerank_top_k": 5,
    "rerank_candidate_limit": 20,
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
    "match_verifier_node",
    "final_answer_node",
    "summary_node"
  ],
  "final_answer": "The most relevant clip is in Abuse037_x264, around 0:00:25 - 0:00:48.\nSources: [hybrid] Abuse037_x264 | event_id=3 | 25.3-48.5; [hybrid] Abuse037_x264 | event_id=4 | 48.5-59.1; [hybrid] Abuse037_x264 | event_id=5 | 40.4-47.6",
  "tool_error": null,
  "error": null,
  "current_node": "summary_node",
  "top5": [
    {
      "event_id": 3,
      "video_id": "Abuse037_x264",
      "event_text": "From 25.3s to 48.5s, there was a black dog left on the road. It walked to the middle of the road next to the dog that had just been crushed.",
      "distance": 0.0
    },
    {
      "event_id": 4,
      "video_id": "Abuse037_x264",
      "event_text": "From 48.5s to 59.1s, the black dog walked away and left the middle of the road.",
      "distance": 0.0
    },
    {
      "event_id": 5,
      "video_id": "Abuse037_x264",
      "event_text": "From 40.4s to 47.6s, the gray dog pulled out the tail of the dog that had just been run over by the car, then stayed for a few minutes and left.",
      "distance": 0.0
    },
    {
      "event_id": 7,
      "video_id": "Abuse038_x264",
      "event_text": "From 11.5s to 17.2s, two puppies rolled on the road, then one of the dogs left the road and the other stopped in the middle of the road.",
      "distance": 0.0
    },
    {
      "event_id": 6,
      "video_id": "Abuse038_x264",
      "event_text": "From 0.3s to 10.4s, several adults were talking on the side of the road. There were many vehicles on the road. Later, two puppies appeared on the road. A black car hit the two puppies.",
      "distance": 0.0
    }
  ],
  "merged_count": 5,
  "sql_rows_count": 5,
  "hybrid_rows_count": 0,
  "degraded": true,
  "hybrid_summary": "",
  "sql_summary": "Deterministic SQL planner retrieval complete rows=5 stage=guided",
  "hybrid_error": "Collection expecting embedding with dimension of 1024, got 3072",
  "sql_error": null,
  "sql_debug": {
    "duration": 0.014959070977056399,
    "sql_summary": "Deterministic SQL planner retrieval complete rows=5 stage=guided",
    "hybrid_summary": "",
    "sql_error": null,
    "hybrid_error": "Collection expecting embedding with dimension of 1024, got 3072",
    "fusion_meta": {
      "label": "semantic",
      "degraded": true,
      "degraded_reason": "hybrid_failed",
      "method": "fallback_sql_only"
    },
    "rerank_meta": {
      "enabled": true,
      "model": "cross-encoder/ms-marco-MiniLM-L-6-v2",
      "input_count": 5,
      "candidate_count": 5,
      "output_count": 5
    },
    "parent_rows_count": 5,
    "result_mode": "child_only",
    "parent_context": [
      {
        "video_id": "Abuse037_x264",
        "child_hit_count": 3,
        "start_time": 25.3,
        "end_time": 59.1,
        "best_distance": 0.0,
        "best_hybrid_score": null,
        "track_ids": [],
        "object_types": [
          "dog",
          "car"
        ],
        "object_colors": [
          "black",
          "gray"
        ],
        "scene_zones": [
          "road",
          "unknown"
        ],
        "parent_rank": 1
      },
      {
        "video_id": "Abuse038_x264",
        "child_hit_count": 2,
        "start_time": 0.3,
        "end_time": 17.2,
        "best_distance": 0.0,
        "best_hybrid_score": null,
        "track_ids": [],
        "object_types": [
          "dog",
          "car"
        ],
        "object_colors": [
          "unknown",
          "black"
        ],
        "scene_zones": [
          "road"
        ],
        "parent_rank": 2
      }
    ]
  }
}
```

