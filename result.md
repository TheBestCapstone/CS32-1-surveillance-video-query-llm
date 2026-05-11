# Graph Result Test Report

- Generated At: `2026-04-19 04:42:53`
- Cases File: `/home/yangxp/Capstone/agent/test/result_cases.json`
- Basketball Data Profile:

```json
{
  "exists": true,
  "video_count": 2,
  "event_count": 27,
  "object_types_sample": [
    "person"
  ],
  "colors_sample": [
    "dark",
    "unknown"
  ],
  "scene_zones_sample": [
    "court center",
    "court center-right",
    "court left-center",
    "court upper-middle",
    "left bleachers",
    "left side",
    "parking",
    "road_right",
    "sidewalk"
  ]
}
```

- Summary:

```json
{
  "total": 5,
  "passed": 5,
  "soft_failed": 0,
  "failed": 0,
  "pass_rate": 1.0,
  "soft_fail_rate": 0.0,
  "hard_fail_rate": 0.0,
  "avg_ms": 7708.0,
  "p95_ms": 8370.41,
  "failure_categories": {
    "runtime_exception": 0,
    "route_mismatch": 0,
    "tool_error": 0,
    "insufficient_results": 0,
    "top_field_missing": 0,
    "trace_gap": 0,
    "routing_metrics_missing": 0,
    "citation_missing": 0
  },
  "metrics_summary": {
    "citation_coverage_rate": 1.0,
    "trace_coverage_rate": 1.0,
    "routing_metrics_coverage_rate": 1.0
  }
}
```

- Metrics Summary:

```json
{
  "citation_coverage_rate": 1.0,
  "trace_coverage_rate": 1.0,
  "routing_metrics_coverage_rate": 1.0
}
```

## TC01

- 问题: `Did you see any person in the database?`
- 预期答案: 
- 模型返回答案: `Yes, multiple people were detected in the video. The top results show individuals staying mostly still near the left baseline or bench area, with appearances ranging from about 12 to over 140 seconds in duration. Sources: [sql] basketball_1.mp4 | event_id=1 | 0.0-61.208333333333336; [sql] basketball_1.mp4 | event_id=2 | 0.0-16.083333333333332; [sql] basketball_1.mp4 | event_id=3 | 0.0-12.041666666666666`
- 路由模式: `pure_sql`
- 当前节点: `summary_node`
- 耗时: `7277.73 ms`
- 错误: `None`
- 工具错误: `None`
- 结果: `PASS`
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

- 断言明细:

```json
[
  {
    "name": "no_runtime_exception",
    "passed": true,
    "actual": null,
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
    "name": "no_tool_error",
    "passed": true,
    "actual": null,
    "expected": null,
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
    "name": "citation_present",
    "passed": true,
    "actual": "Yes, multiple people were detected in the video. The top results show individuals staying mostly still near the left baseline or bench area, with appearances ranging from about 12 to over 140 seconds in duration.\nSources: [sql] basketball_1.mp4 | event_id=1 | 0.0-61.208333333333336; [sql] basketball_1.mp4 | event_id=2 | 0.0-16.083333333333332; [sql] basketball_1.mp4 | event_id=3 | 0.0-12.041666666666666",
    "expected": "final answer contains Sources:",
    "severity": "soft"
  },
  {
    "name": "min_results",
    "passed": true,
    "actual": 5,
    "expected": 1,
    "severity": "soft"
  }
]
```

- Top1-Top5:

```json
[
  {
    "video_id": "basketball_1.mp4",
    "event_text": "From 0.0s to 61.2s, a person with unknown color stays mostly still near the left baseline/bench area."
  },
  {
    "video_id": "basketball_1.mp4",
    "event_text": "From 0.0s to 16.1s, a person with unknown color remains mostly still near the left-center baseline area."
  },
  {
    "video_id": "basketball_1.mp4",
    "event_text": "From 0.0s to 12.0s, a person with unknown color remains mostly still near the left-center baseline area."
  },
  {
    "video_id": "basketball_1.mp4",
    "event_text": "From 0.0s to 143.1s, a person with unknown color stays mostly still near the lower-left court/bench area."
  },
  {
    "video_id": "basketball_1.mp4",
    "event_text": "From 0.0s to 17.5s, a person with unknown color remains mostly still near the left-center baseline area."
  }
]
```

- Thought:

```json
{
  "thought": "SelfQuery: focus=structured, intent=structured"
}
```

- SQL Debug:

```json
{
  "duration": 1.7002703629987082,
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
```

## TC02

- 问题: `Show me dark persons.`
- 预期答案: 
- 模型返回答案: `In the video *basketball_2.mp4*, several clips show people in dark clothing: two standing still near the left bleachers (0–30.8s and 0–10s), and others moving across different court areas between 40.6s and 50.5s. Sources: [sql] basketball_2.mp4 | event_id=22 | 0.0-30.84; [sql] basketball_2.mp4 | event_id=27 | 0.0-9.96; [sql] basketball_2.mp4 | event_id=23 | 40.6-44.9`
- 路由模式: `pure_sql`
- 当前节点: `summary_node`
- 耗时: `8112.2 ms`
- 错误: `None`
- 工具错误: `None`
- 结果: `PASS`
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
  "query": "Show me dark persons",
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

