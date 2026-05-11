# Agent 端到端做题测试

**Started**: 2026-05-12T04:40:25.080164  
**Elapsed**: 130.5s  

## 汇总

| 指标 | 值 |
|------|----|
| 通过率 | **92.0%** (23/25) |
| 答案正确率 | **92.0%** (23/25) |
| 时间命中率 | **12.0%** (3/25) |
| 平均 Recall | 0.9800 |
| 平均 Precision | 0.6293 |
| 平均 IoU | 0.6227 |
| 多摄意图检测率 | 100.0% |
| 有效回答率 | 100.0% |
| 平均耗时/题 | 5.2s |
| 总耗时 | 130.5s |

## 逐题结果

### ❌ Q1 [18.3s]
- **问题**: Did a person with beige jacket appear in camera G329 and then appear again in camera G328?
- **期望答案**: yes | **期望时间**: 2:02-3:36
- ❌ 答案正确 | ❌ 时间命中
- **期望摄像头**: ['G328', 'G329']
- **回答中的摄像头**: ['G329', 'G339']
- **Recall**: 0.50 | **Precision**: 0.50 | **IoU**: 0.33
- **multi_camera 检测**: True | **GE rows**: 0
- **节点路径**: self_query_node → query_classification_node → parallel_retrieval_fusion_node → match_verifier_node → final_answer_node → summary_node
- **Agent 回答**: No matching clip is expected.
Sources: [mixed] 2018-03-11.13-50-01.13-55-01.admin.G329.r13 | event_id=7 | 119.633-121.733; [mixed] 2018-03-11.13-50-01.13-55-01.school.G339.r13 | event_id=602 | 164.433-168.883; [mixed] 2018-03-11.13-50-01.13-55-01.admin.G329.r13 | event_id=2 | 109.7-116.5

### ✅ Q2 [3.6s]
- **问题**: Did a person with dark long coat appear in camera G329 and then appear again in camera G328?
- **期望答案**: yes | **期望时间**: 2:03-3:36
- ✅ 答案正确 | ❌ 时间命中
- **期望摄像头**: ['G328', 'G329']
- **回答中的摄像头**: ['G328', 'G329', 'G339', 'G421', 'G506']
- **Recall**: 1.00 | **Precision**: 0.40 | **IoU**: 0.40
- **multi_camera 检测**: True | **GE rows**: 78
- **节点路径**: self_query_node → query_classification_node → parallel_retrieval_fusion_node → match_verifier_node → final_answer_node → summary_node
- **Agent 回答**: Likely yes. The queried entity appears across multiple cameras. | Cameras: G506, G339, G329, G328, G421 | Times: G506 131.26666666666668-157.6; G339 150.8-153.55; G329 188.233-196.7; G328 279.2-283.23333333333335; G421 284.15-293.533 | Summary: Entity person_global_4 appears in both G329 and G328, m

### ✅ Q3 [4.4s]
- **问题**: Did a person with dark jacket (hood up) appear in camera G329 and then appear again in camera G328?
- **期望答案**: yes | **期望时间**: 3:17-4:28
- ✅ 答案正确 | ✅ 时间命中
- **期望摄像头**: ['G328', 'G329']
- **回答中的摄像头**: ['G328', 'G329', 'G339', 'G421', 'G506']
- **Recall**: 1.00 | **Precision**: 0.40 | **IoU**: 0.40
- **multi_camera 检测**: True | **GE rows**: 78
- **节点路径**: self_query_node → query_classification_node → parallel_retrieval_fusion_node → match_verifier_node → final_answer_node → summary_node
- **Agent 回答**: Likely yes. The queried entity appears across multiple cameras. | Cameras: G506, G339, G329, G328, G421 | Times: G506 131.26666666666668-157.6; G339 150.8-153.55; G329 188.233-196.7; G328 279.2-283.23333333333335; G421 284.15-293.533 | Summary: Entity person_global_4 appears in both G329 (3:08-3:16)

