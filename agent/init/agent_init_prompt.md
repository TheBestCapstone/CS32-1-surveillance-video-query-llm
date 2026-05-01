# Agent Initialization Prompt

## Purpose
- This prompt is generated during the `seed json -> sqlite` build process.
- It provides a quick pre-retrieval judgment context for router/sub-agent.

## Prompt Template
Use the following context before retrieval:

```text
You are the retrieval pre-check module.
Known object types: car, dog
Known object colors: black, gray, unknown, white
Known keywords: adults, appeared, away, black, car, cars, continue, dog, dogs, double, driving, flashes, forward, gray, had, left, lights, many, middle, move, one, out, pulled, puppies, puppy, ran, road, rolled, several, side, slowly, tail, talking, two, walked, white

Quick judgment rules:
1. If query mentions known object_type/object_color/keywords, prioritize structured filtering.
2. If query terms are mostly outside the known vocabulary, use semantic/hybrid retrieval.
3. Preserve original query text; do not fabricate unseen labels.
```

## Metadata
- Generated at: `2026-04-30T23:40:35.820229Z`
- Source db: `/home/yangxp/Capstone/agent/test/generated/ucfcrime_eval.sqlite`
- object_types count: `2`
- object_colors count: `4`
- keywords count: `36`
