# lightingRL 接入方案

- 目标: 将当前 `agent` 接入 `Agent-lightning/LightningRL`，优先实现“训练并自动修改 prompt”，在收益稳定后再评估是否进入模型权重训练。
- 当前结论: 第一阶段应选择 `prompt optimization first`，不要一开始直接做全图 `VERL`。

## 1. 框架调研结论

- `Agent-lightning` 适合把现有 agent 包装成可训练对象，核心抽象是 `task`、`rollout`、`span`、`prompt template`。
- 如果重点是“让框架自动改 prompt”，最适合采用 `prompt_rollout + APO`。
- 如果后续要训练模型权重，可以再切到 `LitAgent + Trainer + VERL`。
- `Trainer.dev()` 可以先做干跑，验证 traces、reward、数据集、数据库连接和 graph 控制流。
- 官方 `SQL agent` 与 `RAG agent` 示例都说明：LangGraph/RAG agent 可以通过薄封装接入，不必重写整套业务逻辑。

## 2. 当前 agent 现状映射

### 2.1 默认主链路

- 当前默认执行模式是 `parallel_fusion`。
- 主链路为 `self_query -> query_classification -> parallel_retrieval_fusion -> final_answer -> summary`。
- 这条链路是第一阶段唯一应该围绕其做训练接入的对象。

### 2.2 当前真正生效的 prompt

- `agent/node/self_query_node.py` 中的 `self_query prompt`
- `agent/agents/shared/query_classifier.py` 中的 `query classification prompt`
- `agent/node/summary_node.py` 中的 `summary prompt`

### 2.3 当前不建议立即训练的 prompt

- `agent/init/agent_init_prompt.md`
- `agent/node/router_prompts.py` 中的两类 `router prompts`

- 原因: 这两部分只在 `legacy_router` 模式下才会生效，而当前默认路径并不消费它们。

### 2.4 已有可复用评测骨架

- `agent/test/agent_test_importer.py` 已能将 `agent_test.xlsx` 规范化为可评测样本。
- `agent/test/ragas_eval_runner.py` 已能完成以下流程:
- 读取 `Part1` 与 `Part4` 数据
- 执行 graph rollout
- 采集 `node_trace`、`response`、`retrieved_contexts`、`top_video_ids`
- 计算 `RAGAS` 指标
- 汇总 `summary_report`

- 这意味着仓库已经具备“离线 rollout + 离线打分”的基础设施，缺的是正式训练层。

## 3. 与 Agent-lightning 的概念对齐

- `task`: 一条评测样本，一般来自 `agent_test.xlsx` 规范化后的 case
- `rollout`: 一次完整 graph 调用
- `span`: graph 中的节点执行、LLM 调用、检索操作、最终评分
- `prompt template`: 被训练算法优化的目标 prompt
- `reward`: 来自 `RAGAS`、命中率、路由正确率、延迟约束等组合后的单值分数

## 4. 推荐技术路线

### 4.1 路线总览

- 阶段 A: `Prompt-only` 接入，使用 `APO` 自动优化 prompt，不改模型权重
- 阶段 B: 在阶段 A 明显有效后，再接入 `VERL` 做选择性节点权重训练

### 4.2 为什么先做 Prompt-only

- 当前目标明确提到“训练并修改 prompt”，`APO` 与目标直接吻合。
- 当前仓库已经有稳定的离线评测与 case 运行入口，先做 prompt 优化改动最小。
- 直接进入 `VERL` 需要处理更复杂的资源、模型服务、credit assignment 和训练成本。
- 多 prompt、多节点、全图同时做 RL，容易把 reward 噪声与 credit assignment 问题放大。

### 4.3 第一阶段训练优先级

- `P0`: `summary prompt`
- `P1`: `query classification prompt`
- `P2`: `self_query prompt`

- 原因:
- `summary prompt` 与最终回答质量最直接相关，reward 定义最清晰。
- `query classification prompt` 直接影响走向 `pure_sql` 或 `hybrid_search` 的兼容标签，容易做路由正确率与下游效果联动评估。
- `self_query prompt` 会影响整条检索链，但 credit assignment 相对更难，因此排在第三位。

### 4.4 第一阶段不要做的事情

- 不要把 `legacy_router` 的 prompt 纳入第一轮训练
- 不要把 3 个 prompt 绑成单一超大 `prompt bundle` 直接优化
- 不要让训练过程读取 ground truth 答案作为 agent 输入
- 不要一开始就让训练目标覆盖所有节点和所有分支

## 5. 目标架构设计

