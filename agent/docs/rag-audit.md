# 混合 RAG（结构化 + 语义）架构完整性审计

## 快速审核入口

### 30 秒审核版
- 你不需要先读完整报告。
- 只要先确认下面 `6` 个决策，我就可以基于你的选择继续推进后续 todo。
- 如果你时间很少，优先看“推荐默认选项”和“可直接回复模板”。

### 你只需要先确认这 6 件事
| 编号 | 待确认事项 | 当前审计判断 | 推荐默认选项 | 你需要确认什么 |
|---|---|---|---|---|
| R1 | 默认主图是否以并行融合为唯一主线 | 当前是 | 同意 | 是否接受后续所有文档、测试、改造都以 `parallel_fusion` 为准，`legacy_router` 仅作为 fallback |
| R2 | 是否接受 `pure_sql` 双实现现状 | 不建议接受 | 不接受 | 是否同意后续收敛为一个统一 SQL executor |
| R3 | 是否接受 `hybrid` 双实现现状 | 不建议接受 | 不接受 | 是否同意后续收敛为一个统一 Hybrid executor |
| R4 | 最终答案是否必须带引用/出处 | 当前缺失 | 至少补最小 citation | 是否要求下一阶段补最小 citation |
| R5 | Query rewrite 是否只保守增强 | 当前建议是 | 保守 | 是否同意继续保持“保守 rewrite”，暂不做激进扩写 |
| R6 | 评估体系是否先补可观测性再补能力增强 | 建议如此 | 先补完整性 | 是否认同先补指标/trace/citation，再做 rerank / decomposition / HyDE |

### 建议你优先拍板的决策
- `决策 A`：是否把 `parallel_fusion` 定为唯一主图口径
- `决策 B`：是否启动 `SQL/Hybrid` 双实现收敛
- `决策 C`：是否要求答案级 citation 成为下一阶段硬约束
- `决策 D`：是否把 query rewrite 保持为“保守模式”

### 可直接回复模板
```text
A. 主图口径：同意 / 不同意 / 需讨论
B. SQL 收敛：同意 / 不同意 / 需讨论
C. Hybrid 收敛：同意 / 不同意 / 需讨论
D. Citation：必须 / 可延期 / 不需要
E. Rewrite 策略：保守 / 增强 / 需讨论
F. 后续优先级：先补完整性 / 先补效果 / 并行推进
```

### 我的默认推荐
- `A. 主图口径`：同意
- `B. SQL 收敛`：同意
- `C. Hybrid 收敛`：同意
- `D. Citation`：必须
- `E. Rewrite 策略`：保守
- `F. 后续优先级`：先补完整性

### 你已确认的审核结论
- `A. 主图口径`：同意，后续以 `parallel_fusion` 为主口径
- `B. SQL 收敛`：保持现有架构不变，不强行合并入口；后续重点解决内部能力漂移
- `C. Hybrid 收敛`：保持现有架构不变，不强行合并入口；后续重点解决内部能力漂移
- `D. Citation`：必须
- `E. Rewrite 策略`：保守
- `F. 后续优先级`：并行推进

### 这意味着后续动作应改为
- 不以“删除一个入口”作为目标
- 保留当前 `parallel` 主链与现有 `pure_sql/hybrid` 入口结构
- 重点收敛内部能力与契约：
  - 输出 schema 一致性
  - 配置项一致性
  - 错误处理与 fallback 一致性
  - 指标与 trace 一致性
  - citation 能力一致性

## 如何使用这份报告
- 如果你只想快速审核：先看“快速审核入口”和“需要你确认的事项”
- 如果你想看证据：直接查“Checklist 总表”
- 如果你想决定下一步：直接看“问题分级”“最小补全方案”“建议优先级排序”
- 如果你想知道哪些已被现有 todo 覆盖：看“与已有 todo 的映射”

