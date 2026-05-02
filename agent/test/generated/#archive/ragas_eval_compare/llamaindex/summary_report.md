# RAGAS Eval Report

## Summary
- Case count: `20`
- Success count: `20`
- Top hit rate: `0.75`
- Avg latency ms: `16297.94`

## Retrieval
- Context precision avg: `0.5833`
- Context recall avg: `0.5`

## Generation
- Faithfulness avg: `0.2005`
- Answer relevancy avg: `0.2838`
- Factual correctness avg: `0.0`

## End To End
- RAGAS e2e avg: `0.2214`

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
- Top hit: `False`
- Retrieval: `{"context_precision": null, "context_recall": null}`
- Generation: `{"answer_relevancy": 0.0, "factual_correctness": 0.0, "faithfulness": null}`
- End-to-end: `{"ragas_e2e_score": 0.0}`
- Metric errors: `{}`

### PART1_0004
- Sheet: `Part1`
- Video: `Abuse037_x264`
- Question: An animal bent down to pull the tail of a motionless object on the ground, then left after a moment.
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 0.0, "context_recall": 0.0}`
- Generation: `{"answer_relevancy": 0.2881, "factual_correctness": 0.0, "faithfulness": 0.2}`
- End-to-end: `{"ragas_e2e_score": 0.0976}`
- Metric errors: `{}`

### PART1_0005
- Sheet: `Part1`
- Video: `Abuse038_x264`
- Question: Is there a clip of two puppies being hit by a car and rolling on the road?
- Route mode: `pure_sql`
- Top hit: `False`
- Retrieval: `{"context_precision": null, "context_recall": null}`
- Generation: `{"answer_relevancy": 0.0, "factual_correctness": 0.0, "faithfulness": null}`
- End-to-end: `{"ragas_e2e_score": 0.0}`
- Metric errors: `{}`

### PART1_0006
- Sheet: `Part1`
- Video: `Abuse038_x264`
- Question: Animals fell on the road after a vehicle passed, while pedestrians were chatting nearby.
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 1.0, "context_recall": 1.0}`
- Generation: `{"answer_relevancy": 0.3283, "factual_correctness": 0.0, "faithfulness": 0.4444}`
- End-to-end: `{"ragas_e2e_score": 0.5545}`
- Metric errors: `{}`

### PART1_0007
- Sheet: `Part1`
- Video: `Abuse038_x264`
- Question: A car with its lights on stopped, and the headlights shone on something on the road ahead.
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 1.0, "context_recall": 1.0}`
- Generation: `{"answer_relevancy": 0.3599, "factual_correctness": 0.0, "faithfulness": null}`
- End-to-end: `{"ragas_e2e_score": 0.59}`
- Metric errors: `{"faithfulness": "<failed_attempts>\n\n<generation number=\"1\">\n<exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 29322, Requested 1572. Please try again in 1.788s. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</exception>\n<completion>\n    None\n</completion>\n</generation>\n\n<generation number=\"2\">\n<exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 29462, Requested 1572. Please try again in 2.068s. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</exception>\n<completion>\n    None\n</completion>\n</generation>\n\n<generation number=\"3\">\n<exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 28936, Requested 1572. Please try again in 1.016s. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</exception>\n<completion>\n    None\n</completion>\n</generation>\n\n</failed_attempts>\n\n<last_exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 28936, Requested 1572. Please try again in 1.016s. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</last_exception>"}`

### PART1_0008
- Sheet: `Part1`
- Video: `Abuse039_x264`
- Question: Is there a video of two staff members conducting a full-body search on a detained woman in a closed room?
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 0.0, "context_recall": 0.0}`
- Generation: `{"answer_relevancy": 0.4207, "factual_correctness": 0.0, "faithfulness": null}`
- End-to-end: `{"ragas_e2e_score": 0.1052}`
- Metric errors: `{"faithfulness": "<failed_attempts>\n\n<generation number=\"1\">\n<exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 29171, Requested 1605. Please try again in 1.552s. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</exception>\n<completion>\n    None\n</completion>\n</generation>\n\n<generation number=\"2\">\n<exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 29244, Requested 1605. Please try again in 1.698s. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</exception>\n<completion>\n    None\n</completion>\n</generation>\n\n<generation number=\"3\">\n<exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 29648, Requested 1605. Please try again in 2.506s. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</exception>\n<completion>\n    None\n</completion>\n</generation>\n\n</failed_attempts>\n\n<last_exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 29648, Requested 1605. Please try again in 2.506s. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</last_exception>"}`

