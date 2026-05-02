# RAGAS Eval Report

## Summary
- Case count: `50`
- Success count: `50`
- Top hit rate: `0.9`
- Avg latency ms: `10386.75`

## Retrieval
- Context precision avg: `0.3567`
- Context recall avg: `0.23`

## Generation
- Faithfulness avg: `nan`
- Factual correctness avg: `0.49`

## Temporal Localization
- Time overlap IoU avg: `0.1333`
- Time overlap case count: `8`
- Time overlap hit@0.3: `0.125`
- Time overlap hit@0.5: `0.125`

## End To End
- RAGAS e2e avg: `nan`

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
- Generation: `{"factual_correctness": 0.0, "faithfulness": 0.5}`
- Temporal: `{"time_range_overlap_iou": 0.0, "temporal_iou": 0.0, "eligible": true, "video_match": false}`
- End-to-end: `{"ragas_e2e_score": 0.25}`
- Metric errors: `{}`

### PART1_0004
- Sheet: `Part1`
- Video: `Abuse037_x264`
- Question: An animal bent down to pull the tail of a motionless object on the ground, then left after a moment.
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 0.0, "context_recall": 0.0}`
- Generation: `{"factual_correctness": 1.0, "faithfulness": 0.5}`
- Temporal: `{"time_range_overlap_iou": null, "temporal_iou": null, "eligible": false, "video_match": null}`
- End-to-end: `{"ragas_e2e_score": 0.375}`
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
- Retrieval: `{"context_precision": 0.5, "context_recall": 0.5}`
- Generation: `{"factual_correctness": 1.0, "faithfulness": 0.0}`
- Temporal: `{"time_range_overlap_iou": 0.0, "temporal_iou": 0.0, "eligible": true, "video_match": true}`
- End-to-end: `{"ragas_e2e_score": 0.5}`
- Metric errors: `{}`

### PART1_0007
- Sheet: `Part1`
- Video: `Abuse038_x264`
- Question: A car with its lights on stopped, and the headlights shone on something on the road ahead.
- Route mode: `pure_sql`
- Top hit: `True`
- Retrieval: `{"context_precision": 1.0, "context_recall": 1.0}`
- Generation: `{"factual_correctness": 1.0, "faithfulness": 0.5}`
- Temporal: `{"time_range_overlap_iou": 0.8333, "temporal_iou": 0.8333, "eligible": true, "video_match": true}`
- End-to-end: `{"ragas_e2e_score": 0.875}`
- Metric errors: `{}`

### PART1_0008
- Sheet: `Part1`
- Video: `Abuse039_x264`
- Question: Is there a video of two staff members conducting a full-body search on a detained woman in a closed room?
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 0.0, "context_recall": 0.0}`
- Generation: `{"factual_correctness": 0.0, "faithfulness": 1.0}`
- Temporal: `{"time_range_overlap_iou": 0.0, "temporal_iou": 0.0, "eligible": true, "video_match": true}`
- End-to-end: `{"ragas_e2e_score": 0.25}`
- Metric errors: `{}`

### PART1_0009
- Sheet: `Part1`
- Video: `Abuse039_x264`
- Question: A woman was repeatedly told to turn around and face the wall in a closed room, and was forced to undress.
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 0.3333, "context_recall": 0.5}`
- Generation: `{"factual_correctness": 1.0, "faithfulness": 0.0}`
- Temporal: `{"time_range_overlap_iou": 0.0173, "temporal_iou": 0.0173, "eligible": true, "video_match": true}`
- End-to-end: `{"ragas_e2e_score": 0.4583}`
- Metric errors: `{}`

### PART1_0010
- Sheet: `Part1`
- Video: `Abuse039_x264`
- Question: A person used a handheld device to scan another person top to bottom, then someone took shoes from a conveyor belt.
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 0.0, "context_recall": 0.0}`
- Generation: `{"factual_correctness": 0.5, "faithfulness": 0.0}`
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
- Generation: `{"factual_correctness": 0.5, "faithfulness": 0.5}`
- Temporal: `{"time_range_overlap_iou": null, "temporal_iou": null, "eligible": false, "video_match": null}`
- End-to-end: `{"ragas_e2e_score": 0.4583}`
- Metric errors: `{}`