## 审计范围
- 审计对象：当前 `pure_sql + hybrid` 双路混合 RAG，以及默认主图 `self_query -> query_classification -> parallel_retrieval_fusion -> final_answer -> summary`。
- 审计方式：只读代码、文档、配置、测试报告核查；不改业务代码、不做重构、不做性能 benchmark。
- 证据来源：代码路径、配置项、现有测试报告与仓库文档。所有判断均尽量给出直接证据；缺失项以“未发现实现”明确标注。

## 现状总览
- 默认运行主图：`parallel_fusion`，见 `agent/graph_builder.py::build_graph`、`_build_parallel_fusion_graph`。
- 旧路由主图仍保留：`legacy_router`，见 `agent/graph_builder.py::_build_legacy_router_graph`。
- 当前真实形态是“并行双路 + 分类加权融合”，而非单路二选一路由。
- 文档与运行态存在明显偏移：`agent/architecture.md`、`agent/graph_structure.md` 仍主要描述旧路由图。

## 需要你确认的事项

### 1. 主图口径是否正式切换
- 当前证据：
  - 运行态默认主图是 `parallel_fusion`
  - 文档主图仍是 `legacy_router`
- 我建议你确认：
  - 后续是否统一以“并行融合主图”为唯一标准口径
- 如果你确认“是”：
  - 后续所有架构图、测试、审计、改造都按并行主图推进
- 如果你确认“否”：
  - 需要明确保留双主图并为两套链路分别维护文档与测试

### 2. 是否接受 SQL 双实现继续存在
- 当前证据：
  - 正式 SQL 链：`pure_sql_node -> pure_sql sub_agent -> sql_tools`
  - 默认并行链：`parallel_retrieval_fusion_node::_run_sql_branch`
- 我建议你确认：
  - 后续是否要收敛为单一 SQL 执行实现
- 我当前建议：
  - 不建议继续长期双轨维护
- 你的当前决策：
  - 保持现有架构不变，不强制收敛为单入口；后续只解决内部能力漂移
- 因此后续补齐重点：
  - SQL 两条路径的字段输出要对齐
  - schema linking / enum 校准能力差异要补平
  - 错误与超时处理口径要补平

### 3. 是否接受 Hybrid 双实现继续存在
- 当前证据：
  - 正式 Hybrid 链：`hybrid_search_node -> hybrid_search sub_agent`
  - 默认并行链：`parallel_retrieval_fusion_node::_run_hybrid_branch`
- 我建议你确认：
  - 后续是否要收敛为单一 Hybrid 执行实现
- 我当前建议：
  - 不建议继续长期双轨维护
- 你的当前决策：
  - 保持现有架构不变，不强制收敛为单入口；后续只解决内部能力漂移
- 因此后续补齐重点：
  - Hybrid 两条路径的参数、fallback、错误透传要对齐
  - 结果 schema 与 citation 能力要对齐
  - 复杂 query 能力与默认链能力边界要明确

### 4. 最终答案是否需要最小 citation
- 当前证据：
  - 底层结果保留 `event_id/video_id/start_time/end_time`
  - 最终答案未正式生成 citation
- 我建议你确认：
  - 下一阶段是否要求“最终答案必须可引用回表行/片段”
- 我当前建议：
  - 至少补最小 citation

### 5. Query rewrite 的风险容忍度
- 当前证据：
  - 已新增 `self_query_node`
  - 为避免改坏结构化查询，当前已收敛到保守 rewrite
- 我建议你确认：
  - 后续是继续保守 rewrite，还是允许更强的 query expansion
- 我当前建议：
  - 在双路 executor 未收敛前，继续保守

### 6. 后续改造优先顺序
- 可选方向：
  - 先补完整性：文档、单一 executor、citation、指标
  - 先补效果：HyDE、多 query、rerank、decomposition
  - 并行推进
- 我当前建议：
  - 先补完整性，再补效果

