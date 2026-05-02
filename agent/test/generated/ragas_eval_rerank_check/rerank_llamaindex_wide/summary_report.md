# RAGAS Eval Report

## Summary
- Case count: `10`
- Success count: `10`
- Top hit rate: `0.8`
- Avg latency ms: `15567.24`

## Retrieval
- Context precision avg: `0.4375`
- Context recall avg: `0.375`

## Generation
- Faithfulness avg: `0.3067`
- Answer relevancy avg: `0.3446`
- Factual correctness avg: `0.014`

## End To End
- RAGAS e2e avg: `0.2508`

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
- Generation: `{"answer_relevancy": 0.6506, "factual_correctness": 0.0, "faithfulness": 0.2857}`
- End-to-end: `{"ragas_e2e_score": 0.3873}`
- Metric errors: `{}`

### PART1_0004
- Sheet: `Part1`
- Video: `Abuse037_x264`
- Question: An animal bent down to pull the tail of a motionless object on the ground, then left after a moment.
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 0.0, "context_recall": 0.0}`
- Generation: `{"answer_relevancy": 0.3212, "factual_correctness": 0.0, "faithfulness": 0.2}`
- End-to-end: `{"ragas_e2e_score": 0.1042}`
- Metric errors: `{}`

### PART1_0005
- Sheet: `Part1`
- Video: `Abuse038_x264`
- Question: Is there a clip of two puppies being hit by a car and rolling on the road?
- Route mode: `pure_sql`
- Top hit: `True`
- Retrieval: `{"context_precision": 1.0, "context_recall": 1.0}`
- Generation: `{"answer_relevancy": 0.313, "factual_correctness": 0.14, "faithfulness": 0.5714}`
- End-to-end: `{"ragas_e2e_score": 0.6049}`
- Metric errors: `{}`

### PART1_0006
- Sheet: `Part1`
- Video: `Abuse038_x264`
- Question: Animals fell on the road after a vehicle passed, while pedestrians were chatting nearby.
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 1.0, "context_recall": 1.0}`
- Generation: `{"answer_relevancy": 0.4997, "factual_correctness": 0.0, "faithfulness": 0.625}`
- End-to-end: `{"ragas_e2e_score": 0.6249}`
- Metric errors: `{}`

### PART1_0007
- Sheet: `Part1`
- Video: `Abuse038_x264`
- Question: A car with its lights on stopped, and the headlights shone on something on the road ahead.
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 1.0, "context_recall": 0.5}`
- Generation: `{"answer_relevancy": 0.2614, "factual_correctness": 0.0, "faithfulness": 0.5714}`
- End-to-end: `{"ragas_e2e_score": 0.4666}`
- Metric errors: `{}`

### PART1_0008
- Sheet: `Part1`
- Video: `Abuse039_x264`
- Question: Is there a video of two staff members conducting a full-body search on a detained woman in a closed room?
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 0.0, "context_recall": 0.0}`
- Generation: `{"answer_relevancy": 0.8364, "factual_correctness": 0.0, "faithfulness": 0.0}`
- End-to-end: `{"ragas_e2e_score": 0.1673}`
- Metric errors: `{}`

### PART1_0009
- Sheet: `Part1`
- Video: `Abuse039_x264`
- Question: A woman was repeatedly told to turn around and face the wall in a closed room, and was forced to undress.
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 0.0, "context_recall": 0.0}`
- Generation: `{"answer_relevancy": 0.3187, "factual_correctness": 0.0, "faithfulness": 0.0}`
- End-to-end: `{"ragas_e2e_score": 0.0637}`
- Metric errors: `{}`

### PART1_0010
- Sheet: `Part1`
- Video: `Abuse039_x264`
- Question: A person used a handheld device to scan another person top to bottom, then someone took shoes from a conveyor belt.
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 0.0, "context_recall": 0.0}`
- Generation: `{"answer_relevancy": 0.2446, "factual_correctness": 0.0, "faithfulness": 0.2}`
- End-to-end: `{"ragas_e2e_score": 0.0889}`
- Metric errors: `{}`

### PART1_0011
- Sheet: `Part1`
- Video: `Abuse040_x264`
- Question: Is there a clip of a caregiver repeatedly hitting a white-haired elderly person on the head while they sit on a sofa?
- Route mode: `pure_sql`
- Top hit: `False`
- Retrieval: `{"context_precision": null, "context_recall": null}`
- Generation: `{"answer_relevancy": 0.0, "factual_correctness": 0.0, "faithfulness": null}`
- End-to-end: `{"ragas_e2e_score": 0.0}`
- Metric errors: `{}`