### PART1_0012
- Sheet: `Part1`
- Video: `Abuse040_x264`
- Question: A person pushed a wheelchair next to a seated elderly person but also used violence against them.
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 0.3333, "context_recall": 0.5}`
- Generation: `{"factual_correctness": 0.5, "faithfulness": 0.5}`
- Temporal: `{"time_range_overlap_iou": null, "temporal_iou": null, "eligible": false, "video_match": null}`
- End-to-end: `{"ragas_e2e_score": 0.4583}`
- Metric errors: `{}`

### PART1_0013
- Sheet: `Part1`
- Video: `Abuse040_x264`
- Question: After entering the room, the person turned off the light, then moved a piece of furniture next to a seated person.
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 0.0, "context_recall": 0.0}`
- Generation: `{"factual_correctness": 0.0, "faithfulness": 0.0}`
- Temporal: `{"time_range_overlap_iou": null, "temporal_iou": null, "eligible": false, "video_match": null}`
- End-to-end: `{"ragas_e2e_score": 0.0}`
- Metric errors: `{}`

### PART1_0014
- Sheet: `Part1`
- Video: `Abuse041_x264`
- Question: Is there indoor surveillance of multiple children sitting at green tables with an adult woman nearby?
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 1.0, "context_recall": 0.5}`
- Generation: `{"factual_correctness": 0.5, "faithfulness": 0.75}`
- Temporal: `{"time_range_overlap_iou": null, "temporal_iou": null, "eligible": false, "video_match": null}`
- End-to-end: `{"ragas_e2e_score": 0.6875}`
- Metric errors: `{}`

### PART1_0015
- Sheet: `Part1`
- Video: `Abuse041_x264`
- Question: A woman moved around alone in a closed space with multiple children, occasionally crouching to clean the floor.
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 0.0, "context_recall": 0.5}`
- Generation: `{"factual_correctness": 1.0, "faithfulness": 0.5}`
- Temporal: `{"time_range_overlap_iou": null, "temporal_iou": null, "eligible": false, "video_match": null}`
- End-to-end: `{"ragas_e2e_score": 0.5}`
- Metric errors: `{}`

### PART1_0016
- Sheet: `Part1`
- Video: `Abuse041_x264`
- Question: A woman held a child with one hand and pulled out a green object from under the table with the other.
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 0.0, "context_recall": 0.0}`
- Generation: `{"factual_correctness": 0.5, "faithfulness": 0.5}`
- Temporal: `{"time_range_overlap_iou": null, "temporal_iou": null, "eligible": false, "video_match": null}`
- End-to-end: `{"ragas_e2e_score": 0.25}`
- Metric errors: `{}`

### PART1_0017
- Sheet: `Part1`
- Video: `Abuse042_x264`
- Question: Is there a video of a woman feeding a baby on the floor and forcefully pushing the baby at some point?
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 1.0, "context_recall": 0.5}`
- Generation: `{"factual_correctness": 0.5, "faithfulness": 0.5}`
- Temporal: `{"time_range_overlap_iou": null, "temporal_iou": null, "eligible": false, "video_match": null}`
- End-to-end: `{"ragas_e2e_score": 0.625}`
- Metric errors: `{}`

### PART1_0018
- Sheet: `Part1`
- Video: `Abuse042_x264`
- Question: A baby lay alone on the floor for a long time while the caregiver was away.
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 0.0, "context_recall": 0.0}`
- Generation: `{"factual_correctness": 0.0, "faithfulness": 0.0}`
- Temporal: `{"time_range_overlap_iou": null, "temporal_iou": null, "eligible": false, "video_match": null}`
- End-to-end: `{"ragas_e2e_score": 0.0}`
- Metric errors: `{}`

### PART1_0019
- Sheet: `Part1`
- Video: `Abuse042_x264`
- Question: A woman talked on the phone while continuously patting the back of a baby lying beside her with her other hand.
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 0.8333, "context_recall": 0.0}`
- Generation: `{"factual_correctness": 0.5, "faithfulness": 0.0}`
- Temporal: `{"time_range_overlap_iou": null, "temporal_iou": null, "eligible": false, "video_match": null}`
- End-to-end: `{"ragas_e2e_score": 0.3333}`
- Metric errors: `{}`