## Checklist 总表
| 层级 | 检查项 | 状态 | 证据 / 说明 |
|---|---|---:|---|
| A 数据准备 | 结构化数据：表结构 / schema 文档化程度 | ✅ | `agent/db/schema.py` 是表结构真源；`agent/db/README.md` 说明字段变更以 `schema.py` 与 `sqlite_builder.py` 为准。 |
| A 数据准备 | 结构化数据：字段语义说明 | ⚠️ | `agent/db/schema.py` 有字段分区注释，但缺单独的数据字典文档；字段含义主要散落在注释和 builder 映射中。 |
| A 数据准备 | 结构化数据：外键关系维护 | ❌ | `agent/db/schema.py` 仅单表 `episodic_events`，无显式外键；`sqlite_builder.py` 虽启用 `PRAGMA foreign_keys=ON`，但当前 schema 未定义 FK。 |
| A 数据准备 | 非结构化数据：文档加载 | ✅ | `agent/db/sqlite_builder.py::_load_seed_rows` 从 `events_vector_flat` 载入事件并生成 `vector_doc_text`。 |
| A 数据准备 | 非结构化数据：切分策略 | ⚠️ | 当前以事件/轨迹级文本作为单条向量文档，见 `vector_doc_text`、`vector_ref_id`；未见更细粒度 chunk 策略。 |
| A 数据准备 | 非结构化数据：元数据抽取 | ✅ | `sqlite_builder.py` 写入 `object_type/object_color_en/scene_zone_en/metadata_json/vector_ref_id`，Chroma 侧检索消费 metadata。 |
| A 数据准备 | 嵌入模型选型与版本管理 | ⚠️ | `agent/tools/llm.py` 硬编码 `text-embedding-v3`、`dimensions=1024`；未见版本注册、切换策略或 embedding schema version。 |
| A 数据准备 | 向量库索引结构 | ✅ | `agent/tools/db_access.py::ChromaGateway` 使用 `chromadb.PersistentClient` 和 `hnsw:space=cosine`。 |
| A 数据准备 | 向量库更新 / 重建机制 | ⚠️ | 有 `agent/db/manage_graph_db.py` 的 SQLite build/switch，但主链未见统一 Chroma 重建 CLI；仅有 `agent/db/chorma_test_runner.py` 测试脚本。 |
| A 数据准备 | 结构化数据与向量数据的关联关系 | ✅ | SQLite 中写入 `vector_ref_id`、`metadata_json`；Fusion 用 `event_id` 或 `video_id/track_id/start_time/end_time/summary` 对齐，见 `fusion_engine.py::_row_key`。 |
| B 查询处理 | Query 意图识别（结构化 / 语义 / 混合） | ✅ | `agent/node/query_classification_node.py` + `agent/agents/shared/query_classifier.py` 已实现结构化标签输出。 |
| B 查询处理 | Query 改写 / 扩展 | ⚠️ | 已有 `agent/node/self_query_node.py` 做保守 rewrite；未发现 HyDE、multi-query、同义词扩展专门实现。 |
| B 查询处理 | Query 分解（复杂问题拆子问题） | ❌ | 未发现 subquestion / decomposition 逻辑；grep 未命中相关实现。 |
| B 查询处理 | 结构化路径：NL2SQL schema linking | ✅ | `agent/agents/pure_sql/sub_agent.py` 强制 `inspect_database_schema` 和 `inspect_column_enum_values` 校准。 |
| B 查询处理 | 结构化路径：字段映射 | ⚠️ | 正式 `pure_sql` 子 agent 有 schema sniff；但并行主链 `_run_sql_branch` 仅靠 `_extract_filters` 的启发式词表。 |
| B 查询处理 | 结构化路径：歧义消解 | ⚠️ | `inspect_column_enum_values` 可做枚举校准；但仅在正式 `pure_sql` sub-agent 中，默认并行 SQL 分支未复用。 |
| B 查询处理 | 语义路径：向量化前规范化 / 清洗 | ⚠️ | `self_query_node` 与 `_normalize_query_text` 做轻量清洗；未见更系统的 query normalization pipeline。 |
| C 检索 | `pure_sql`：SQL 生成质量 | ⚠️ | 正式链通过 ReAct + 工具调用生成 SQL；默认并行主链未复用，而是 `_run_sql_branch` 直接拼条件 SQL。 |
| C 检索 | `pure_sql`：执行安全性（注入防护） | ⚠️ | `execute_dynamic_sql` 只允许 `SELECT`，但仍执行原始字符串；并行 `_run_sql_branch` 用参数化较安全。整体无统一 SQL 安全层。 |
| C 检索 | `pure_sql`：超时 | ❌ | 未见 SQLite 级 query timeout；仅并行节点层有 branch timeout。 |
| C 检索 | `pure_sql`：行数限制 | ✅ | `execute_dynamic_sql` 大结果截断到 50 条；并行 `_run_sql_branch` `LIMIT 80`。 |
| C 检索 | `pure_sql`：结果 schema 一致性 | ⚠️ | 正式 SQL 子 agent 与并行 `_run_sql_branch` 返回字段不完全一致；并行分支更贴近 fusion 需求。 |
| C 检索 | `hybrid`：向量检索 | ✅ | `agent/tools/hybrid_tools.py::dynamic_weighted_vector_search` 调用 `ChromaGateway.search`。 |
| C 检索 | `hybrid`：关键词检索（BM25 / 全文） | ✅ | `agent/tools/db_access.py::ChromaGateway._bm25_scores` 实现 BM25，并与 cosine 线性融合。 |
| C 检索 | `hybrid`：top-K 配置 | ⚠️ | `dynamic_weighted_vector_search` 有 `limit`、`alpha`；并行主链写死 `limit=50`，未统一接 `search_config`。 |
| C 检索 | 两路结果格式可对齐 | ✅ | 融合前均标准化到 `video_id/start_time/end_time/event_summary_en` 等字段，见 `parallel_retrieval_fusion_node.py`。 |
| C 检索 | 两路 score 同量纲 / 归一化 | ⚠️ | Hybrid 内部有 cosine/BM25 归一化；SQL 侧无天然 score，只在 fusion 阶段通过 rank-based RRF 规避量纲问题。 |
| D 融合/后处理 | 当前融合逻辑 | ✅ | `agent/node/parallel_retrieval_fusion_node.py` + `agent/agents/shared/fusion_engine.py` 使用 Weighted RRF，并支持单路失败降级。 |
| D 融合/后处理 | Rerank（cross-encoder / LLM rerank） | ❌ | `rerank_result` 当前只是融合结果别名或原始 rows；未发现 cross-encoder / LLM rerank 实现。 |
| D 融合/后处理 | 上下文压缩 / 去重 | ⚠️ | Fusion 通过 `_row_key` 去重；但没有单独的上下文压缩器，SQL 行与语义片段仅做轻量合并。 |
| D 融合/后处理 | 上下文长度控制（token budget） | ⚠️ | `summary_node` 限制 `max_tokens=120`；但检索上下文整体无统一 token budget 管理。 |
| D 融合/后处理 | 引用 / 溯源保留 | ⚠️ | 结果保留 `event_id/video_id/start_time/end_time/_fusion_trace`；但最终答案未生成正式 citation，也未区分“表行引用”与“文档片段引用”。 |
| E 生成 | Prompt 模板管理 | ⚠️ | 有 `router_prompts.py`、`init/agent_init_prompt.md`、sub-agent prompt 常量；但未见模板版本化或集中注册。 |
| E 生成 | 结构化结果与语义结果的上下文注入方式 | ⚠️ | `final_answer_node` 直接拼接文本行，`summary_node` 输入 top results 列表；未统一为表格 / Markdown / JSON 注入协议。 |
| E 生成 | 幻觉检测 / 答案支撑校验 | ❌ | 未见专门的 grounding / verify 节点接入主链。 |
| E 生成 | 引用生成（citation to 表 / 行 / 文档） | ❌ | 最终输出无 citation 格式；仅保留底层 `event_id/video_id` 信息。 |
| E 生成 | 流式输出支持 | ⚠️ | 图执行使用 `graph.stream(..., stream_mode="values")`；但用户级最终总结未实现 token streaming，仅节点状态流。 |
| F 可观测性 | 两路各自命中率 / recall 指标 | ⚠️ | `comprehensive_test_trends.md` 有 `semantic_label_cases_with_zero_hybrid_rows` 等代理指标；但无正式线上 recall 仪表板。 |
| F 可观测性 | 端到端答案质量评估机制 | ✅ | `agent/test/comprehensive_test_runner.py`、`result_test_runner.py`、报告 JSON/MD 已形成评测流程。 |
| F 可观测性 | 全链路 trace | ✅ | state 中有 `classification_result/self_query_result/sql_debug/routing_metrics/cot_context`，测试报告也记录这些关键字段。 |
| F 可观测性 | Fallback 策略 | ✅ | 并行节点支持 `sql_failed/hybrid_failed/both_failed/structured_zero_guardrail`，`summary_node` 和 `answer_node` 也有空结果 fallback。 |

