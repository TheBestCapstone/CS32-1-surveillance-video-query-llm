# Agent 下一步 Todo

> 维护方式：每完成一项就修改状态，并补充“结果/阻塞/下一步”。

## 状态约定
- `PENDING`：未开始
- `IN_PROGRESS`：进行中
- `DONE`：已完成
- `BLOCKED`：阻塞

## 任务列表
1. `DONE` 建立初始化文档  
目标：提供一段可持续迭代的初始化提示词，用于启动 Agent（角色、目标、约束、输入输出约定、失败处理）。  
结果：已接入 `build` 流程自动生成（去重 `keywords/object_type/object_color`）。

2. `DONE` 确认 SQLite 数据库建立方式并评估是否修改  
目标：对比当前 `agent/db/sqlite_builder.py` 与业务数据源的字段差异，确定是否要增加新字段、索引、迁移脚本。  
结果：已重设计 SQL/向量互补字段并新增 `修改数据库.md` 快速同步手册。

3. `DONE` 设计并测试“当前数据 -> Chroma”流程（先不改现有代码）  
目标：基于 `events_vector_flat` 明确 embedding 模型、metadata 结构、切片策略、写入与检索约束。  
结果：已完成 embedding 模型可用性、cosine/BM25/混合检索测试，并确认当前 Chroma 为 `track-level` 切片（26 条记录来自 27 条事件聚合）。

4. `DONE` 梳理当前 agent 代码架构（盘点、识别无用代码、重构计划、文档化）  
目标：先输出模块清单（职责/依赖/调用方）供确认，确认后再进入无用代码识别与解耦重构。  
结果：已完成模块盘点、无用代码识别、解耦 Stage 1/2/3/4 与模块文档化，并通过 TC01 回归；详见 `agent/step4_cleanup_temp.md`。

5. `DONE` 将图中的向量接口替换为 Chroma  
目标：替换向量检索底座（连接、建索引、写入、检索接口），并保证 `hybrid` 路径可回归通过。
结果：已切换 `hybrid_tools` 到 Chroma 网关并完成可运行验证（TC01/TC04）；已补充 `LanceDB回滚说明.md`，后续默认不再维护 LanceDB。

## 下一阶段任务（篮球数据）
6. `DONE` 改写 agent 逻辑，增加 init 阅读流程  
目标：在 agent 启动/路由前读取 `init/Agent Initialization Prompt`，作为初始化上下文。  
结果：已在 `graph -> graph_builder -> tool_router` 链路接入 `init/agent_init_prompt.md` 读取与注入。

7. `DONE` 篮球数据落地改造计划  
目标：以当前篮球数据作为主数据源，完成数据清理、初始化接入、测试重建与端到端跑通。  
结果：8/9/10 均已完成，篮球数据链路可运行。

8. `DONE` 删除 mock_data 与 mvp_data  
目标：移除历史样例数据目录，减少歧义数据源与维护成本。  
结果：已删除 `/agent/mock_data` 与 `/agent/mvp_data` 目录。

9. `DONE` 用篮球数据初始化数据库并重设计 5 条测试用例  
目标：基于当前篮球数据重建数据库，替换现有测试样例，形成 5 条有效用例。  
结果：数据库已重建为篮球数据（27 行），`result_cases.json` 已改为 5 条篮球场景用例。

10. `DONE` 跑通篮球数据版 agent  
目标：完成端到端运行验证，确保主链路可执行、结果可返回、无运行时异常。  
结果：`result_test_runner.py` 全量 5/5 通过（pass_rate=1.0）。

## 执行顺序建议
- 当前主线任务：任务 6（篮球数据全面落地）
- 建议顺序：`7 -> 8 -> 9 -> 10`

## 新增任务（并行融合改造）
11. `DONE` pure_sql 与 hybrid 执行策略改造（路由二选一 -> 并行融合）  
目标：每次查询并行执行 `pure_sql` 与 `hybrid`，通过独立分类器输出 `structured/semantic/mixed` 并进行可配置加权融合；保留旧路由为 feature flag 回切。  
结果：已落地 `query_classification_node + parallel_retrieval_fusion_node`，融合采用 Weighted RRF，支持超时降级；`AGENT_EXECUTION_MODE=legacy_router` 可回切旧路由；篮球 5 用例回归通过。

12. `DONE` 新增统一自查询节点与最终总结节点  
目标：在所有检索节点前统一加入 `self_query_node`，完成原始输入预处理、意图澄清、查询改写与需求识别；在流程末尾新增 `summary_node`，基于上游结果生成符合英语母语者表达习惯的友好总结，并为 CoT/需求识别提供可验证的结构化观测字段。  
结果：已完成 `self_query_node -> 检索/路由节点 -> final_answer_node -> summary_node` 链路接入；统一查询入口支持 `rewritten_query/optimized_query`；综合测试报告已新增 `self_query_result/raw_final_answer/llm_final_output` 观测字段；综合测试 11/11 通过，篮球回归 5/5 通过。

