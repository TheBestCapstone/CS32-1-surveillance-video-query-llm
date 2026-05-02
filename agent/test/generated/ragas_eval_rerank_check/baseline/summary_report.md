# RAGAS Eval Report

## Summary
- Case count: `10`
- Success count: `10`
- Top hit rate: `0.8`
- Avg latency ms: `10889.18`

## Retrieval
- Context precision avg: `0.4375`
- Context recall avg: `0.375`

## Generation
- Faithfulness avg: `0.2201`
- Answer relevancy avg: `0.3323`
- Factual correctness avg: `0.014`

## End To End
- RAGAS e2e avg: `0.2345`

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
- Retrieval: `{"context_precision": 0.5, "context_recall": 0.0}`
- Generation: `{"answer_relevancy": 0.6506, "factual_correctness": 0.0, "faithfulness": 0.2857}`
- End-to-end: `{"ragas_e2e_score": 0.2873}`
- Metric errors: `{}`

### PART1_0004
- Sheet: `Part1`
- Video: `Abuse037_x264`
- Question: An animal bent down to pull the tail of a motionless object on the ground, then left after a moment.
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 0.0, "context_recall": 0.0}`
- Generation: `{"answer_relevancy": 0.3599, "factual_correctness": 0.0, "faithfulness": 0.0}`
- End-to-end: `{"ragas_e2e_score": 0.072}`
- Metric errors: `{}`

### PART1_0005
- Sheet: `Part1`
- Video: `Abuse038_x264`
- Question: Is there a clip of two puppies being hit by a car and rolling on the road?
- Route mode: `pure_sql`
- Top hit: `True`
- Retrieval: `{"context_precision": 1.0, "context_recall": 1.0}`
- Generation: `{"answer_relevancy": 0.3582, "factual_correctness": 0.0, "faithfulness": 0.5}`
- End-to-end: `{"ragas_e2e_score": 0.5716}`
- Metric errors: `{}`

### PART1_0006
- Sheet: `Part1`
- Video: `Abuse038_x264`
- Question: Animals fell on the road after a vehicle passed, while pedestrians were chatting nearby.
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 1.0, "context_recall": 1.0}`
- Generation: `{"answer_relevancy": 0.4385, "factual_correctness": 0.0, "faithfulness": 0.6}`
- End-to-end: `{"ragas_e2e_score": 0.6077}`
- Metric errors: `{}`

### PART1_0007
- Sheet: `Part1`
- Video: `Abuse038_x264`
- Question: A car with its lights on stopped, and the headlights shone on something on the road ahead.
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 1.0, "context_recall": 1.0}`
- Generation: `{"answer_relevancy": 0.0991, "factual_correctness": 0.0, "faithfulness": 0.375}`
- End-to-end: `{"ragas_e2e_score": 0.4948}`
- Metric errors: `{}`

### PART1_0008
- Sheet: `Part1`
- Video: `Abuse039_x264`
- Question: Is there a video of two staff members conducting a full-body search on a detained woman in a closed room?
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 0.0, "context_recall": 0.0}`
- Generation: `{"answer_relevancy": 0.8364, "factual_correctness": 0.14, "faithfulness": 0.0}`
- End-to-end: `{"ragas_e2e_score": 0.1953}`
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
- Generation: `{"answer_relevancy": 0.2615, "factual_correctness": 0.0, "faithfulness": 0.0}`
- End-to-end: `{"ragas_e2e_score": 0.0523}`
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