### 5.1 建议在 `agent/lightingRL` 下新增的实现文件

- `prompt_registry.py`
  - 统一管理当前可训练 prompt
  - 支持按 `prompt_key` 加载、覆盖、回滚

- `dataset_builder.py`
  - 将 `agent/test` 下现有评测数据转换为 `Agent-lightning` 可消费的 `jsonl/parquet`

- `reward_adapter.py`
  - 将 `RAGAS`、`top_hit_rate`、路由正确率、失败惩罚、延迟惩罚组合成训练 reward

- `prompt_rollout_agent.py`
  - 用 `@prompt_rollout` 封装现有 agent，使训练算法可以注入 prompt template

- `train_prompt_apo.py`
  - 运行 `APO` 训练
  - 控制 `target_prompt_key`
  - 保存每轮 prompt 候选与评测结果

- `train_verl.py`
  - 第二阶段可选
  - 用 `LitAgent + Trainer + VERL` 训练选定节点

- `eval_compare.py`
  - 对 baseline prompt 与优化后 prompt 做统一对比

### 5.2 prompt registry 设计原则

- 每个 prompt 必须有独立 `prompt_key`
- 每个 prompt 必须能以纯文本模板形式被外部注入
- 节点代码不再直接内嵌长 prompt 文本，而是通过 registry 读取
- 每次训练只激活一个主目标 `prompt_key`

### 5.3 rollout 封装原则

- 不重写现有 graph 主逻辑
- 只在外层包一层“可注入 prompt 的 runner”
- rollout 内部继续复用 `build_graph()` 和现有 runtime/env 装配
- rollout 结束后返回单值 reward，同时保留 traces 供框架分析

## 6. 数据接入方案

### 6.1 数据来源

- 主来源: `agent/test/agent_test.xlsx`
- 规范化入口: `agent/test/agent_test_importer.py`
- 默认评测范围: `Part1` 与 `Part4`

### 6.2 建议训练样本结构

- `case_id`
- `question`
- `reference_answer`
- `video_id`
- `source_sheet`
- `difficulty`
- `expected_route`，如果能从规则或人工标注补齐
- `metadata`

### 6.3 rollout 运行时额外采集字段

- `response`
- `node_trace`
- `retrieved_contexts`
- `top_video_ids`
- `top_hit`
- `route_mode`
- `tool_error`
- `elapsed_ms`

### 6.4 数据切分建议

- `train`: 70%
- `val`: 15%
- `test`: 15%

- 原则:
- 至少按 `video_id` 或 case 主题做去泄漏切分
- 不要只在同一批 `Part1/Part4` case 上训练再回测同一批样本
- 先保留一份完全冻结的 `holdout` 集做最终验收

## 7. Reward 设计

### 7.1 通用 reward 设计原则

- reward 必须是单值
- reward 必须和当前被优化的 prompt 直接相关
- reward 不能完全依赖单一指标
- 失败、异常、空结果必须有明确惩罚

### 7.2 `summary prompt` 的 reward

- 推荐公式:
- `0.40 * factual_correctness`
- `0.35 * answer_relevancy`
- `0.25 * faithfulness`

- 补充规则:
- 没有 `response` 时直接给低分
- 出现 hallucination 或严重偏题时做额外惩罚

### 7.3 `query classification prompt` 的 reward

- 推荐公式:
- `0.40 * route_accuracy`
- `0.30 * top_hit`
- `0.30 * ragas_e2e_score`

- 说明:
- 如果暂时没有人工 `route label`，可以先用规则弱标注加人工抽检
- 也可以将 “structured / semantic / mixed” 的历史表现统计后转成软标签

### 7.4 `self_query prompt` 的 reward

- 推荐公式:
- `0.35 * context_recall`
- `0.25 * context_precision`
- `0.20 * top_hit`
- `0.20 * ragas_e2e_score`

- 说明:
- `self_query` 对最终答案有间接影响，因此不要只看最终回答分
- 更应关注它对检索上下文质量的提升

### 7.5 全局惩罚项

- graph 执行异常: `-1.0`
- 空上下文且本应可检索: `-0.5`
- 延迟超阈值: 线性扣分
- 产生不可解析输出: 额外扣分

## 8. 第一阶段 Prompt-only 实施步骤

### Step 0 冻结 baseline

- 固定当前主链路为 `parallel_fusion`
- 固定当前模型、数据库、评测范围和 `RAGAS` 配置
- 先跑一版 baseline，产出可对比的 `summary_report`

### Step 1 抽离 prompt

