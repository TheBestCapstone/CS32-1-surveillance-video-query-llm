# Agent Initialization Prompt

## Purpose
- This prompt is generated during the `seed json -> sqlite` build process.
- It provides a quick pre-retrieval judgment context for router/sub-agent.

## Prompt Template
Use the following context before retrieval:

```text
You are the retrieval pre-check module.
Known object types: person
Known object colors: dark, unknown
Known keywords: baseline, bench_area, bleachers, center, center_left, center_right, court, court_edge, driving_in, idle, indoor, left, left_center, left_side, lower_left, movement, person, right_center, right_edge, right_side, road_right, sideline, standing, static, upper_middle, walking

Quick judgment rules:
1. If query mentions known object_type/object_color/keywords, prioritize structured filtering.
2. If query terms are mostly outside the known vocabulary, use semantic/hybrid retrieval.
3. Preserve original query text; do not fabricate unseen labels.
```

## Metadata
- Generated at: `2026-04-18T16:18:32.210845Z`
- Source db: `/home/yangxp/Capstone/data/SQLite/episodic_events.sqlite`
- object_types count: `1`
- object_colors count: `2`
- keywords count: `26`
