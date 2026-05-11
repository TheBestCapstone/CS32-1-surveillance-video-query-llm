# Handoff：多摄像头端到端测试后的下一步

本文档承接聊天上下文，记录当前现象、根因与建议的后续工作，便于交接或继续迭代。

## 发现的问题

在「做题式」端到端测试（如 `test_07_e2e_agent.py`）中：

- **match_verifier_node 对跨摄像头「存在性」类问题整体偏消极**：例如 25 道题里约有 **18** 道的 `final_answer` 文案为 **「No matching clip is expected」**。
- **与检索事实不一致**：同一题的 **Sources** 里往往已经包含两条来自不同摄像头、且与标注期望一致的 event（例如 Q11 中同时出现 G424 与 G339），说明 **检索层已召回正确证据**，但最终面向用户的结论仍为否定。

## 根因（简要）

- **final_answer_node** 与 **match_verifier_node** 当前逻辑与 prompt 主要面向 **单摄像头 existence** 场景（单一 clip / 单一视角是否「命中」）。
- **cross_camera** 问题的合格答案通常需要：**在同一 global entity 轨迹下汇总多个 camera_id**，并明确「先后 / 同时出现在哪些视角」，而不是用「是否唯一匹配某一个 clip」来判断。
- **Global Entity（GE）分支** 与 fusion 侧数据已就绪；缺口在 **生成与校验层**：缺少 **multi_camera 专用** 的判定规则与 **prompt 模板**（何时答 Yes、如何列举多摄像头与时间线、如何避免误报「无匹配 clip」）。

## 下一步需要做的事

1. **读透现状**
  - 通读 `agent/node/match_verifier_node.py`、`agent/node/answer_node.py`（含 final_answer 相关分支），标出所有触发「No matching clip…」或等价否定输出的条件。
2. **按状态分支适配 multi_camera**
  - 从 `classification_result.multi_camera`（或等价字段）传入 verifier / answer 节点。  
  - 当 `multi_camera=True` 且 fused / GE 结果中存在 **同一 `global_entity_id` 下多条不同 `camera_id`（或等价字段）** 时：  
    - **不应**默认走「单 clip 必须严格匹配」的否定路径；  
    - 应改为 **跨摄像头证据聚合**（列举摄像头 + 时间段 + 简要依据）。
3. **新增 prompt 与结构化输出**
  - 为 multi_camera 增加专用 system/user 片段：**明确要求**根据 Sources 中多条 event 给出肯定性结论（若证据充分），并输出 **Cameras:** / **Times:** 等可解析小节（与现有测试里的召回/时间匹配指标对齐）。  
  - 限定：**不得**在 Sources 已含多摄像头一致证据时输出笼统的「无匹配 clip」。
4. **回归测试**
  - 重新跑 `test_07_e2e_agent.py`（或当前约定的 testable 题集），对比修改前后：`answer_correct`、camera recall/precision/IoU、以及「No matching clip」占比。
5. **文档与设计同步（可选）**
  - 将上述行为约定补一节到 `agent/多摄像头管道搭建.md`（检索 vs 生成层 gap 闭合说明）。

---

*文件名按交接约定写作 `hanoff.md`（与 `handoff` 同义备忘）。*