## 关键发现

### 1. 主图已切为并行融合，但核心文档仍停留在旧路由图
- 运行态证据：`agent/graph_builder.py` 默认 `AGENT_EXECUTION_MODE=parallel_fusion` 时走 `self_query_node -> query_classification_node -> parallel_retrieval_fusion_node -> final_answer_node -> summary_node`。
- 文档证据：`agent/architecture.md` 和 `agent/graph_structure.md` 仍描述 `tool_router -> hybrid_search/pure_sql -> reflection -> final_answer`。
- 影响：后续若继续在过时架构图上做优化，容易把审计、改造、测试口径做散。

### 2. `pure_sql` 和 `hybrid` 都存在“正式 sub-agent”与“默认并行分支直连实现”双轨
- `pure_sql` 正式链：`agent/node/pure_sql_node.py` -> `agent/agents/pure_sql/sub_agent.py` -> `agent/tools/sql_tools.py`
- 默认并行链：`agent/node/parallel_retrieval_fusion_node.py::_run_sql_branch`
- `hybrid` 正式链：`agent/node/hybrid_search_node.py` -> `agent/agents/hybrid_search/sub_agent.py`
- 默认并行链：`agent/node/parallel_retrieval_fusion_node.py::_run_hybrid_branch`
- 影响：功能可用，但会长期造成质量、配置、异常处理、观测字段漂移。

