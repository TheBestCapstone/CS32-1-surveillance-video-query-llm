# RAGAS Eval Report

## Summary
- Case count: `2`
- Success count: `2`
- Top hit rate: `0.5`
- Avg latency ms: `10917.98`

## Retrieval
- Context precision avg: `0.5`
- Context recall avg: `0.5`

## Generation
- Faithfulness avg: `0.4`
- Answer relevancy avg: `0.377`
- Factual correctness avg: `0.0`

## End To End
- RAGAS e2e avg: `0.3554`

## Cases
### PART1_0002
- Sheet: `Part1`
- Video: `Abuse037_x264`
- Question: Is there a clip of a car running over a black dog on the road?
- Route mode: `pure_sql`
- Top hit: `False`
- Retrieval: `{"context_precision": 0.0, "context_recall": 0.0}`
- Generation: `{"answer_relevancy": 0.0, "factual_correctness": 0.0, "faithfulness": 0.0}`
- End-to-end: `{"ragas_e2e_score": 0.0}`

### PART1_0003
- Sheet: `Part1`
- Video: `Abuse037_x264`
- Question: A vehicle injured an animal on the road, and other animals approached the injured one afterward.
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 1.0, "context_recall": 1.0}`
- Generation: `{"answer_relevancy": 0.7541, "factual_correctness": 0.0, "faithfulness": 0.8}`
- End-to-end: `{"ragas_e2e_score": 0.7108}`