### PART1_0020
- Sheet: `Part1`
- Video: `Arrest043_x264`
- Question: Is there a clip of a police officer stomping on and beating a person lying on the ground in a yard?
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 0.0, "context_recall": 0.0}`
- Generation: `{"factual_correctness": 0.5, "faithfulness": 0.3333}`
- Temporal: `{"time_range_overlap_iou": null, "temporal_iou": null, "eligible": false, "video_match": null}`
- End-to-end: `{"ragas_e2e_score": 0.2083}`
- Metric errors: `{}`

### PART1_0021
- Sheet: `Part1`
- Video: `Arrest043_x264`
- Question: Law enforcement was present, but one officer inflicted physical harm beyond normal procedure on a restrained person.
- Route mode: `hybrid_search`
- Top hit: `False`
- Retrieval: `{"context_precision": 0.0, "context_recall": 0.0}`
- Generation: `{"factual_correctness": 0.0, "faithfulness": NaN}`
- Temporal: `{"time_range_overlap_iou": null, "temporal_iou": null, "eligible": false, "video_match": null}`
- End-to-end: `{"ragas_e2e_score": NaN}`
- Metric errors: `{}`

### PART1_0022
- Sheet: `Part1`
- Video: `Arrest043_x264`
- Question: A person wearing a yellow hat stood on top of another person for an extended time, continuously making hand movements on them.
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 1.0, "context_recall": 0.0}`
- Generation: `{"factual_correctness": 0.5, "faithfulness": 0.5}`
- Temporal: `{"time_range_overlap_iou": null, "temporal_iou": null, "eligible": false, "video_match": null}`
- End-to-end: `{"ragas_e2e_score": 0.5}`
- Metric errors: `{}`

### PART1_0023
- Sheet: `Part1`
- Video: `Arrest044_x264`
- Question: Is there a surveillance video of multiple officers going up indoor stairs and entering a room one after another?
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 0.0, "context_recall": 0.0}`
- Generation: `{"factual_correctness": 0.0, "faithfulness": 1.0}`
- Temporal: `{"time_range_overlap_iou": null, "temporal_iou": null, "eligible": false, "video_match": null}`
- End-to-end: `{"ragas_e2e_score": 0.25}`
- Metric errors: `{}`

### PART1_0024
- Sheet: `Part1`
- Video: `Arrest044_x264`
- Question: Several uniformed officers entered a house and shortly after brought a person down from upstairs and left.
- Route mode: `hybrid_search`
- Top hit: `False`
- Retrieval: `{"context_precision": 0.0, "context_recall": 0.0}`
- Generation: `{"factual_correctness": 0.0, "faithfulness": NaN}`
- Temporal: `{"time_range_overlap_iou": null, "temporal_iou": null, "eligible": false, "video_match": null}`
- End-to-end: `{"ragas_e2e_score": NaN}`
- Metric errors: `{}`

### PART1_0025
- Sheet: `Part1`
- Video: `Arrest044_x264`
- Question: A white animal jumped onto a sofa while multiple people were moving around indoors.
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 0.0, "context_recall": 0.5}`
- Generation: `{"factual_correctness": 1.0, "faithfulness": 0.5}`
- Temporal: `{"time_range_overlap_iou": null, "temporal_iou": null, "eligible": false, "video_match": null}`
- End-to-end: `{"ragas_e2e_score": 0.5}`
- Metric errors: `{}`

### PART1_0026
- Sheet: `Part1`
- Video: `Arrest046_x264`
- Question: Is there an indoor video of police searching a handcuffed person and placing items on a table one by one?
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 1.0, "context_recall": 0.5}`
- Generation: `{"factual_correctness": 0.5, "faithfulness": 0.5}`
- Temporal: `{"time_range_overlap_iou": null, "temporal_iou": null, "eligible": false, "video_match": null}`
- End-to-end: `{"ragas_e2e_score": 0.625}`
- Metric errors: `{}`

### PART1_0027
- Sheet: `Part1`
- Video: `Arrest046_x264`
- Question: A restrained person was forced to remove shoes and socks, which were then inspected and set aside by another.
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 0.0, "context_recall": 0.0}`
- Generation: `{"factual_correctness": 0.5, "faithfulness": 0.0}`
- Temporal: `{"time_range_overlap_iou": null, "temporal_iou": null, "eligible": false, "video_match": null}`
- End-to-end: `{"ragas_e2e_score": 0.125}`
- Metric errors: `{}`