### 3. 混合 RAG 的“基础骨架”完整，但高级增强项仍明显缺位
- 已有：双路执行、分类偏置、BM25+向量、Weighted RRF、降级、测试报告。
- 缺位：HyDE、多查询扩展、query decomposition、专用 rerank、citation、grounding check、统一 token budget。

### 4. 数据对齐基础存在，但仍有混合场景特有风险
- 好处：SQLite 写入了 `vector_ref_id`、`metadata_json`，Fusion 通过 `event_id` 或自然键对齐。
- 风险：Hybrid 结果中 `event_id` 可能来自 Chroma 文档 ID，不一定稳定等于 SQLite 自增 `event_id`；当回退到自然键对齐时，若 `summary` 文本漂移，可能影响融合去重稳定性。

## 问题分级

### P0
1. 默认并行主链与核心文档不一致  
   - 影响：架构理解、审计口径、后续优化方向都可能偏离真实运行链。
2. `pure_sql` 双实现漂移  
   - 影响：一个路径做 schema linking，一个路径做启发式拼条件，结果质量和安全策略无法统一。
3. `hybrid` 双实现漂移  
   - 影响：正式 sub-agent 支持更丰富工具调用，而默认主链未复用，后续功能会继续分叉。
4. 结构化与语义来源的 citation 未落地  
   - 影响：答案可读，但难以审计“答案是否被检索内容支撑”。