- 断言明细:

```json
[
  {
    "name": "no_runtime_exception",
    "passed": true,
    "actual": null,
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
    "name": "no_tool_error",
    "passed": true,
    "actual": null,
    "expected": null,
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
      "query": "Show me dark persons",
      "sql_rows_count": 6,
      "hybrid_rows_count": 26,
      "sql_error": null,
      "hybrid_error": null
    },
    "expected": "non-empty routing_metrics",
    "severity": "soft"
  },
  {
    "name": "citation_present",
    "passed": true,
    "actual": "In the video *basketball_2.mp4*, several clips show people in dark clothing: two standing still near the left bleachers (0–30.8s and 0–10s), and others moving across different court areas between 40.6s and 50.5s.\nSources: [sql] basketball_2.mp4 | event_id=22 | 0.0-30.84; [sql] basketball_2.mp4 | event_id=27 | 0.0-9.96; [sql] basketball_2.mp4 | event_id=23 | 40.6-44.9",
    "expected": "final answer contains Sources:",
    "severity": "soft"
  },
  {
    "name": "min_results",
    "passed": true,
    "actual": 5,
    "expected": 1,
    "severity": "soft"
  }
]
```

- Top1-Top5:

```json
[
  {
    "video_id": "basketball_2.mp4",
    "event_text": "From 0.00s to 30.84s, a dark-clothed person stands near the left bleachers with little motion."
  },
  {
    "video_id": "basketball_2.mp4",
    "event_text": "From 0.00s to 9.96s, a dark-clothed person stands near the left side with little motion."
  },
  {
    "video_id": "basketball_2.mp4",
    "event_text": "From 40.60s to 44.90s, a dark-clothed person moves across the center-right court area."
  },
  {
    "video_id": "basketball_2.mp4",
    "event_text": "From 41.50s to 46.85s, a dark-clothed person moves near the left-center court area."
  },
  {
    "video_id": "basketball_2.mp4",
    "event_text": "From 46.15s to 50.45s, a dark-clothed person moves near the upper-middle court area."
  }
]
```

- Thought:

```json
{
  "thought": "SelfQuery: focus=structured, intent=structured"
}
```

- SQL Debug:

```json
{
  "duration": 2.8803786839998793,
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
```

## TC03

- 问题: `Find a person near the left bleachers.`
- 预期答案: 
- 模型返回答案: `A dark-clothed person stands near the left bleachers with little motion from 0.00s to 30.84s in *basketball_2.mp4*. In *basketball_1.mp4*, several individuals remain mostly still near the left baseline, bench area, or left side of the court during various time intervals. Sources: [hybrid] basketball_2.mp4 | event_id=basketball_2.mp4_track_id_1 | 0.0-30.84; [hybrid] basketball_1.mp4 | event_id=basketball_1.mp4_track_1 | 0.0-61.208333333333336; [hybrid] basketball_1.mp4 | event_id=basketball_1.mp4_track_29 | 43.791666666666664-125.70833333333331`
- 路由模式: `hybrid_search`
- 当前节点: `summary_node`
- 耗时: `9203.96 ms`
- 错误: `None`
- 工具错误: `None`
- 结果: `PASS`
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

- 断言明细:

```json
[
  {
    "name": "no_runtime_exception",
    "passed": true,
    "actual": null,
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
    "name": "no_tool_error",
    "passed": true,
    "actual": null,
    "expected": null,
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
    "name": "citation_present",
    "passed": true,
    "actual": "A dark-clothed person stands near the left bleachers with little motion from 0.00s to 30.84s in *basketball_2.mp4*. In *basketball_1.mp4*, several individuals remain mostly still near the left baseline, bench area, or left side of the court during various time intervals.\nSources: [hybrid] basketball_2.mp4 | event_id=basketball_2.mp4_track_id_1 | 0.0-30.84; [hybrid] basketball_1.mp4 | event_id=basketball_1.mp4_track_1 | 0.0-61.208333333333336; [hybrid] basketball_1.mp4 | event_id=basketball_1.mp4_track_29 | 43.791666666666664-125.70833333333331",
    "expected": "final answer contains Sources:",
    "severity": "soft"
  },
  {
    "name": "min_results",
    "passed": true,
    "actual": 5,
    "expected": 1,
    "severity": "soft"
  }
]
```

- Top1-Top5:

```json
[
  {
    "video_id": "basketball_2.mp4",
    "event_text": "standing near left bleachers with little motion Located in left bleachers. From 0.00s to 30.84s, a dark-clothed person stands near the left bleachers with little motion."
  },
  {
    "video_id": "basketball_1.mp4",
    "event_text": "Little motion; standing near the left baseline/bench area. Located in sidewalk. From 0.0s to 61.2s, a person with unknown color stays mostly still near the left baseline/bench area."
  },
  {
    "video_id": "basketball_1.mp4",
    "event_text": "Little motion; standing near the left side of the court. Located in sidewalk. From 43.8s to 125.7s, a person with unknown color remains mostly still near the left side of the court."
  },
  {
    "video_id": "basketball_1.mp4",
    "event_text": "Little motion; standing near the left-center court area. Located in sidewalk. From 47.8s to 48.8s, a person with unknown color remains mostly still near the left-center court area."
  },
  {
    "video_id": "basketball_1.mp4",
    "event_text": "Little motion; standing near the left-center baseline area. Located in sidewalk. From 11.5s to 91.8s, a person with unknown color remains mostly still near the left-center baseline area."
  }
]
```