### PART1_0028
- Sheet: `Part1`
- Video: `Arrest046_x264`
- Question: A person wearing purple gloves looked down at items in their hands while another person stood against the wall.
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 1.0, "context_recall": 0.5}`
- Generation: `{"factual_correctness": 0.5, "faithfulness": 0.5}`
- Temporal: `{"time_range_overlap_iou": null, "temporal_iou": null, "eligible": false, "video_match": null}`
- End-to-end: `{"ragas_e2e_score": 0.625}`
- Metric errors: `{}`

### PART1_0029
- Sheet: `Part1`
- Video: `Arrest048_x264`
- Question: Is there a video of multiple officers physically clashing with people inside a supermarket and handcuffing them?
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 0.3333, "context_recall": 0.5}`
- Generation: `{"factual_correctness": 0.5, "faithfulness": 0.5}`
- Temporal: `{"time_range_overlap_iou": null, "temporal_iou": null, "eligible": false, "video_match": null}`
- End-to-end: `{"ragas_e2e_score": 0.4583}`
- Metric errors: `{}`

### PART1_0030
- Sheet: `Part1`
- Video: `Arrest048_x264`
- Question: Officers and civilians scuffled inside a store; two men were separately handcuffed and taken away.
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 0.0, "context_recall": 0.0}`
- Generation: `{"factual_correctness": 0.0, "faithfulness": 1.0}`
- Temporal: `{"time_range_overlap_iou": null, "temporal_iou": null, "eligible": false, "video_match": null}`
- End-to-end: `{"ragas_e2e_score": 0.25}`
- Metric errors: `{}`

### PART1_0031
- Sheet: `Part1`
- Video: `Arrest048_x264`
- Question: A female officer rushed into the chaotic scene; before that, someone had left the store carrying a drink.
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 0.0, "context_recall": 0.0}`
- Generation: `{"factual_correctness": 0.0, "faithfulness": 0.0}`
- Temporal: `{"time_range_overlap_iou": null, "temporal_iou": null, "eligible": false, "video_match": null}`
- End-to-end: `{"ragas_e2e_score": 0.0}`
- Metric errors: `{}`

### PART1_0032
- Sheet: `Part1`
- Video: `Arrest049_x264`
- Question: Is there a video of police stopping a cyclist at the roadside, searching them, and handcuffing them into a police car?
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 0.0, "context_recall": 0.5}`
- Generation: `{"factual_correctness": 0.5, "faithfulness": 0.0}`
- Temporal: `{"time_range_overlap_iou": null, "temporal_iou": null, "eligible": false, "video_match": null}`
- End-to-end: `{"ragas_e2e_score": 0.25}`
- Metric errors: `{}`

### PART1_0033
- Sheet: `Part1`
- Video: `Arrest049_x264`
- Question: The person being searched tried to run toward the road to escape, was tackled to the ground, and had their clothes torn.
- Route mode: `hybrid_search`
- Top hit: `False`
- Retrieval: `{"context_precision": 0.0, "context_recall": 0.0}`
- Generation: `{"factual_correctness": 0.0, "faithfulness": NaN}`
- Temporal: `{"time_range_overlap_iou": null, "temporal_iou": null, "eligible": false, "video_match": null}`
- End-to-end: `{"ragas_e2e_score": NaN}`
- Metric errors: `{}`

### PART1_0034
- Sheet: `Part1`
- Video: `Arrest049_x264`
- Question: A blonde woman stood watching the entire time without taking part in any physical action.
- Route mode: `hybrid_search`
- Top hit: `False`
- Retrieval: `{"context_precision": 0.0, "context_recall": 0.0}`
- Generation: `{"factual_correctness": 0.0, "faithfulness": 0.0}`
- Temporal: `{"time_range_overlap_iou": null, "temporal_iou": null, "eligible": false, "video_match": null}`
- End-to-end: `{"ragas_e2e_score": 0.0}`
- Metric errors: `{}`

### PART1_0035
- Sheet: `Part1`
- Video: `Arrest050_x264`
- Question: Is there a video of a police car chasing a sedan that eventually crashed into a roadside building?
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 0.5, "context_recall": 0.5}`
- Generation: `{"factual_correctness": 0.5, "faithfulness": 0.25}`
- Temporal: `{"time_range_overlap_iou": null, "temporal_iou": null, "eligible": false, "video_match": null}`
- End-to-end: `{"ragas_e2e_score": 0.4375}`
- Metric errors: `{}`