### 这一组 P0 需要你优先审核
| 问题 | 我的建议 | 你需要决定什么 |
|---|---|---|
| 主图文档与运行态不一致 | 立即统一 | 是否接受只保留并行主图为主口径 |
| `pure_sql` 双实现漂移 | 保持架构不变，补平内部能力 | 是否接受“不改架构，只治理漂移” |
| `hybrid` 双实现漂移 | 保持架构不变，补平内部能力 | 是否接受“不改架构，只治理漂移” |
| citation 缺失 | 下一阶段补 | 是否把 citation 定为硬要求 |

### P1
1. 字段语义 / 数据字典缺失
2. Query rewrite 仅轻量实现，缺同义词、HyDE、multi-query
3. 复杂问题拆解缺失
4. SQL timeout 与统一安全层缺失
5. 无专用 rerank / context compression / token budget 管理
6. 缺正式 recall / hit-rate 仪表板，只能依赖测试报告代理指标

### P2
1. Prompt 模板未版本化
2. 流式输出仅到状态流，不是用户级 token streaming
3. Chroma 重建机制未收敛到统一运维入口

## P0 / P1 的最小补全方案

| 级别 | 问题 | 最小补全方案 | 估算改造量 |
|---|---|---|---|
| P0 | 文档与运行态不一致 | 先更新 `architecture.md`、`graph_structure.md`、`routing_rules.md`，明确默认主链、`legacy_router` 的定位和状态契约。 | 小 |
| P0 | `pure_sql` 双实现漂移 | 抽一个统一 SQL executor，让并行主链优先复用 `run_pure_sql_sub_agent` 或其安全子集；至少统一 schema linking / enum calibration / 输出字段。 | 中 |
| P0 | `hybrid` 双实现漂移 | 抽一个统一 Hybrid executor，让并行主链和 legacy 共用同一 `alpha/limit/fallback` 与工具调用入口。 | 中 |
| P0 | citation 缺失 | 在最终输出里至少保留 `video_id + event_id/start_time` 的可读引用；先不做完整 citation 样式，也能显著提升可审计性。 | 小 |
| P1 | 数据字典缺失 | 新增一份字段字典文档，按 `schema.py` 和 `sqlite_builder.py` 汇总。 | 小 |
| P1 | query rewrite 能力弱 | 在 `self_query_node` 上增加可选扩展层，但默认关闭；先从同义词表和 query normalization 开始。 | 中 |
| P1 | query decomposition 缺失 | 先只做“复合问题拆成并列子 query”的最小版，不碰复杂 planner。 | 中 |
| P1 | SQL timeout / 安全层不足 | 在 SQLite 执行入口统一加 query 白名单、行数限制和超时/中断机制。 | 中 |
| P1 | 无专用 rerank / compression | 先加轻量 rerank 或基于 `_fusion_trace` 的规则后排，再评估是否需要 cross-encoder。 | 中 |
| P1 | 评估指标不足 | 复用现有 `comprehensive_test_runner.py`，增加两路 hit-rate / fallback-rate / citation coverage 统计即可。 | 小 |

## 与已有 todo 的映射

### 已被现有 todo 覆盖
- `todo 11`：并行融合主链、双路执行、加权融合、超时降级  
  - 本次审计结论：已落地，但需继续解决“双实现漂移”。
- `todo 12`：统一自查询节点与最终总结节点  
  - 本次审计结论：已落地，但 query rewrite 仍属于轻量版本。
- `todo 6`：init 阅读流程  
  - 本次审计结论：已为 query/routing 提供先验上下文，但还不是完整 prompt registry。