- 把 `self_query`、`query classification`、`summary` 三个 prompt 从节点代码中抽离
- 保持默认行为完全不变
- 支持外部覆盖单个 prompt

### Step 2 建立 dataset builder

- 复用 `agent_test_importer.py`
- 生成 `Agent-lightning` 所需的 `task dataset`
- 每条 task 只包含 agent 运行必需字段，不暴露 reference 给 agent 输入

### Step 3 建立 prompt rollout agent

- 用 `@prompt_rollout` 包装一个函数
- 输入为 `task` 与 `prompt_template`
- 在函数内部将 `prompt_template` 注入目标节点
- 调用现有 graph
- 运行后返回 reward

### Step 4 建立 reward adapter

- 调用或复用 `ragas_eval_runner.py` 内现有的打分逻辑
- 将多指标压缩成单值 reward
- 输出每条样本的 reward 分解，便于诊断

### Step 5 先用 `Trainer.dev()` 干跑

- 检查 trace 是否完整
- 检查 reward 是否非空
- 检查 prompt 注入是否真的命中目标节点
- 检查数据库与向量库在并发下是否稳定

### Step 6 运行 `APO`

- 一次只训练一个 `prompt_key`
- 每轮保存:
- 原始 prompt
- critique
- rewritten prompt
- val 集指标
- best prompt

### Step 7 对比评测

- 在冻结的 `holdout` 集上比较 baseline 与新 prompt
- 只有当收益稳定且无明显副作用时，才允许替换线上默认 prompt

## 9. 第二阶段 VERL 方案

### 9.1 何时进入 VERL

- `APO` 已经把 prompt 调到较稳定水平
- 但最终质量仍被模型推理能力限制
- 或者需要训练的对象已经不是“纯 prompt”，而是更深层的生成策略

### 9.2 推荐训练边界

- 只选择单节点或少数节点进入 `VERL`
- 优先考虑 `summary` 相关生成节点
- 路由和 `self_query` 节点除非 label 质量足够高，否则暂不进入权重训练

### 9.3 接入方式

- 通过 `LitAgent` 包装现有 graph
- rollout 内调用 `build_graph()`
- 从 `resources["main_llm"]` 获取训练时注入的模型 endpoint
- 返回单值 reward
- 通过 `Trainer(..., adapter={"agent_match": ...})` 控制只训练目标 agent

### 9.4 VERL 风险

- 训练资源成本显著提升
- trace、tool call、并发 runner 稳定性要求更高
- reward 噪声会直接影响模型更新方向
- 若目标只是改 prompt，这一步很可能投入产出比不高

## 10. 验收标准

- `ragas_e2e_score_avg` 相比 baseline 提升，或至少不下降
- `factual_correctness_avg` 不允许明显下降
- `top_hit_rate` 不下降
- graph error cases 不增加
- 平均延迟不出现不可接受恶化
- 新 prompt 可读、可解释、可回滚

## 11. 风险与规避

- 风险: `RAGAS` 分数有波动
- 规避: 每轮都保留固定 `holdout` 集与多次重复评测

- 风险: 多 prompt 同时训练导致 credit assignment 失真
- 规避: 第一阶段坚持“一次一个 prompt_key”

- 风险: 训练结果只对 `Part1/Part4` 有效
- 规避: 后续补充更多 sheet 或外部数据，并做分层评测

- 风险: 默认主链路与 `legacy_router` 混淆
- 规避: 所有实验都显式固定 `AGENT_EXECUTION_MODE=parallel_fusion`

- 风险: reward 泄漏 ground truth
- 规避: reference 只给 scorer，不给 rollout 内 agent

## 12. 最终建议

- 现在就可以启动的最优方案是:
- 先做 `summary prompt` 的 `APO` 原型
- 复用现有 `ragas_eval_runner.py` 作为第一版 scorer
- 用 `Trainer.dev()` 验证 traces 与 reward
- 在首轮成功后，再依次推进 `query classification prompt` 与 `self_query prompt`

- 不建议当前立刻做的事情是:
- 直接上全图 `VERL`
- 优化 `legacy_router` prompt
- 将多个 prompt 一起联训

## 13. 落地顺序清单

1. 建立 `prompt registry`
2. 建立 `dataset builder`
3. 建立 `reward adapter`
4. 建立 `prompt rollout agent`
5. 运行 `Trainer.dev()`
6. 训练 `summary prompt`
7. 跑 `holdout` 对比评测
8. 决定是否继续训练第二个 prompt
9. 只有在 prompt 收益见顶后，再评估 `VERL`