13. `DONE` 混合 RAG（结构化 + 语义）架构完整性审计  
目标：在进一步做融合改造、子 agent 接口统一等工作前，对当前 `pure_sql + hybrid` 双路混合 RAG 做完整性审计，按数据准备、查询处理、检索、融合/后处理、生成、可观测性与评估逐项核查，确认关键环节无缺失。  
结果：已完成只读审计并输出报告 `agent/docs/rag-audit.md`；报告包含 checklist 状态总览、P0/P1 分级、最小补全方案、与已有 todo 的映射、混合场景特有风险与建议优先级。

## 审计后执行任务（按优先级）

### P0
14. `DONE` 主图文档收敛（以 `parallel_fusion` 为唯一主口径）  
目标：统一 `architecture.md / graph_structure.md / routing_rules.md` 与真实运行主图，明确 `legacy_router` 仅为 fallback。  
结果：已完成三份主图文档同步，默认图已更新为 `self_query -> query_classification -> parallel_retrieval_fusion -> final_answer -> summary`，并明确 `legacy_router` 仅作 fallback。

15. `DONE` SQL 能力漂移治理（保持现有架构不变）  
目标：不合并入口，只补平 `run_pure_sql_sub_agent` 与 `_run_sql_branch` 的输出 schema、校准能力、错误处理与配置契约差异。  
结果：已完成首轮治理；新增统一检索契约层，补齐默认主链 `routing_metrics/search_config/sql_plan` 写回，统一 SQL 结果 schema，并让 `pure_sql_node` 与并行主链共享输出契约。

16. `DONE` Hybrid 能力漂移治理（保持现有架构不变）  
目标：不合并入口，只补平 `run_hybrid_sub_agent` 与 `_run_hybrid_branch` 的参数、fallback、错误透传、结果 schema 与 citation 能力差异。  
结果：已完成首轮治理；统一 Hybrid 结果 schema，补齐 `event_id/end_time/object_type/object_color_en/scene_zone_en/hybrid_score/bm25` 等字段透传，统一默认主链与 `hybrid_search_node` 的配置契约，并验证最终 `Sources:` 可携带 Hybrid 引用。

17. `DONE` citation 最小落地  
目标：在最终答案中增加可审计的最小引用信息，至少能回溯到 `video_id + event_id/start_time/end_time`，并区分结构化/语义来源。  
结果：已在 `summary_node` 中落地最小引用拼接，最终答案追加 `Sources:`，区分 `sql/hybrid/mixed` 来源；综合测试与篮球回归已验证通过。

### P1
18. `DONE` 混合 RAG 指标与 trace 补齐  
目标：补齐两路 hit-rate / fallback-rate / citation coverage / grounding coverage 等指标，并统一报告口径。  
结果：已在 `comprehensive_test_runner.py` 与 `result_test_runner.py` 落地；报告新增 `metrics_summary`、`node_trace`、`routing_metrics`、`search_config`、`sql_plan`、`summary_result` 等观测字段，补齐 citation coverage / grounding coverage / trace coverage / routing metrics coverage / 分支非空率 / degraded rate 等指标；综合测试与篮球回归均通过。

19. `DONE` 数据字典与字段语义文档  
目标：补充 SQLite/Chroma 关键字段的数据字典，降低 schema 漂移与误用风险。  
结果：已新增文档 `agent/docs/data-dictionary.md`，统一说明 `SQLite 真表`、`Chroma/Hybrid 输出`、运行态统一检索契约、字段映射规则、易混字段与使用建议，作为当前字段语义的单一参考口径。

20. `DONE` Query rewrite 增强边界梳理  
目标：在“保守 rewrite”前提下，明确哪些增强允许做、哪些不允许做，并形成约束文档。  
结果：已新增文档 `agent/docs/query-rewrite-boundaries.md`，明确 `self_query_node` 的允许增强、禁止增强、按意图类型的 rewrite 约束、未来 `HyDE/multi-query/decomposition` 的准入条件，以及回归测试建议。

### P2
21. `DONE` Prompt 模板与版本化治理  
目标：梳理 init/router/summary/sub-agent prompt 的复用与版本管理方式。  
结果：已新增 `agent/docs/prompt-governance.md` 与 `agent/docs/prompt-registry.json`，建立当前 prompt 资产清单、`prompt_id/version` 命名规则、变更准入原则与最小版本治理模型。

22. `DONE` 流式输出与上下文预算治理  
目标：评估用户级 streaming 与统一 token budget 管理方案，但暂不作为主线阻塞项。  
结果：已新增文档 `agent/docs/streaming-token-budget.md`，梳理当前 `graph.stream`、summary 输出上限、检索候选规模控制现状，并形成统一 `query/retrieval/generation` 预算建议与用户级 streaming 准入规则。