- Thought:

```json
{
  "thought": "SelfQuery: focus=semantic, intent=semantic"
}
```

- SQL Debug:

```json
{
  "duration": 2.9722101250008564,
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
```

## TC04

- 问题: `Look for a person moving on the sidewalk.`
- 预期答案: 
- 模型返回答案: `The search found multiple instances of people on the sidewalk near the left-center baseline area, but they were mostly standing still rather than moving. These appear in the video *basketball_1.mp4* across various time segments, including 0–5 seconds, 11.5–91.8 seconds, and others. While located where requested, the individuals show little motion. Sources: [hybrid] basketball_1.mp4 | event_id=basketball_1.mp4_track_8 | 0.0-4.958333333333333; [hybrid] basketball_1.mp4 | event_id=basketball_1.mp4_track_11 | 11.5-91.75; [hybrid] basketball_1.mp4 | event_id=basketball_1.mp4_track_6 | 0.0-17.458333333333332`
- 路由模式: `hybrid_search`
- 当前节点: `summary_node`
- 耗时: `8370.41 ms`
- 错误: `None`
- 工具错误: `None`
- 结果: `PASS`
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

- 断言明细:

```json
[
  {
    "name": "no_runtime_exception",
    "passed": true,
    "actual": null,
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
    "name": "no_tool_error",
    "passed": true,
    "actual": null,
    "expected": null,
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
    "name": "citation_present",
    "passed": true,
    "actual": "The search found multiple instances of people on the sidewalk near the left-center baseline area, but they were mostly standing still rather than moving. These appear in the video *basketball_1.mp4* across various time segments, including 0–5 seconds, 11.5–91.8 seconds, and others. While located where requested, the individuals show little motion.\nSources: [hybrid] basketball_1.mp4 | event_id=basketball_1.mp4_track_8 | 0.0-4.958333333333333; [hybrid] basketball_1.mp4 | event_id=basketball_1.mp4_track_11 | 11.5-91.75; [hybrid] basketball_1.mp4 | event_id=basketball_1.mp4_track_6 | 0.0-17.458333333333332",
    "expected": "final answer contains Sources:",
    "severity": "soft"
  },
  {
    "name": "min_results",
    "passed": true,
    "actual": 5,
    "expected": 1,
    "severity": "soft"
  }
]
```

- Top1-Top5:

```json
[
  {
    "video_id": "basketball_1.mp4",
    "event_text": "Little motion; standing near the left-center baseline area. Located in sidewalk. From 0.0s to 5.0s, a person with unknown color remains mostly still near the left-center baseline area."
  },
  {
    "video_id": "basketball_1.mp4",
    "event_text": "Little motion; standing near the left-center baseline area. Located in sidewalk. From 11.5s to 91.8s, a person with unknown color remains mostly still near the left-center baseline area."
  },
  {
    "video_id": "basketball_1.mp4",
    "event_text": "Little motion; standing near the left-center baseline area. Located in sidewalk. From 0.0s to 17.5s, a person with unknown color remains mostly still near the left-center baseline area."
  },
  {
    "video_id": "basketball_1.mp4",
    "event_text": "Little motion; standing near the left-center baseline area. Located in sidewalk. From 0.0s to 12.0s, a person with unknown color remains mostly still near the left-center baseline area."
  },
  {
    "video_id": "basketball_1.mp4",
    "event_text": "Little motion; standing near the left-center court edge. Located in sidewalk. From 62.4s to 64.0s, a person with unknown color remains mostly still near the left-center court edge."
  }
]
```

- Thought:

```json
{
  "thought": "SelfQuery: focus=semantic, intent=semantic"
}
```

- SQL Debug:

```json
{
  "duration": 2.805793921001168,
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
```

## TC05

- 问题: `Are there any cars in the database?`
- 预期答案: 
- 模型返回答案: `No matching results found. You can add more specific descriptions like colors or actions.`
- 路由模式: `pure_sql`
- 当前节点: `summary_node`
- 耗时: `5575.72 ms`
- 错误: `None`
- 工具错误: `None`
- 结果: `PASS`
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

- 断言明细:

```json
[
  {
    "name": "no_runtime_exception",
    "passed": true,
    "actual": null,
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
    "name": "no_tool_error",
    "passed": true,
    "actual": null,
    "expected": null,
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
    "name": "min_results",
    "passed": true,
    "actual": 0,
    "expected": 0,
    "severity": "soft"
  }
]
```

- Top1-Top5:

```json
[]
```

- Thought:

```json
{
  "thought": "SelfQuery: focus=structured, intent=structured"
}
```

- SQL Debug:

```json
{
  "duration": 2.771013967001636,
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
```