### PART1_0009
- Sheet: `Part1`
- Video: `Abuse039_x264`
- Question: A woman was repeatedly told to turn around and face the wall in a closed room, and was forced to undress.
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 0.0, "context_recall": null}`
- Generation: `{"answer_relevancy": 0.3195, "factual_correctness": 0.0, "faithfulness": 0.2857}`
- End-to-end: `{"ragas_e2e_score": 0.1513}`
- Metric errors: `{"context_recall": "<failed_attempts>\n\n<generation number=\"1\">\n<exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 30000, Requested 2183. Please try again in 4.366s. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</exception>\n<completion>\n    None\n</completion>\n</generation>\n\n<generation number=\"2\">\n<exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 29202, Requested 2183. Please try again in 2.77s. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</exception>\n<completion>\n    None\n</completion>\n</generation>\n\n<generation number=\"3\">\n<exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 28823, Requested 2183. Please try again in 2.012s. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</exception>\n<completion>\n    None\n</completion>\n</generation>\n\n</failed_attempts>\n\n<last_exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 28823, Requested 2183. Please try again in 2.012s. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</last_exception>"}`

### PART1_0010
- Sheet: `Part1`
- Video: `Abuse039_x264`
- Question: A person used a handheld device to scan another person top to bottom, then someone took shoes from a conveyor belt.
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": null, "context_recall": null}`
- Generation: `{"answer_relevancy": 0.2446, "factual_correctness": 0.0, "faithfulness": 0.0}`
- End-to-end: `{"ragas_e2e_score": 0.0815}`
- Metric errors: `{"context_precision": "<failed_attempts>\n\n<generation number=\"1\">\n<exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 29007, Requested 1386. Please try again in 786ms. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</exception>\n<completion>\n    None\n</completion>\n</generation>\n\n<generation number=\"2\">\n<exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 29103, Requested 1386. Please try again in 977ms. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</exception>\n<completion>\n    None\n</completion>\n</generation>\n\n<generation number=\"3\">\n<exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 29105, Requested 1386. Please try again in 982ms. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</exception>\n<completion>\n    None\n</completion>\n</generation>\n\n</failed_attempts>\n\n<last_exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 29105, Requested 1386. Please try again in 982ms. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</last_exception>", "context_recall": "<failed_attempts>\n\n<generation number=\"1\">\n<exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 28704, Requested 2185. Please try again in 1.778s. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</exception>\n<completion>\n    None\n</completion>\n</generation>\n\n<generation number=\"2\">\n<exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 29493, Requested 2185. Please try again in 3.356s. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</exception>\n<completion>\n    None\n</completion>\n</generation>\n\n<generation number=\"3\">\n<exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 30000, Requested 2185. Please try again in 4.37s. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</exception>\n<completion>\n    None\n</completion>\n</generation>\n\n</failed_attempts>\n\n<last_exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 30000, Requested 2185. Please try again in 4.37s. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</last_exception>"}`

### PART1_0011
- Sheet: `Part1`
- Video: `Abuse040_x264`
- Question: Is there a clip of a caregiver repeatedly hitting a white-haired elderly person on the head while they sit on a sofa?
- Route mode: `hybrid_search`
- Top hit: `False`
- Retrieval: `{"context_precision": null, "context_recall": null}`
- Generation: `{"answer_relevancy": 0.0, "factual_correctness": 0.0, "faithfulness": null}`
- End-to-end: `{"ragas_e2e_score": 0.0}`
- Metric errors: `{}`

