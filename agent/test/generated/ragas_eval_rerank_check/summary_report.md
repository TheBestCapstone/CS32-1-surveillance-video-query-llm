# RAGAS Eval Report

## Summary
- Case count: `3`
- Success count: `3`
- Top hit rate: `0.6667`
- Avg latency ms: `23176.62`

## Retrieval
- Context precision avg: `0.5`
- Context recall avg: `0.0`

## Generation
- Faithfulness avg: `0.2679`
- Answer relevancy avg: `0.2873`
- Factual correctness avg: `0.0`

## End To End
- RAGAS e2e avg: `0.1598`

## Cases
### PART1_0002
- Sheet: `Part1`
- Video: `Abuse037_x264`
- Question: Is there a clip of a car running over a black dog on the road?
- Route mode: `pure_sql`
- Top hit: `False`
- Retrieval: `{"context_precision": null, "context_recall": null}`
- Generation: `{"answer_relevancy": 0.0, "factual_correctness": 0.0, "faithfulness": null}`
- End-to-end: `{"ragas_e2e_score": 0.0}`
- Metric errors: `{}`

### PART1_0003
- Sheet: `Part1`
- Video: `Abuse037_x264`
- Question: A vehicle injured an animal on the road, and other animals approached the injured one afterward.
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 1.0, "context_recall": 0.0}`
- Generation: `{"answer_relevancy": 0.5766, "factual_correctness": 0.0, "faithfulness": 0.25}`
- End-to-end: `{"ragas_e2e_score": 0.3653}`
- Metric errors: `{}`

### PART1_0004
- Sheet: `Part1`
- Video: `Abuse037_x264`
- Question: An animal bent down to pull the tail of a motionless object on the ground, then left after a moment.
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 0.0, "context_recall": 0.0}`
- Generation: `{"answer_relevancy": 0.2853, "factual_correctness": 0.0, "faithfulness": 0.2857}`
- End-to-end: `{"ragas_e2e_score": 0.1142}`
- Metric errors: `{}`