### PART1_0036
- Sheet: `Part1`
- Video: `Arrest050_x264`
- Question: After a car crashed into a building, multiple police cars pulled over and a large crowd gathered at the scene.
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 0.0, "context_recall": 0.0}`
- Generation: `{"factual_correctness": 1.0, "faithfulness": 0.0}`
- Temporal: `{"time_range_overlap_iou": null, "temporal_iou": null, "eligible": false, "video_match": null}`
- End-to-end: `{"ragas_e2e_score": 0.25}`
- Metric errors: `{}`

### PART1_0037
- Sheet: `Part1`
- Video: `Arrest050_x264`
- Question: Two white and one black vehicle were parked by the road, all three with flashing roof lights.
- Route mode: `pure_sql`
- Top hit: `True`
- Retrieval: `{"context_precision": 0.0, "context_recall": 0.0}`
- Generation: `{"factual_correctness": 0.5, "faithfulness": 0.25}`
- Temporal: `{"time_range_overlap_iou": null, "temporal_iou": null, "eligible": false, "video_match": null}`
- End-to-end: `{"ragas_e2e_score": 0.1875}`
- Metric errors: `{}`

### PART1_0038
- Sheet: `Part1`
- Video: `Arrest051_x264`
- Question: Is there street surveillance of police pushing two men to the ground and handcuffing them separately?
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 0.0, "context_recall": 0.0}`
- Generation: `{"factual_correctness": 0.0, "faithfulness": 1.0}`
- Temporal: `{"time_range_overlap_iou": null, "temporal_iou": null, "eligible": false, "video_match": null}`
- End-to-end: `{"ragas_e2e_score": 0.25}`
- Metric errors: `{}`

### PART1_0039
- Sheet: `Part1`
- Video: `Arrest051_x264`
- Question: Near an intersection, a man tried to intervene in police action and was subsequently subdued.
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 0.0, "context_recall": 0.5}`
- Generation: `{"factual_correctness": 1.0, "faithfulness": 0.5}`
- Temporal: `{"time_range_overlap_iou": null, "temporal_iou": null, "eligible": false, "video_match": null}`
- End-to-end: `{"ragas_e2e_score": 0.5}`
- Metric errors: `{}`

### PART1_0040
- Sheet: `Part1`
- Video: `Arrest051_x264`
- Question: A man on a tricycle passed by the scene without stopping.
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 0.0, "context_recall": 0.0}`
- Generation: `{"factual_correctness": 1.0, "faithfulness": 0.0}`
- Temporal: `{"time_range_overlap_iou": null, "temporal_iou": null, "eligible": false, "video_match": null}`
- End-to-end: `{"ragas_e2e_score": 0.25}`
- Metric errors: `{}`

### PART1_0041
- Sheet: `Part1`
- Video: `Arson020_x264`
- Question: Is there a video of someone smashing a parked car's windshield and throwing a fire source inside to ignite it?
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 1.0, "context_recall": 0.5}`
- Generation: `{"factual_correctness": 0.5, "faithfulness": 0.75}`
- Temporal: `{"time_range_overlap_iou": null, "temporal_iou": null, "eligible": false, "video_match": null}`
- End-to-end: `{"ragas_e2e_score": 0.6875}`
- Metric errors: `{}`

### PART1_0042
- Sheet: `Part1`
- Video: `Arson020_x264`
- Question: Two people got out of a car and then damaged a nearby parked vehicle, causing it to catch fire.
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 0.8333, "context_recall": 0.5}`
- Generation: `{"factual_correctness": 0.5, "faithfulness": 0.5}`
- Temporal: `{"time_range_overlap_iou": null, "temporal_iou": null, "eligible": false, "video_match": null}`
- End-to-end: `{"ragas_e2e_score": 0.5833}`
- Metric errors: `{}`