### PART1_0012
- Sheet: `Part1`
- Video: `Abuse040_x264`
- Question: A person pushed a wheelchair next to a seated elderly person but also used violence against them.
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 0.0, "context_recall": null}`
- Generation: `{"answer_relevancy": 0.3564, "factual_correctness": 0.0, "faithfulness": 0.0}`
- End-to-end: `{"ragas_e2e_score": 0.0891}`
- Metric errors: `{"context_recall": "<failed_attempts>\n\n<generation number=\"1\">\n<exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 28283, Requested 2174. Please try again in 914ms. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</exception>\n<completion>\n    None\n</completion>\n</generation>\n\n<generation number=\"2\">\n<exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 29149, Requested 2174. Please try again in 2.646s. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</exception>\n<completion>\n    None\n</completion>\n</generation>\n\n<generation number=\"3\">\n<exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 28288, Requested 2174. Please try again in 924ms. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</exception>\n<completion>\n    None\n</completion>\n</generation>\n\n</failed_attempts>\n\n<last_exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 28288, Requested 2174. Please try again in 924ms. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</last_exception>"}`

### PART1_0013
- Sheet: `Part1`
- Video: `Abuse040_x264`
- Question: After entering the room, the person turned off the light, then moved a piece of furniture next to a seated person.
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 1.0, "context_recall": null}`
- Generation: `{"answer_relevancy": 0.1439, "factual_correctness": 0.0, "faithfulness": null}`
- End-to-end: `{"ragas_e2e_score": 0.3813}`
- Metric errors: `{"context_recall": "<failed_attempts>\n\n<generation number=\"1\">\n<exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 28494, Requested 2179. Please try again in 1.346s. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</exception>\n<completion>\n    None\n</completion>\n</generation>\n\n<generation number=\"2\">\n<exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 30000, Requested 2179. Please try again in 4.358s. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</exception>\n<completion>\n    None\n</completion>\n</generation>\n\n<generation number=\"3\">\n<exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 29288, Requested 2179. Please try again in 2.934s. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</exception>\n<completion>\n    None\n</completion>\n</generation>\n\n</failed_attempts>\n\n<last_exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 29288, Requested 2179. Please try again in 2.934s. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</last_exception>", "faithfulness": "<failed_attempts>\n\n<generation number=\"1\">\n<exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 30000, Requested 1576. Please try again in 3.152s. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</exception>\n<completion>\n    None\n</completion>\n</generation>\n\n<generation number=\"2\">\n<exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 29476, Requested 1576. Please try again in 2.104s. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</exception>\n<completion>\n    None\n</completion>\n</generation>\n\n<generation number=\"3\">\n<exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 28480, Requested 1576. Please try again in 112ms. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</exception>\n<completion>\n    None\n</completion>\n</generation>\n\n</failed_attempts>\n\n<last_exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 28480, Requested 1576. Please try again in 112ms. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</last_exception>"}`

### PART1_0014
- Sheet: `Part1`
- Video: `Abuse041_x264`
- Question: Is there indoor surveillance of multiple children sitting at green tables with an adult woman nearby?
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 1.0, "context_recall": null}`
- Generation: `{"answer_relevancy": 0.7955, "factual_correctness": 0.0, "faithfulness": null}`
- End-to-end: `{"ragas_e2e_score": 0.5985}`
- Metric errors: `{"context_recall": "<failed_attempts>\n\n<generation number=\"1\">\n<exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 30000, Requested 2175. Please try again in 4.35s. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</exception>\n<completion>\n    None\n</completion>\n</generation>\n\n<generation number=\"2\">\n<exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 30000, Requested 2175. Please try again in 4.35s. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</exception>\n<completion>\n    None\n</completion>\n</generation>\n\n<generation number=\"3\">\n<exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 29906, Requested 2175. Please try again in 4.162s. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</exception>\n<completion>\n    None\n</completion>\n</generation>\n\n</failed_attempts>\n\n<last_exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 29906, Requested 2175. Please try again in 4.162s. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</last_exception>", "faithfulness": "<failed_attempts>\n\n<generation number=\"1\">\n<exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 29127, Requested 1584. Please try again in 1.422s. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</exception>\n<completion>\n    None\n</completion>\n</generation>\n\n<generation number=\"2\">\n<exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 29687, Requested 1584. Please try again in 2.542s. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</exception>\n<completion>\n    None\n</completion>\n</generation>\n\n<generation number=\"3\">\n<exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 29686, Requested 1584. Please try again in 2.54s. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</exception>\n<completion>\n    None\n</completion>\n</generation>\n\n</failed_attempts>\n\n<last_exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 29686, Requested 1584. Please try again in 2.54s. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</last_exception>"}`

### PART1_0015
- Sheet: `Part1`
- Video: `Abuse041_x264`
- Question: A woman moved around alone in a closed space with multiple children, occasionally crouching to clean the floor.
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 1.0, "context_recall": null}`
- Generation: `{"answer_relevancy": 0.2867, "factual_correctness": 0.0, "faithfulness": 0.2}`
- End-to-end: `{"ragas_e2e_score": 0.3717}`
- Metric errors: `{"context_recall": "<failed_attempts>\n\n<generation number=\"1\">\n<exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 29575, Requested 2178. Please try again in 3.506s. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</exception>\n<completion>\n    None\n</completion>\n</generation>\n\n<generation number=\"2\">\n<exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 30000, Requested 2178. Please try again in 4.356s. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</exception>\n<completion>\n    None\n</completion>\n</generation>\n\n<generation number=\"3\">\n<exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 30000, Requested 2178. Please try again in 4.356s. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</exception>\n<completion>\n    None\n</completion>\n</generation>\n\n</failed_attempts>\n\n<last_exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 30000, Requested 2178. Please try again in 4.356s. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</last_exception>"}`

