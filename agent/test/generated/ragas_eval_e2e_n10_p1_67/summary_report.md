# RAGAS Eval Report

## Summary
- Case count: `10`
- Success count: `10`
- Top hit rate: `1.0`
- Avg latency ms: `10185.68`

## Retrieval
- Context precision avg: `0.45`
- Context recall avg: `0.3`

## Generation
- Faithfulness avg: `0.1917`
- Factual correctness avg: `0.6`

## Temporal Localization
- Time overlap IoU avg: `0.1333`
- Time overlap case count: `8`
- Time overlap hit@0.3: `0.125`
- Time overlap hit@0.5: `0.125`

## End To End
- RAGAS e2e avg: `0.3854`

## Cases
### PART1_0002
- Sheet: `Part1`
- Video: `Abuse037_x264`
- Question: Is there a clip of a car running over a black dog on the road?
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 1.0, "context_recall": 0.5}`
- Generation: `{"factual_correctness": 0.5, "faithfulness": 0.6667}`
- Temporal: `{"time_range_overlap_iou": 0.1058, "temporal_iou": 0.1058, "eligible": true, "video_match": true}`
- End-to-end: `{"ragas_e2e_score": 0.6667}`
- Metric errors: `{}`

### PART1_0003
- Sheet: `Part1`
- Video: `Abuse037_x264`
- Question: A vehicle injured an animal on the road, and other animals approached the injured one afterward.
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 0.0, "context_recall": 0.5}`
- Generation: `{"factual_correctness": 0.5, "faithfulness": 0.25}`
- Temporal: `{"time_range_overlap_iou": 0.0, "temporal_iou": 0.0, "eligible": true, "video_match": false}`
- End-to-end: `{"ragas_e2e_score": 0.3125}`
- Metric errors: `{}`

### PART1_0004
- Sheet: `Part1`
- Video: `Abuse037_x264`
- Question: An animal bent down to pull the tail of a motionless object on the ground, then left after a moment.
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 0.0, "context_recall": 0.0}`
- Generation: `{"factual_correctness": 1.0, "faithfulness": 0.0}`
- Temporal: `{"time_range_overlap_iou": null, "temporal_iou": null, "eligible": false, "video_match": null}`
- End-to-end: `{"ragas_e2e_score": 0.25}`
- Metric errors: `{}`

### PART1_0005
- Sheet: `Part1`
- Video: `Abuse038_x264`
- Question: Is there a clip of two puppies being hit by a car and rolling on the road?
- Route mode: `pure_sql`
- Top hit: `True`
- Retrieval: `{"context_precision": 1.0, "context_recall": 0.5}`
- Generation: `{"factual_correctness": 1.0, "faithfulness": 0.0}`
- Temporal: `{"time_range_overlap_iou": 0.1102, "temporal_iou": 0.1102, "eligible": true, "video_match": true}`
- End-to-end: `{"ragas_e2e_score": 0.625}`
- Metric errors: `{}`

### PART1_0006
- Sheet: `Part1`
- Video: `Abuse038_x264`
- Question: Animals fell on the road after a vehicle passed, while pedestrians were chatting nearby.
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 0.5833, "context_recall": 0.5}`
- Generation: `{"factual_correctness": 1.0, "faithfulness": 0.0}`
- Temporal: `{"time_range_overlap_iou": 0.0, "temporal_iou": 0.0, "eligible": true, "video_match": true}`
- End-to-end: `{"ragas_e2e_score": 0.5208}`
- Metric errors: `{}`

### PART1_0007
- Sheet: `Part1`
- Video: `Abuse038_x264`
- Question: A car with its lights on stopped, and the headlights shone on something on the road ahead.
- Route mode: `pure_sql`
- Top hit: `True`
- Retrieval: `{"context_precision": 1.0, "context_recall": 0.0}`
- Generation: `{"factual_correctness": 0.5, "faithfulness": 0.5}`
- Temporal: `{"time_range_overlap_iou": 0.8333, "temporal_iou": 0.8333, "eligible": true, "video_match": true}`
- End-to-end: `{"ragas_e2e_score": 0.5}`
- Metric errors: `{}`

### PART1_0008
- Sheet: `Part1`
- Video: `Abuse039_x264`
- Question: Is there a video of two staff members conducting a full-body search on a detained woman in a closed room?
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 0.0, "context_recall": 0.0}`
- Generation: `{"factual_correctness": 0.5, "faithfulness": 0.0}`
- Temporal: `{"time_range_overlap_iou": 0.0, "temporal_iou": 0.0, "eligible": true, "video_match": true}`
- End-to-end: `{"ragas_e2e_score": 0.125}`
- Metric errors: `{}`

### PART1_0009
- Sheet: `Part1`
- Video: `Abuse039_x264`
- Question: A woman was repeatedly told to turn around and face the wall in a closed room, and was forced to undress.
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 0.5833, "context_recall": 0.5}`
- Generation: `{"factual_correctness": 1.0, "faithfulness": 0.0}`
- Temporal: `{"time_range_overlap_iou": 0.0173, "temporal_iou": 0.0173, "eligible": true, "video_match": true}`
- End-to-end: `{"ragas_e2e_score": 0.5208}`
- Metric errors: `{}`

### PART1_0010
- Sheet: `Part1`
- Video: `Abuse039_x264`
- Question: A person used a handheld device to scan another person top to bottom, then someone took shoes from a conveyor belt.
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 0.0, "context_recall": 0.0}`
- Generation: `{"factual_correctness": 0.0, "faithfulness": 0.5}`
- Temporal: `{"time_range_overlap_iou": 0.0, "temporal_iou": 0.0, "eligible": true, "video_match": true}`
- End-to-end: `{"ragas_e2e_score": 0.125}`
- Metric errors: `{}`

### PART1_0011
- Sheet: `Part1`
- Video: `Abuse040_x264`
- Question: Is there a clip of a caregiver repeatedly hitting a white-haired elderly person on the head while they sit on a sofa?
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 0.3333, "context_recall": 0.5}`
- Generation: `{"factual_correctness": 0.0, "faithfulness": 0.0}`
- Temporal: `{"time_range_overlap_iou": null, "temporal_iou": null, "eligible": false, "video_match": null}`
- End-to-end: `{"ragas_e2e_score": 0.2083}`
- Metric errors: `{}`
