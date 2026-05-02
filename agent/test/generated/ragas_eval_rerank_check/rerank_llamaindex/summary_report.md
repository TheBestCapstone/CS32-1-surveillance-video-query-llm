# RAGAS Eval Report

## Summary
- Case count: `10`
- Success count: `10`
- Top hit rate: `0.9`
- Avg latency ms: `16273.49`

## Retrieval
- Context precision avg: `0.3889`
- Context recall avg: `0.3889`

## Generation
- Faithfulness avg: `0.3125`
- Answer relevancy avg: `0.3404`
- Factual correctness avg: `0.012`

## End To End
- RAGAS e2e avg: `0.2667`

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
- Generation: `{"answer_relevancy": 0.3424, "factual_correctness": 0.0, "faithfulness": 0.0}`
- End-to-end: `{"ragas_e2e_score": 0.0685}`
- Metric errors: `{}`

### PART1_0005
- Sheet: `Part1`
- Video: `Abuse038_x264`
- Question: Is there a clip of two puppies being hit by a car and rolling on the road?
- Route mode: `pure_sql`
- Top hit: `True`
- Retrieval: `{"context_precision": 1.0, "context_recall": 1.0}`
- Generation: `{"answer_relevancy": 0.313, "factual_correctness": 0.0, "faithfulness": 0.5714}`
- End-to-end: `{"ragas_e2e_score": 0.5769}`
- Metric errors: `{}`

### PART1_0006
- Sheet: `Part1`
- Video: `Abuse038_x264`
- Question: Animals fell on the road after a vehicle passed, while pedestrians were chatting nearby.
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 1.0, "context_recall": 1.0}`
- Generation: `{"answer_relevancy": 0.5958, "factual_correctness": 0.0, "faithfulness": 0.5556}`
- End-to-end: `{"ragas_e2e_score": 0.6303}`
- Metric errors: `{}`

### PART1_0007
- Sheet: `Part1`
- Video: `Abuse038_x264`
- Question: A car with its lights on stopped, and the headlights shone on something on the road ahead.
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 1.0, "context_recall": 1.0}`
- Generation: `{"answer_relevancy": 0.2654, "factual_correctness": 0.0, "faithfulness": 0.5714}`
- End-to-end: `{"ragas_e2e_score": 0.5674}`
- Metric errors: `{}`

### PART1_0008
- Sheet: `Part1`
- Video: `Abuse039_x264`
- Question: Is there a video of two staff members conducting a full-body search on a detained woman in a closed room?
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 0.0, "context_recall": 0.0}`
- Generation: `{"answer_relevancy": 0.3118, "factual_correctness": 0.0, "faithfulness": 0.0}`
- End-to-end: `{"ragas_e2e_score": 0.0624}`
- Metric errors: `{}`

### PART1_0009
- Sheet: `Part1`
- Video: `Abuse039_x264`
- Question: A woman was repeatedly told to turn around and face the wall in a closed room, and was forced to undress.
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 0.0, "context_recall": 0.0}`
- Generation: `{"answer_relevancy": 0.2432, "factual_correctness": 0.0, "faithfulness": 0.2}`
- End-to-end: `{"ragas_e2e_score": 0.0886}`
- Metric errors: `{}`

### PART1_0010
- Sheet: `Part1`
- Video: `Abuse039_x264`
- Question: A person used a handheld device to scan another person top to bottom, then someone took shoes from a conveyor belt.
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 0.0, "context_recall": 0.0}`
- Generation: `{"answer_relevancy": 0.2615, "factual_correctness": 0.0, "faithfulness": 0.4286}`
- End-to-end: `{"ragas_e2e_score": 0.138}`
- Metric errors: `{}`

### PART1_0011
- Sheet: `Part1`
- Video: `Abuse040_x264`
- Question: Is there a clip of a caregiver repeatedly hitting a white-haired elderly person on the head while they sit on a sofa?
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 0.0, "context_recall": 0.0}`
- Generation: `{"answer_relevancy": 0.4203, "factual_correctness": 0.12, "faithfulness": 0.2}`
- End-to-end: `{"ragas_e2e_score": 0.1481}`
- Metric errors: `{}`