### PART1_0016
- Sheet: `Part1`
- Video: `Abuse041_x264`
- Question: A woman held a child with one hand and pulled out a green object from under the table with the other.
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 1.0, "context_recall": null}`
- Generation: `{"answer_relevancy": 0.2559, "factual_correctness": 0.0, "faithfulness": 0.625}`
- End-to-end: `{"ragas_e2e_score": 0.4702}`
- Metric errors: `{"context_recall": "<failed_attempts>\n\n<generation number=\"1\">\n<exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 29561, Requested 2175. Please try again in 3.472s. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</exception>\n<completion>\n    None\n</completion>\n</generation>\n\n<generation number=\"2\">\n<exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 30000, Requested 2175. Please try again in 4.35s. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</exception>\n<completion>\n    None\n</completion>\n</generation>\n\n<generation number=\"3\">\n<exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 30000, Requested 2175. Please try again in 4.35s. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</exception>\n<completion>\n    None\n</completion>\n</generation>\n\n</failed_attempts>\n\n<last_exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 30000, Requested 2175. Please try again in 4.35s. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</last_exception>"}`

### PART1_0017
- Sheet: `Part1`
- Video: `Abuse042_x264`
- Question: Is there a video of a woman feeding a baby on the floor and forcefully pushing the baby at some point?
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 1.0, "context_recall": null}`
- Generation: `{"answer_relevancy": 0.4493, "factual_correctness": 0.0, "faithfulness": 0.2}`
- End-to-end: `{"ragas_e2e_score": 0.4123}`
- Metric errors: `{"context_recall": "<failed_attempts>\n\n<generation number=\"1\">\n<exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 30000, Requested 2176. Please try again in 4.352s. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</exception>\n<completion>\n    None\n</completion>\n</generation>\n\n<generation number=\"2\">\n<exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 28362, Requested 2176. Please try again in 1.076s. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</exception>\n<completion>\n    None\n</completion>\n</generation>\n\n<generation number=\"3\">\n<exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 30000, Requested 2176. Please try again in 4.352s. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</exception>\n<completion>\n    None\n</completion>\n</generation>\n\n</failed_attempts>\n\n<last_exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 30000, Requested 2176. Please try again in 4.352s. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</last_exception>"}`

### PART1_0018
- Sheet: `Part1`
- Video: `Abuse042_x264`
- Question: A baby lay alone on the floor for a long time while the caregiver was away.
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": null, "context_recall": null}`
- Generation: `{"answer_relevancy": 0.4795, "factual_correctness": 0.0, "faithfulness": 0.125}`
- End-to-end: `{"ragas_e2e_score": 0.2015}`
- Metric errors: `{"context_precision": "<failed_attempts>\n\n<generation number=\"1\">\n<exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 30000, Requested 1369. Please try again in 2.738s. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</exception>\n<completion>\n    None\n</completion>\n</generation>\n\n<generation number=\"2\">\n<exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 29213, Requested 1369. Please try again in 1.164s. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</exception>\n<completion>\n    None\n</completion>\n</generation>\n\n<generation number=\"3\">\n<exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 29611, Requested 1369. Please try again in 1.959s. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</exception>\n<completion>\n    None\n</completion>\n</generation>\n\n</failed_attempts>\n\n<last_exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 29611, Requested 1369. Please try again in 1.959s. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</last_exception>", "context_recall": "<failed_attempts>\n\n<generation number=\"1\">\n<exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 30000, Requested 2169. Please try again in 4.338s. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</exception>\n<completion>\n    None\n</completion>\n</generation>\n\n<generation number=\"2\">\n<exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 30000, Requested 2169. Please try again in 4.338s. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</exception>\n<completion>\n    None\n</completion>\n</generation>\n\n<generation number=\"3\">\n<exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 30000, Requested 2169. Please try again in 4.338s. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</exception>\n<completion>\n    None\n</completion>\n</generation>\n\n</failed_attempts>\n\n<last_exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 30000, Requested 2169. Please try again in 4.338s. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</last_exception>"}`