### 本次新发现，建议新增的 todo
- 建议新增：主图文档收敛任务  
  - 更新 `architecture.md`、`graph_structure.md`、`routing_rules.md`
- 建议新增：SQL 能力漂移治理任务  
  - 在不改当前架构的前提下，补平 `run_pure_sql_sub_agent` 与 `_run_sql_branch` 的能力与契约差异
- 建议新增：Hybrid 能力漂移治理任务  
  - 在不改当前架构的前提下，补平 `run_hybrid_sub_agent` 与 `_run_hybrid_branch` 的能力与契约差异
- 建议新增：citation 最小落地任务  
  - 在最终答案中区分结构化来源和语义来源
- 建议新增：评估指标补齐任务  
  - 两路 hit-rate / fallback-rate / citation coverage / grounding coverage

## 建议你快速审核的新增 todo 候选
| 候选 todo | 是否建议新增 | 原因 | 建议你确认 |
|---|---|---|---|
| 主图文档收敛 | 是 | 当前文档与运行态不一致 | 是否立即加入主线 |
| SQL 能力漂移治理 | 是 | 不改架构前提下补平内部差异 | 是否作为 P0 |
| Hybrid 能力漂移治理 | 是 | 不改架构前提下补平内部差异 | 是否作为 P0 |
| citation 最小落地 | 是 | 提升可审计性 | 是否作为 P0 或 P1 |
| 指标补齐 | 是 | 支撑后续优化 | 是否作为 P1 |

## 混合场景特有风险

### 1. 结构化与语义数据不一致
- SQL 与 Chroma 都来源于同批篮球数据，但一个强调字段，一个强调 `vector_doc_text`。
- 当 `event_summary_en` 或 metadata 抽取规则调整后，语义侧和 SQL 侧可能出现“同一事件描述不同步”。

### 2. schema 漂移风险
- `schema.py` 是 SQLite 真源，但 Chroma metadata 字段名来自 builder 映射和 gateway 输出。
- 如果未来改 `object_color_en/scene_zone_en/vector_ref_id` 命名，SQL 与 Chroma 需要同步迁移，否则 filter / fusion 会隐性失真。

### 3. 实体对齐失败风险
- Fusion 先用 `event_id`，否则退化到 `video_id + track_id + start_time + end_time + summary` 自然键。
- 若 Chroma 文档 ID 与 SQLite `event_id` 不一一对应，或者 summary 文本更新导致自然键漂移，去重和融合稳定性会下降。

### 4. 双路策略分叉风险
- 现在“正式 sub-agent 链”和“默认并行分支直连链”共存，是当前混合场景里最大的架构风险。
- 这不是短期 bug，而是会持续制造“测试通过但能力并不统一”的系统性问题。

## 不适用项说明
- “外键关系维护”：当前单表事件库设计中不适用复杂关系型外键建模，但若未来拆实体表/视频表，则需补回。
- “性能 benchmark”：本次按要求不做性能基准评估，只引用现有测试趋势作为可观测性证据，不做性能审判。

## 建议优先级排序
1. 先统一文档与真实主图，停止“旧文档指导新系统”
2. 统一 `pure_sql` executor，消除双轨
3. 统一 `hybrid` executor，消除双轨
4. 落最小 citation，提升答案可审计性
5. 补两路指标与 grounding 覆盖率
6. 再考虑 query rewrite 增强、query decomposition、rerank 等效果优化

## 最终请你确认
- 是否确认 `parallel_fusion` 为唯一主图口径
- 是否确认新增“SQL 能力漂移治理”
- 是否确认新增“Hybrid 能力漂移治理”
- 是否确认“citation”进入下一阶段
- 是否确认“并行推进”的排序

## 一句话结论
- 当前混合 RAG 已具备“可运行、可测试、可降级”的完整骨架，但还没有达到“单一实现、单一文档、单一契约”的完整态；在继续做更深的融合优化之前，最该先补的是文档与双实现收敛。