### PART1_0043
- Sheet: `Part1`
- Video: `Arson020_x264`
- Question: Two cars were parked by the road; two people got out of one and walked toward the other.
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 0.0, "context_recall": 0.0}`
- Generation: `{"factual_correctness": 1.0, "faithfulness": 0.0}`
- Temporal: `{"time_range_overlap_iou": null, "temporal_iou": null, "eligible": false, "video_match": null}`
- End-to-end: `{"ragas_e2e_score": 0.25}`
- Metric errors: `{}`

### PART1_0044
- Sheet: `Part1`
- Video: `Arson021_x264`
- Question: Is there a video of a cyclist setting fire at a building entrance and then riding away?
- Route mode: `hybrid_search`
- Top hit: `False`
- Retrieval: `{"context_precision": 0.0, "context_recall": 0.0}`
- Generation: `{"factual_correctness": 0.0, "faithfulness": 1.0}`
- Temporal: `{"time_range_overlap_iou": null, "temporal_iou": null, "eligible": false, "video_match": null}`
- End-to-end: `{"ragas_e2e_score": 0.25}`
- Metric errors: `{}`

### PART1_0045
- Sheet: `Part1`
- Video: `Arson021_x264`
- Question: A cyclist briefly stopped at a door, made hand movements, then the door began to burn.
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 1.0, "context_recall": 0.0}`
- Generation: `{"factual_correctness": 0.5, "faithfulness": 0.5}`
- Temporal: `{"time_range_overlap_iou": null, "temporal_iou": null, "eligible": false, "video_match": null}`
- End-to-end: `{"ragas_e2e_score": 0.5}`
- Metric errors: `{}`

### PART1_0046
- Sheet: `Part1`
- Video: `Arson021_x264`
- Question: A man spent less than 30 seconds at the door, made some movements against it, then quickly rode away.
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 1.0, "context_recall": 0.0}`
- Generation: `{"factual_correctness": 1.0, "faithfulness": 0.5}`
- Temporal: `{"time_range_overlap_iou": null, "temporal_iou": null, "eligible": false, "video_match": null}`
- End-to-end: `{"ragas_e2e_score": 0.625}`
- Metric errors: `{}`

### PART1_0047
- Sheet: `Part1`
- Video: `Arson022_x264`
- Question: Is there a video of someone repeatedly trying to light a Christmas tree indoors, succeeding, then leaving?
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 1.0, "context_recall": 0.5}`
- Generation: `{"factual_correctness": 1.0, "faithfulness": 0.4}`
- Temporal: `{"time_range_overlap_iou": null, "temporal_iou": null, "eligible": false, "video_match": null}`
- End-to-end: `{"ragas_e2e_score": 0.725}`
- Metric errors: `{}`

### PART1_0048
- Sheet: `Part1`
- Video: `Arson022_x264`
- Question: Inside a closed space, a person failed multiple times at the same action and finally succeeded before leaving the way they came.
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 0.0, "context_recall": 0.0}`
- Generation: `{"factual_correctness": 0.0, "faithfulness": 0.5}`
- Temporal: `{"time_range_overlap_iou": null, "temporal_iou": null, "eligible": false, "video_match": null}`
- End-to-end: `{"ragas_e2e_score": 0.125}`
- Metric errors: `{}`

### PART1_0049
- Sheet: `Part1`
- Video: `Arson022_x264`
- Question: A man searched through items on a white shelf and placed something he found onto a nearby decorative object.
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 1.0, "context_recall": 0.0}`
- Generation: `{"factual_correctness": 0.5, "faithfulness": 0.5}`
- Temporal: `{"time_range_overlap_iou": null, "temporal_iou": null, "eligible": false, "video_match": null}`
- End-to-end: `{"ragas_e2e_score": 0.5}`
- Metric errors: `{}`

### PART1_0050
- Sheet: `Part1`
- Video: `Arson023_x264`
- Question: Is there a video of someone pouring gasoline on a white car and setting it on fire?
- Route mode: `pure_sql`
- Top hit: `True`
- Retrieval: `{"context_precision": 0.0, "context_recall": 0.0}`
- Generation: `{"factual_correctness": 0.5, "faithfulness": 0.3333}`
- Temporal: `{"time_range_overlap_iou": null, "temporal_iou": null, "eligible": false, "video_match": null}`
- End-to-end: `{"ragas_e2e_score": 0.2083}`
- Metric errors: `{}`

### PART1_0051
- Sheet: `Part1`
- Video: `Arson023_x264`
- Question: A man applied a liquid around a parked car, which then caught fire.
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 0.8333, "context_recall": 0.5}`
- Generation: `{"factual_correctness": 0.5, "faithfulness": 0.5}`
- Temporal: `{"time_range_overlap_iou": null, "temporal_iou": null, "eligible": false, "video_match": null}`
- End-to-end: `{"ragas_e2e_score": 0.5833}`
- Metric errors: `{}`
