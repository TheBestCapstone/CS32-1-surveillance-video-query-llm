# RAGAS Eval Report

## Summary
- Case count: `4`
- Success count: `4`
- Top hit rate: `0.75`
- Avg latency ms: `10708.47`

## Retrieval
- Context precision avg: `0.5`
- Context recall avg: `0.5`

## Generation
- Faithfulness avg: `0.4405`
- Answer relevancy avg: `0.346`
- Factual correctness avg: `0.0425`

## End To End
- RAGAS e2e avg: `0.2938`

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
- Retrieval: `{"context_precision": 0.5, "context_recall": 0.5}`
- Generation: `{"answer_relevancy": 0.515, "factual_correctness": 0.0, "faithfulness": 0.25}`
- End-to-end: `{"ragas_e2e_score": 0.353}`
- Metric errors: `{}`

### PART1_0004
- Sheet: `Part1`
- Video: `Abuse037_x264`
- Question: An animal bent down to pull the tail of a motionless object on the ground, then left after a moment.
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 0.0, "context_recall": 0.0}`
- Generation: `{"answer_relevancy": 0.556, "factual_correctness": 0.0, "faithfulness": 0.5}`
- End-to-end: `{"ragas_e2e_score": 0.2112}`
- Metric errors: `{}`

### PART1_0005
- Sheet: `Part1`
- Video: `Abuse038_x264`
- Question: Is there a clip of two puppies being hit by a car and rolling on the road?
- Route mode: `pure_sql`
- Top hit: `True`
- Retrieval: `{"context_precision": 1.0, "context_recall": 1.0}`
- Generation: `{"answer_relevancy": 0.313, "factual_correctness": 0.17, "faithfulness": 0.5714}`
- End-to-end: `{"ragas_e2e_score": 0.6109}`
- Metric errors: `{}`
