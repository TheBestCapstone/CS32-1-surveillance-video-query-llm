# lightingRL 工作记录

- 更新时间: `2026-05-01`
- 记录方式: 每一步按 `计划`、`执行`、`结果` 记录，后续继续追加。

## Step 1 需求拆解
- 计划: 在 `agent/lightingRL` 下建立工作区，并补齐 `work.md`、`todo.md`、`plan.md`。
- 执行: 确认用户目标是基于 `Agent-lightning/LightningRL` 为现有 `agent` 设计一套可训练、可调 prompt 的接入方案。
- 结果: 任务范围收敛为三部分：仓库调研、框架调研、方案文档落盘。

## Step 2 仓库现状调研
- 计划: 查清当前 `agent` 的默认执行链、实际生效的 prompt、评测与数据入口。
- 执行: 阅读了 `agent/graph.py`、`agent/graph_builder.py`、`agent/node/self_query_node.py`、`agent/agents/shared/query_classifier.py`、`agent/node/summary_node.py`、`agent/test/ragas_eval_runner.py` 等文件。
- 结果: 当前默认主链路是 `parallel_fusion`，即 `self_query -> query_classification -> parallel_retrieval_fusion -> final_answer -> summary`。
- 结果: 默认真正会跑到的 prompt 主要是 `self_query`、`query classification`、`summary`。
- 结果: `init prompt` 与 `router prompts` 仅在 `legacy_router` 模式下生效，不适合作为第一批训练目标。
- 结果: `agent/test/ragas_eval_runner.py` 已具备 `case rollout -> contexts/response 采集 -> RAGAS 打分 -> summary 汇总` 的离线评测骨架。

## Step 3 Agent-lightning / LightningRL 调研
- 计划: 确认该框架支持什么训练形态，尤其是否适合 prompt 优化与现有 LangGraph agent 接入。
- 执行: 调研了官方文档与 GitHub 示例，重点查看了 `Train the First Agent`、`Agent Developer APIs`、`train_sql_agent`、`train_rag.py`。
- 结果: `Agent-lightning` 的核心抽象是 `task`、`rollout`、`span`、`prompt template`。
- 结果: 若目标是先“训练并修改 prompt”，最适合优先采用 `prompt_rollout + APO`。
- 结果: 若后续要继续做模型权重训练，可再引入 `LitAgent + Trainer + VERL`。
- 结果: `Trainer.dev()` 适合先做干跑，验证 trace、reward、数据库连接和 graph 控制流是否正常。

## Step 4 方案决策
- 计划: 结合仓库现状与框架能力，给出一条风险最低、收益最高的落地路径。
- 执行: 对比了“直接上 VERL 训练模型权重”和“先做 APO 优化 prompt”两条路线。
- 结果: 建议采用“两阶段接入”。
- 结果: 第一阶段只优化 prompt，不改现有模型权重，优先训练 `summary`、`query classification`、`self_query` 三类 prompt。
- 结果: 第二阶段只有在离线收益稳定后，再选择性把 `summary` 或路由相关节点升级到 `VERL`。
- 结果: 第一阶段不要训练 `legacy_router` 的 prompt，也不要把多个 prompt 一起绑成一个大 bundle 直接优化。

## Step 5 文档交付
- 计划: 将调研结论、实施步骤、风险与交付项写入文档。
- 执行: 生成 `agent/lightingRL/todo.md` 与 `agent/lightingRL/plan.md` 的内容结构，并同步本文件中的工作记录。
- 结果: `lightingRL` 工作区已建立，后续实现时可继续在该目录追加训练脚本、数据转换脚本与实验记录。

## Step 6 prompt 抽离与 smoke test
- 计划: 将默认主链路当前实际生效的 prompt 抽离为统一 `registry`，并通过最小 `smoke test` 验证行为不变。
- 执行: 新增 `agent/lightingRL/prompt_registry.py` 与 `agent/lightingRL/__init__.py`，统一管理 `self_query`、`query classification`、`summary` 三组 prompt。
- 执行: 修改 `agent/node/self_query_node.py`、`agent/agents/shared/query_classifier.py`、`agent/node/summary_node.py`，将原内嵌 prompt 改为从 `prompt registry` 读取。
- 执行: 新增 `agent/test_somke/prompt_registry_smoke_test.py`，使用假 `LLM` 对 3 个调用点做无外部依赖验证。
- 结果: 默认主链路 prompt 已完成抽离，调用点已切换到统一 `registry`。
- 结果: `python agent/test_somke/prompt_registry_smoke_test.py` 已通过，确认 system prompt、user prompt、输出结构与 citation 追加逻辑正常。