### ✅ Q4 [6.4s]
- **问题**: Did a person with dark jacket (hood up) appear in camera G328 and then appear again in camera G339?
- **期望答案**: yes | **期望时间**: 3:36-3:50
- ✅ 答案正确 | ✅ 时间命中
- **期望摄像头**: ['G328', 'G339']
- **回答中的摄像头**: ['G328', 'G339', 'G424']
- **Recall**: 1.00 | **Precision**: 0.67 | **IoU**: 0.67
- **multi_camera 检测**: True | **GE rows**: 78
- **节点路径**: self_query_node → query_classification_node → parallel_retrieval_fusion_node → match_verifier_node → final_answer_node → summary_node
- **Agent 回答**: Yes. The queried entity appears across multiple cameras. | Cameras: G424, G328, G339 | Times: G424 80.1-89.96666666666667; G328 233.13333333333333-234.06666666666666; G339 266.7-277.6 | Summary: Entity person_global_1 appears in both G328 and G339 with consistent cross-camera tracking (G328 3:53-4:2

### ✅ Q5 [5.5s]
- **问题**: Did a person with dark jacket (hood up) appear in camera G329 and then appear again in camera G339?
- **期望答案**: yes | **期望时间**: 3:36-3:50
- ✅ 答案正确 | ✅ 时间命中
- **期望摄像头**: ['G329', 'G339']
- **回答中的摄像头**: ['G328', 'G329', 'G339', 'G421', 'G506']
- **Recall**: 1.00 | **Precision**: 0.40 | **IoU**: 0.40
- **multi_camera 检测**: True | **GE rows**: 78
- **节点路径**: self_query_node → query_classification_node → parallel_retrieval_fusion_node → match_verifier_node → final_answer_node → summary_node
- **Agent 回答**: Yes. The queried entity appears across multiple cameras. | Cameras: G506, G339, G329, G328, G421 | Times: G506 131.26666666666668-157.6; G339 150.8-153.55; G329 188.233-196.7; G328 279.2-283.23333333333335; G421 284.15-293.533 | Summary: Entity person_global_4 appears in both G329 and G339 with cons

### ✅ Q6 [4.9s]
- **问题**: Did a person with black coat with fur-trimmed hood appear in camera G329 and then appear again in camera G328?
- **期望答案**: yes | **期望时间**: 3:18-4:28
- ✅ 答案正确 | ❌ 时间命中
- **期望摄像头**: ['G328', 'G329']
- **回答中的摄像头**: ['G328', 'G329', 'G339', 'G421', 'G506']
- **Recall**: 1.00 | **Precision**: 0.40 | **IoU**: 0.40
- **multi_camera 检测**: True | **GE rows**: 78
- **节点路径**: self_query_node → query_classification_node → parallel_retrieval_fusion_node → match_verifier_node → final_answer_node → summary_node
- **Agent 回答**: Likely yes. The queried entity appears across multiple cameras. | Cameras: G506, G339, G329, G328, G421 | Times: G506 131.26666666666668-157.6; G339 150.8-153.55; G329 188.233-196.7; G328 279.2-283.23333333333335; G421 284.15-293.533 | Summary: Entity person_global_4 appears in both G329 (188.233-19

### ✅ Q7 [4.8s]
- **问题**: Did a person with black coat with fur-trimmed hood appear in camera G328 and then appear again in camera G339?
- **期望答案**: yes | **期望时间**: 3:36-3:50
- ✅ 答案正确 | ❌ 时间命中
- **期望摄像头**: ['G328', 'G339']
- **回答中的摄像头**: ['G328', 'G339', 'G424']
- **Recall**: 1.00 | **Precision**: 0.67 | **IoU**: 0.67
- **multi_camera 检测**: True | **GE rows**: 78
- **节点路径**: self_query_node → query_classification_node → parallel_retrieval_fusion_node → match_verifier_node → final_answer_node → summary_node
- **Agent 回答**: Likely yes. The queried entity appears across multiple cameras. | Cameras: G424, G328, G339 | Times: G424 80.1-89.96666666666667; G328 233.13333333333333-234.06666666666666; G339 266.7-277.6 | Summary: Entity person_global_1 appears in both G328 and G339 (as well as G424), confirming cross-camera pr

### ✅ Q8 [5.7s]
- **问题**: Did a person with black coat with fur-trimmed hood appear in camera G329 and then appear again in camera G339?
- **期望答案**: yes | **期望时间**: 3:36-3:50
- ✅ 答案正确 | ❌ 时间命中
- **期望摄像头**: ['G329', 'G339']
- **回答中的摄像头**: ['G328', 'G329', 'G339', 'G421', 'G506']
- **Recall**: 1.00 | **Precision**: 0.40 | **IoU**: 0.40
- **multi_camera 检测**: True | **GE rows**: 78
- **节点路径**: self_query_node → query_classification_node → parallel_retrieval_fusion_node → match_verifier_node → final_answer_node → summary_node
- **Agent 回答**: Likely yes. The queried entity appears across multiple cameras. | Cameras: G506, G339, G329, G328, G421 | Times: G506 131.26666666666668-157.6; G339 150.8-153.55; G329 188.233-196.7; G328 279.2-283.23333333333335; G421 284.15-293.533 | Summary: Entity person_global_4 and person_global_5 both appear 

### ✅ Q9 [3.3s]
- **问题**: Did a person with white shirt appear in camera G328 and then appear again in camera G339?
- **期望答案**: yes | **期望时间**: 4:56-4:59
- ✅ 答案正确 | ❌ 时间命中
- **期望摄像头**: ['G328', 'G339']
- **回答中的摄像头**: ['G328', 'G339', 'G424']
- **Recall**: 1.00 | **Precision**: 0.67 | **IoU**: 0.67
- **multi_camera 检测**: True | **GE rows**: 78
- **节点路径**: self_query_node → query_classification_node → parallel_retrieval_fusion_node → match_verifier_node → final_answer_node → summary_node
- **Agent 回答**: Yes. The queried entity appears across multiple cameras. | Cameras: G424, G328, G339 | Times: G424 80.1-89.96666666666667; G328 233.13333333333333-234.06666666666666; G339 266.7-277.6 | Summary: Entity person_global_1 appears in both G328 and G339 with consistent cross-camera tracking, matching the 

### ✅ Q10 [3.7s]
- **问题**: Did a person with white shirt appear in camera G328 and then appear again in camera G424?
- **期望答案**: yes | **期望时间**: 3:25-4:52
- ✅ 答案正确 | ❌ 时间命中
- **期望摄像头**: ['G328', 'G424']
- **回答中的摄像头**: ['G328', 'G339', 'G424']
- **Recall**: 1.00 | **Precision**: 0.67 | **IoU**: 0.67
- **multi_camera 检测**: True | **GE rows**: 78
- **节点路径**: self_query_node → query_classification_node → parallel_retrieval_fusion_node → match_verifier_node → final_answer_node → summary_node
- **Agent 回答**: Yes. The queried entity appears across multiple cameras. | Cameras: G424, G328, G339 | Times: G424 80.1-89.96666666666667; G328 233.13333333333333-234.06666666666666; G339 266.7-277.6 | Summary: Entity person_global_1 appears in both G328 and G424 (as well as G339), confirming the same person moved 

### ✅ Q11 [5.0s]
- **问题**: Did a person with white shirt appear in camera G424 and then appear again in camera G339?
- **期望答案**: yes | **期望时间**: 4:56-4:59
- ✅ 答案正确 | ❌ 时间命中
- **期望摄像头**: ['G339', 'G424']
- **回答中的摄像头**: ['G328', 'G339', 'G424']
- **Recall**: 1.00 | **Precision**: 0.67 | **IoU**: 0.67
- **multi_camera 检测**: True | **GE rows**: 78
- **节点路径**: self_query_node → query_classification_node → parallel_retrieval_fusion_node → match_verifier_node → final_answer_node → summary_node
- **Agent 回答**: Likely yes. The queried entity appears across multiple cameras. | Cameras: G424, G328, G339 | Times: G424 80.1-89.96666666666667; G328 233.13333333333333-234.06666666666666; G339 266.7-277.6 | Summary: Entity person_global_1 appears in both G424 and G339 (as well as G328), confirming cross-camera pr

### ✅ Q12 [4.0s]
- **问题**: Did a person with light grey hoodie appear in camera G339 and then appear again in camera G421?
- **期望答案**: yes | **期望时间**: 4:41-4:53
- ✅ 答案正确 | ❌ 时间命中
- **期望摄像头**: ['G339', 'G421']
- **回答中的摄像头**: ['G339', 'G421']
- **Recall**: 1.00 | **Precision**: 1.00 | **IoU**: 1.00
- **multi_camera 检测**: True | **GE rows**: 78
- **节点路径**: self_query_node → query_classification_node → parallel_retrieval_fusion_node → match_verifier_node → final_answer_node → summary_node
- **Agent 回答**: Yes. The queried entity appears across multiple cameras. | Cameras: G421, G339 | Times: G421 12.367-16.067; G339 53.767-64.933 | Summary: Entity person_global_12 appears in both G339 and G421 with appearance described as 'light grey ho' (hoodie), matching the query's description and camera sequence.

### ✅ Q13 [3.9s]
- **问题**: Did a person with light grey hoodie appear in camera G424 and then appear again in camera G339?
- **期望答案**: yes | **期望时间**: 0:55-1:25
- ✅ 答案正确 | ❌ 时间命中
- **期望摄像头**: ['G339', 'G424']
- **回答中的摄像头**: ['G328', 'G339', 'G424']
- **Recall**: 1.00 | **Precision**: 0.67 | **IoU**: 0.67
- **multi_camera 检测**: True | **GE rows**: 78
- **节点路径**: self_query_node → query_classification_node → parallel_retrieval_fusion_node → match_verifier_node → final_answer_node → summary_node
- **Agent 回答**: Likely yes. The queried entity appears across multiple cameras. | Cameras: G424, G328, G339 | Times: G424 80.1-89.96666666666667; G328 233.13333333333333-234.06666666666666; G339 266.7-277.6 | Summary: Entity person_global_1 appears in both G424 and G339 (as well as G328), confirming cross-camera pr

### ✅ Q14 [4.4s]
- **问题**: Did a person with light grey hoodie appear in camera G339 and then appear again in camera G506?
- **期望答案**: yes | **期望时间**: 2:11-2:39
- ✅ 答案正确 | ❌ 时间命中
- **期望摄像头**: ['G339', 'G506']
- **回答中的摄像头**: ['G328', 'G329', 'G339', 'G421', 'G506']
- **Recall**: 1.00 | **Precision**: 0.40 | **IoU**: 0.40
- **multi_camera 检测**: True | **GE rows**: 78
- **节点路径**: self_query_node → query_classification_node → parallel_retrieval_fusion_node → match_verifier_node → final_answer_node → summary_node
- **Agent 回答**: Likely yes. The queried entity appears across multiple cameras. | Cameras: G506, G339, G329, G328, G421 | Times: G506 131.26666666666668-157.6; G339 150.8-153.55; G329 188.233-196.7; G328 279.2-283.23333333333335; G421 284.15-293.533 | Summary: Entity person_global_4 appears in both G339 and G506 as

### ✅ Q15 [3.9s]
- **问题**: Did a person with light grey hoodie appear in camera G424 and then appear again in camera G421?
- **期望答案**: yes | **期望时间**: 4:41-4:53
- ✅ 答案正确 | ❌ 时间命中
- **期望摄像头**: ['G421', 'G424']
- **回答中的摄像头**: ['G328', 'G339', 'G421', 'G424']
- **Recall**: 1.00 | **Precision**: 0.50 | **IoU**: 0.50
- **multi_camera 检测**: True | **GE rows**: 78
- **节点路径**: self_query_node → query_classification_node → parallel_retrieval_fusion_node → match_verifier_node → final_answer_node → summary_node
- **Agent 回答**: Likely yes. The queried entity appears across multiple cameras. | Cameras: G421, G424, G339 | Times: G421 169.117-173.267; G424 266.333-277.133; G339 296.567-299.967 | Summary: Entity person_global_2 appears in both G424 and G421, matching the queried cameras, but its appearance description is missi

### ✅ Q16 [5.5s]
- **问题**: Did a person with light grey hoodie appear in camera G506 and then appear again in camera G421?
- **期望答案**: yes | **期望时间**: 4:41-4:53
- ✅ 答案正确 | ❌ 时间命中
- **期望摄像头**: ['G421', 'G506']
- **回答中的摄像头**: ['G328', 'G329', 'G339', 'G421', 'G424', 'G506']
- **Recall**: 1.00 | **Precision**: 0.33 | **IoU**: 0.33
- **multi_camera 检测**: True | **GE rows**: 78
- **节点路径**: self_query_node → query_classification_node → parallel_retrieval_fusion_node → match_verifier_node → final_answer_node → summary_node
- **Agent 回答**: Yes. The queried entity appears across multiple cameras. | Cameras: G506, G339, G329, G328, G421 | Times: G506 131.26666666666668-157.6; G339 150.8-153.55; G329 188.233-196.7; G328 279.2-283.23333333333335; G421 284.15-293.533 | Summary: Entity person_global_4 appears in both G506 and G421, matching

### ❌ Q17 [5.5s]
- **问题**: Did a person with light grey hoodie appear in camera G424 and then appear again in camera G506?
- **期望答案**: yes | **期望时间**: 2:11-2:39
- ❌ 答案正确 | ❌ 时间命中
- **期望摄像头**: ['G424', 'G506']
- **回答中的摄像头**: ['G328', 'G424', 'G506']
- **Recall**: 1.00 | **Precision**: 0.67 | **IoU**: 0.67
- **multi_camera 检测**: True | **GE rows**: 78
- **节点路径**: self_query_node → query_classification_node → parallel_retrieval_fusion_node → match_verifier_node → final_answer_node → summary_node
- **Agent 回答**: No matching clip is expected. Reason: No global entity appears in both G424 and G506; person_global_4 appears in G506 but not G424, while entities in G424 (e.g., person_global_1, _2, _3, _6, _9, _11) do not appear in G506..
Sources: [hybrid] 2018-03-11.13-50-01.13-55-01.school.G424.r13 | event_id=84

### ✅ Q18 [4.5s]
- **问题**: Did a person with long dark coat appear in camera G424 and then appear again in camera G339?
- **期望答案**: yes | **期望时间**: 0:55-1:25
- ✅ 答案正确 | ❌ 时间命中
- **期望摄像头**: ['G339', 'G424']
- **回答中的摄像头**: ['G339', 'G424']
- **Recall**: 1.00 | **Precision**: 1.00 | **IoU**: 1.00
- **multi_camera 检测**: True | **GE rows**: 78
- **节点路径**: self_query_node → query_classification_node → parallel_retrieval_fusion_node → match_verifier_node → final_answer_node → summary_node
- **Agent 回答**: Likely yes. The queried entity appears across multiple cameras. | Cameras: G339, G424 | Times: G339 150.933-157.583; G424 246.76666666666668-273.06666666666666 | Summary: Entity person_global_11 appears in both G424 and G339 with appearance described as 'dark coat', matching the query's 'long dark c

### ✅ Q19 [3.6s]
- **问题**: Did a person with dark jacket appear in camera G424 and then appear again in camera G339?
- **期望答案**: yes | **期望时间**: 0:55-1:25
- ✅ 答案正确 | ❌ 时间命中
- **期望摄像头**: ['G339', 'G424']
- **回答中的摄像头**: ['G339', 'G424']
- **Recall**: 1.00 | **Precision**: 1.00 | **IoU**: 1.00
- **multi_camera 检测**: True | **GE rows**: 78
- **节点路径**: self_query_node → query_classification_node → parallel_retrieval_fusion_node → match_verifier_node → final_answer_node → summary_node
- **Agent 回答**: Yes. The queried entity appears across multiple cameras. | Cameras: G339, G424 | Times: G339 150.933-157.583; G424 246.76666666666668-273.06666666666666 | Summary: Entity person_global_11 appears in both G424 and G339 with appearance described as 'dark coat', matching the query's 'dark jacket' acros

### ✅ Q20 [7.7s]
- **问题**: Did a person with beige/khaki coat appear in camera G424 and then appear again in camera G339?
- **期望答案**: yes | **期望时间**: 0:55-1:25
- ✅ 答案正确 | ❌ 时间命中
- **期望摄像头**: ['G339', 'G424']
- **回答中的摄像头**: ['G328', 'G339', 'G424']
- **Recall**: 1.00 | **Precision**: 0.67 | **IoU**: 0.67
- **multi_camera 检测**: True | **GE rows**: 78
- **节点路径**: self_query_node → query_classification_node → parallel_retrieval_fusion_node → match_verifier_node → final_answer_node → summary_node
- **Agent 回答**: Likely yes. The queried entity appears across multiple cameras. | Cameras: G424, G328, G339 | Times: G424 80.1-89.96666666666667; G328 233.13333333333333-234.06666666666666; G339 266.7-277.6 | Summary: Entity person_global_1 appears in both G424 and G339 (as well as G328), confirming cross-camera pr

### ✅ Q21 [4.1s]
- **问题**: Did a person with brown jacket with dark hood/scarf appear in camera G424 and then appear again in camera G339?
- **期望答案**: yes | **期望时间**: 0:55-1:25
- ✅ 答案正确 | ❌ 时间命中
- **期望摄像头**: ['G339', 'G424']
- **回答中的摄像头**: ['G328', 'G339', 'G424']
- **Recall**: 1.00 | **Precision**: 0.67 | **IoU**: 0.67
- **multi_camera 检测**: True | **GE rows**: 78
- **节点路径**: self_query_node → query_classification_node → parallel_retrieval_fusion_node → match_verifier_node → final_answer_node → summary_node
- **Agent 回答**: Likely yes. The queried entity appears across multiple cameras. | Cameras: G424, G328, G339 | Times: G424 80.1-89.96666666666667; G328 233.13333333333333-234.06666666666666; G339 266.7-277.6 | Summary: Entity person_global_1 appears in both G424 and G339 (as well as G328), confirming cross-camera pr

### ✅ Q22 [5.0s]
- **问题**: Did a person with light grey coat with black hat appear in camera G424 and then appear again in camera G339?
- **期望答案**: yes | **期望时间**: 0:55-1:25
- ✅ 答案正确 | ❌ 时间命中
- **期望摄像头**: ['G339', 'G424']
- **回答中的摄像头**: ['G328', 'G339', 'G424']
- **Recall**: 1.00 | **Precision**: 0.67 | **IoU**: 0.67
- **multi_camera 检测**: True | **GE rows**: 78
- **节点路径**: self_query_node → query_classification_node → parallel_retrieval_fusion_node → match_verifier_node → final_answer_node → summary_node
- **Agent 回答**: Likely yes. The queried entity appears across multiple cameras. | Cameras: G424, G328, G339 | Times: G424 80.1-89.96666666666667; G328 233.13333333333333-234.06666666666666; G339 266.7-277.6 | Summary: Entity person_global_1 appears in both G424 and G339 (as well as G328), confirming cross-camera pr

### ✅ Q23 [4.5s]
- **问题**: Did a person with black hoodie (hood up) appear in camera G421 and then appear again in camera G339?
- **期望答案**: yes | **期望时间**: 2:32-3:03
- ✅ 答案正确 | ❌ 时间命中
- **期望摄像头**: ['G339', 'G421']
- **回答中的摄像头**: ['G339', 'G421', 'G424']
- **Recall**: 1.00 | **Precision**: 0.67 | **IoU**: 0.67
- **multi_camera 检测**: True | **GE rows**: 78
- **节点路径**: self_query_node → query_classification_node → parallel_retrieval_fusion_node → match_verifier_node → final_answer_node → summary_node
- **Agent 回答**: Likely yes. The queried entity appears across multiple cameras. | Cameras: G339, G421 | Times: G339 53.433-56.033; G421 104.46666666666667-299.96666666666664 | Summary: Entity person_global_10 appears in both G421 and G339 with 'dark long-sle' appearance, consistent with a black hoodie (hood up); ho

### ✅ Q24 [4.1s]
- **问题**: Did a person with dark jacket appear in camera G421 and then appear again in camera G339?
- **期望答案**: yes | **期望时间**: 2:32-3:03
- ✅ 答案正确 | ❌ 时间命中
- **期望摄像头**: ['G339', 'G421']
- **回答中的摄像头**: ['G339', 'G421']
- **Recall**: 1.00 | **Precision**: 1.00 | **IoU**: 1.00
- **multi_camera 检测**: True | **GE rows**: 78
- **节点路径**: self_query_node → query_classification_node → parallel_retrieval_fusion_node → match_verifier_node → final_answer_node → summary_node
- **Agent 回答**: Yes. The queried entity appears across multiple cameras. | Cameras: G339, G421 | Times: G339 53.433-56.033; G421 104.46666666666667-299.96666666666664 | Summary: Entity person_global_10 appears in both G421 and G339 with appearance described as 'dark long-sle' (short for dark long-sleeve jacket), ma

### ✅ Q25 [4.1s]
- **问题**: Did a person with dark hoodie appear in camera G421 and then appear again in camera G339?
- **期望答案**: yes | **期望时间**: 2:32-3:03
- ✅ 答案正确 | ❌ 时间命中
- **期望摄像头**: ['G339', 'G421']
- **回答中的摄像头**: ['G339', 'G421', 'G424']
- **Recall**: 1.00 | **Precision**: 0.67 | **IoU**: 0.67
- **multi_camera 检测**: True | **GE rows**: 78
- **节点路径**: self_query_node → query_classification_node → parallel_retrieval_fusion_node → match_verifier_node → final_answer_node → summary_node
- **Agent 回答**: Likely yes. The queried entity appears across multiple cameras. | Cameras: G339, G421 | Times: G339 53.433-56.033; G421 104.46666666666667-299.96666666666664 | Summary: Entity person_global_10 appears in both G421 and G339 with appearance described as 'dark long-sle' (likely 'dark long-sleeve' or 'd
