# RAGAS Eval Report

## Summary
- Case count: `4`
- Success count: `4`
- Top hit rate: `0.75`
- Avg latency ms: `11237.89`

## Retrieval
- Context precision avg: `0.375`
- Context recall avg: `0.5`

## Generation
- Faithfulness avg: `0.75`
- Answer relevancy avg: `0.4976`
- Factual correctness avg: `0.0`

## End To End
- RAGAS e2e avg: `0.4245`

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
- Retrieval: `{"context_precision": 0.5, "context_recall": 1.0}`
- Generation: `{"answer_relevancy": 0.731, "factual_correctness": 0.0, "faithfulness": 1.0}`
- End-to-end: `{"ragas_e2e_score": 0.6462}`

### PART1_0004
- Sheet: `Part1`
- Video: `Abuse037_x264`
- Question: An animal bent down to pull the tail of a motionless object on the ground, then left after a moment.
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 0.0, "context_recall": 0.0}`
- Generation: `{"answer_relevancy": 0.5415, "factual_correctness": 0.0, "faithfulness": 1.0}`
- End-to-end: `{"ragas_e2e_score": 0.3083}`

### PART1_0005
- Sheet: `Part1`
- Video: `Abuse038_x264`
- Question: Is there a clip of two puppies being hit by a car and rolling on the road?
- Route mode: `pure_sql`
- Top hit: `True`
- Retrieval: `{"context_precision": 1.0, "context_recall": 1.0}`
- Generation: `{"answer_relevancy": 0.7178, "factual_correctness": 0.0, "faithfulness": 1.0}`
- End-to-end: `{"ragas_e2e_score": 0.7436}`