### PART1_0019
- Sheet: `Part1`
- Video: `Abuse042_x264`
- Question: A woman talked on the phone while continuously patting the back of a baby lying beside her with her other hand.
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": null, "context_recall": null}`
- Generation: `{"answer_relevancy": 0.5478, "factual_correctness": 0.0, "faithfulness": 0.125}`
- End-to-end: `{"ragas_e2e_score": 0.2243}`
- Metric errors: `{"context_precision": "<failed_attempts>\n\n<generation number=\"1\">\n<exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 29071, Requested 1378. Please try again in 898ms. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</exception>\n<completion>\n    None\n</completion>\n</generation>\n\n<generation number=\"2\">\n<exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 29683, Requested 1378. Please try again in 2.122s. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</exception>\n<completion>\n    None\n</completion>\n</generation>\n\n<generation number=\"3\">\n<exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 29094, Requested 1378. Please try again in 943ms. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</exception>\n<completion>\n    None\n</completion>\n</generation>\n\n</failed_attempts>\n\n<last_exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 29094, Requested 1378. Please try again in 943ms. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</last_exception>", "context_recall": "<failed_attempts>\n\n<generation number=\"1\">\n<exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 29023, Requested 2178. Please try again in 2.402s. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</exception>\n<completion>\n    None\n</completion>\n</generation>\n\n<generation number=\"2\">\n<exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 30000, Requested 2178. Please try again in 4.356s. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</exception>\n<completion>\n    None\n</completion>\n</generation>\n\n<generation number=\"3\">\n<exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 28916, Requested 2178. Please try again in 2.188s. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</exception>\n<completion>\n    None\n</completion>\n</generation>\n\n</failed_attempts>\n\n<last_exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 28916, Requested 2178. Please try again in 2.188s. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</last_exception>"}`

### PART1_0020
- Sheet: `Part1`
- Video: `Arrest043_x264`
- Question: Is there a clip of a police officer stomping on and beating a person lying on the ground in a yard?
- Route mode: `pure_sql`
- Top hit: `False`
- Retrieval: `{"context_precision": null, "context_recall": null}`
- Generation: `{"answer_relevancy": 0.0, "factual_correctness": 0.0, "faithfulness": null}`
- End-to-end: `{"ragas_e2e_score": 0.0}`
- Metric errors: `{}`

### PART1_0021
- Sheet: `Part1`
- Video: `Arrest043_x264`
- Question: Law enforcement was present, but one officer inflicted physical harm beyond normal procedure on a restrained person.
- Route mode: `hybrid_search`
- Top hit: `True`
- Retrieval: `{"context_precision": 0.0, "context_recall": null}`
- Generation: `{"answer_relevancy": 0.3992, "factual_correctness": 0.0, "faithfulness": 0.0}`
- End-to-end: `{"ragas_e2e_score": 0.0998}`
- Metric errors: `{"context_recall": "<failed_attempts>\n\n<generation number=\"1\">\n<exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 29288, Requested 2179. Please try again in 2.934s. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</exception>\n<completion>\n    None\n</completion>\n</generation>\n\n<generation number=\"2\">\n<exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 29343, Requested 2179. Please try again in 3.044s. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</exception>\n<completion>\n    None\n</completion>\n</generation>\n\n<generation number=\"3\">\n<exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 29273, Requested 2179. Please try again in 2.904s. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</exception>\n<completion>\n    None\n</completion>\n</generation>\n\n</failed_attempts>\n\n<last_exception>\n    Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-VI1F6u5rNCpzlvsUCErTPhz6 on tokens per min (TPM): Limit 30000, Used 29273, Requested 2179. Please try again in 2.904s. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}\n</last_exception>"}`
