# Agent 项目改进 Todo

> 改造原则：不动外层 LangGraph 主图结构，只在节点内部、数据层与融合层做增量改造。所有改造保持下游 `answer_node` / `summary_node` / `ragas_eval_runner.py` 兼容。
>
> 配套文档：
>
> - `agent/handoff.md` — **给下一个 agent 的交接快照（优先读）**
> - `agent/调试记录.md` — 全 session 完整复盘
> - `agent/data_audit_2026_05_02.md` — 父子索引架构调研
> - `agent/recall_diagnosis_2026_05_02.md` — context_recall 低值诊断 ⭐

---

## 本轮工作总结（2026-05-03）

- **图与清理**：仅保留并行融合路径；删除 legacy router / `merged_result` / `SQLiteGateway` 等（P1-5 + P3-3）。
- **存在性链路**：P1-Next-A 收紧 summary bail-out；P1-7 v2.3 重选 span + follow-up 已修。
- **评测去噪（P1-Next-F）**：R1/R2/R3；**Part1 50-case** context_recall +0.19（0.36→0.55）。
- **P1-Next-G R4**：metadata 净化（`Keywords:` 剥离）、reranker A/B（bge-v2-m3 不如 ms-marco）、**Step 1 已修**：禁用 `AGENT_RERANK_METADATA_IN_QUERY`（默认 OFF），消除跨视频噪声。
- **P1-Next-G R6**：self_query_node 扩展 `expansion_terms`，LLM 对抽象 query 生成具体可观测替代词。
- **导入切换**：默认仅 Part4（`DEFAULT_INCLUDE_SHEETS = ["Part4"]`），104 个 Normal_Videos 种子已补全。
- **IoU**：Part4 14/15 eligible（IoU 0.594）；修复 `expected_answer_label == "no"` 时不应算 IoU 的 bug。

---

## 当前已知瓶颈（截至 2026-05-03，Part4 15-case 基线）


| 指标                           | Part4 15-case | 目标     | 说明                                     |
| ---------------------------- | ------------- | ------ | -------------------------------------- |
| `top_hit_rate`               | 0.867         | ≥ 0.90 | Normal_Videos 检索比 UCFCrime 难           |
| `context_precision_avg`      | **0.697**     | ≥ 0.75 | R4 Step1 fix 后已回升（+0.024 vs pre-R4R6）  |
| `context_recall_avg`         | 0.700         | ≥ 0.75 | R6 expansion 已 +0.04；余量在 R4 Step2 / R8 |
| `time_range_overlap_iou_avg` | 0.594         | ≥ 0.60 | 14/15 eligible，口径已修复                   |
| `custom_correctness_avg`     | 0.763         | ≥ 0.80 | Part4 video_match 是瓶颈                  |
| `ragas_e2e_score_avg`        | 0.690         | ≥ 0.75 | 用 custom_correctness 参与合成              |


---

## 评测流程（每次跑完 `ragas_eval_runner.py`）

1. `**REPORT_TABLES.md`（必读）** — 汇总 RAGAS 指标、**自定义指标 `custom_correctness`**（§2.3 与 §6 明细）、任务原生时间/视频对齐、逐 case 宽表与 Verifier。
  - **默认**：runner 在写出 `e2e_report.json` / `summary_report.json` 后**自动**生成 `--output-dir/REPORT_TABLES.md`（`agent/test/eval_report_tables.py`）。不需要时加 `**--no-report-tables`**。  
  - **仅补生成**（改模板后重渲染、或历史 run 未生成）：  
  `python agent/test/scripts/regen_report_tables.py --output-dir <run 输出目录>`  
  - **RAGAS wall 耗时**：若 tee 日志为 `agent/test/generated/<与目录同名>.log`，脚本会自动匹配；否则加 `--log <路径>`。
2. 建议终端 `**tee`** 保存 `.log`，便于耗时与复盘。

---

# 已验收（Smoke 10-case，2026-05-02）


| 项                       | 结论                                                                                                                                                                                                                                                                                                                                     |
| ----------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **输出**                  | `agent/test/generated/ragas_eval_e2e_n10_unverified_20260502/`：`REPORT_TABLES.md`、`summary_report.json`、`e2e_report.json`；日志 `agent/test/generated/ragas_eval_e2e_n10_unverified_20260502.log`                                                                                                                                         |
| **子库**                  | `runtime/eval_subset.sqlite`、`runtime/eval_subset_chroma`；seed：`generated/datasets/ucfcrime_events_vector_flat`（4 视频）                                                                                                                                                                                                                  |
| **指标快照（本机该次 run，10 条）** | `context_precision_avg` **0.4876**；`context_recall_avg` **0.55**；`custom_correctness_avg` **0.7438**；`factual_correctness_avg` **0.8**；`faithfulness_avg` **0.7583**；`ragas_e2e_score_avg` **0.6349**；`top_hit_rate` **1.0**；`time_range_overlap_iou_avg` **0.2278**；`video_match_score_avg` **0.8889**（n=9）；RAGAS/Graph 错误 case **0** |
| **备注**                  | `reference_used_rich_count`=0：当前导入数据侧无可用 `reference_answer_rich` 或未命中富参考路径；smoke 结论**不依赖** rich，后续可单独修导入再对比。                                                                                                                                                                                                                           |


# 🚧 未完成（按优先级排序）

## IoU / 时间定位 ✅ 已解决（2026-05-03）

> 切到 Part4-only 后，15-case smoke 中 **14/15** 有 GT 时间窗（`time_range_overlap_iou_case_count=14`），IoU 均值 **0.594**。Part4 天然自带完整的 `expected_start_sec/expected_end_sec`，不再需要数据补全。
>
> 同时修复了 `expected_answer_label == "no"` 时不应计算 IoU 的 bug（`ragas_eval_runner.py` `_compute_custom_correctness`）。

---

## P1-Next-G retrieval 真实改造（按 ROI 排序；**P1-Next-F 已完成**，可启动 A/B 规划）

> 这一组改动会动 retrieval 真实链路。评测噪声（F1–F3）已通过 P1-Next-F 压低；剩余 recall 缺口以 R4/R6/R8 真改为主。来源：`recall_diagnosis_2026_05_02.md`。

### R4 reranker 升级 / metadata 净化 ✅ Step 1 DONE

> **已落地**：`Keywords:` 剥离、`AGENT_RERANK_METADATA_IN_QUERY` 默认 OFF（灰度口保留）、`_enrich_query_with_metadata`。
> **A/B 结论**：`bge-reranker-v2-m3` 不如 `ms-marco-MiniLM-L-6-v2`（precision -0.033, recall -0.037），保持旧模型。
> **Step 1 fix 已验证**：metadata-in-query OFF → 15-case precision 0.673→0.697，PART4_0014 precision +0.417。

#### 待做 Step 2（兜底，低成本）：reranker 顶上加 ulin abstention

**动机**：Step 1 之后「is there any X」类 negative query 的 reranker positive-class bias 仍可能存在。

**实施**：

1. 从 PART4 挑 ~50 条有 label 样本，跑 reranker 拿 score 向量，fit ridge regression（target mAP 或 precision@K）
2. 推理时算 ulin(z)，低于 τ 返回空（"No matching clip"）
3. τ 扫 abstention rate 10%/30%/50%，在 precision 与 recall 间找平衡
4. 成本：~50 行代码，延迟 ~1ms
5. 注意：按 query 类型分别 fit 或 "无答案" 类型单独走 binary classifier

### R6 Query 改写 / expansion ✅ DONE

- 文件：`agent/node/self_query_node.py`、`agent/lightingRL/prompt_registry.py`
- 已落地：`expansion_terms` 字段，LLM 对抽象 query 生成 3-5 个可观测替代词，拼到 `rewritten_query` 尾部
- 27-case 验证：`context_recall` +0.04（0.70→0.74）
- TODO：expansion 仅在 3-5/27 case 触发，可降低触发门槛或改为检索内部 expansion

### R8 交叉验证用 NonLLM/IDBased recall（诊断辅助）

- 文件：`agent/test/ragas_eval_runner.py:521-532`
- 改动：加跑 `IDBasedContextRecall`（dataset 加 `reference_context_ids = [video_id]` 或 `event_id`）
- 用途：本身不提升数字，但能确认 P1-Next-F 是否真的修对了"评测噪声"
- 工作量：低-中

---

## P1-Next-G R7 Hybrid alpha sweep（独立项，留到最后）

> 从 P1-Next-G 中拆出，作为最终微调项。

- 文件：`agent/node/retrieval_contracts.py:15-17` (`hybrid_alpha=0.7`, `hybrid_fallback_alpha=0.9`)
- 改动：跑 0.5 / 0.7 / 0.9 三档 + dense-only ablation 对比
- 预期：**+0.01~0.03 recall**（不确定，属于 fine-tuning 级别）
- 工作量：低

### 验收

- 同一 `--limit 50`（Part4）子集上 ablate 至少 3 档 alpha + dense-only
- 选最优 alpha 入默认配置
- context_recall / context_precision 不退步

---

## P1-Next-E entity_hint 字段语义修复（长期，独立路径）

> 触发：UCFCrime source data 的 `entity_hint = segment_<event_index>` 顺序编号，导致 chroma_builder 按 `(video_id, entity_hint)` 聚合时每组仅 1 event，三层架构退化为两层（详见 `data_audit_2026_05_02.md`）。

### 推荐方案 B: LLM-based entity clustering

- 不重跑视觉模型，基于现有 events 文字字段做 LLM 实体聚类
- 改 `agent/test/ucfcrime_transcript_importer.py` 在 events 生成时调 LLM
- 新增 `agent/test/entity_clustering.py`（约 +120 LoC）
- 重新生成 ucfcrime source data 310 文件
- 重建 ucfcrime chroma 库
- env flag: `AGENT_USE_LEGACY_ENTITY_HINT=1` 灰度回滚口；chroma 双 namespace 并行

### 备选方案 A: visual entity tracking（重做 source data，工作量大）

### 备选方案 C: heuristic alias normalization（最简，精度低）

### 工作量：方案 B 全套约 6-8 小时

### 验收

- ucfcrime 全数据集 events / (video, entity_hint) 平均 ≥ 2.0（当前 1.0）
- chroma child collection 数量 ≤ 0.6 × event collection 数量
- top_hit_rate / localization_score 不退步
- context_recall 预期 +0.05（child 含更多 events → recall 自然涨）

---

# ✅ 已完成（按时间倒序）

## P1-Next-C `custom_correctness` + 保留 `factual_correctness` 对照 ✅ DONE（2026-05-02）

- **规则型** `custom_correctness`（yes/no 对齐 + top-1 video + 时间 IoU/bonus；期望为 `no` 时跳过 video 权重）；`expected_time_is_approx` 时 GT 区间 ±5s 再算 IoU。
- **保留** RAGAS `factual_correctness`；`**ragas_e2e_score` 均值** 用 `custom_correctness` 替代原 factual 项。
- 报告字段：`generation_summary.custom_correctness_avg`；`challenge.md` §5.4。
- 未做：`--rescore-only`（仍列在可选增强）。

## P1-Next-F evaluator-only（R1+R2+R3）✅ DONE（2026-05-02）

- **R1** `ragas_eval_runner._row_context_text`：每条 context 前缀 `Video <id>. Time <start>s-<end>s.`，消除「参考里写 In video 但 chunk 无 video token」的 RAGAS 归因失败。
- **R2** `agent_test_importer._build_reference_scene_description`：场景描述从**题干**推导，`recall_challenge` 仅 metadata，**不**再污染 reference 文本（消 F1）。
- **R3** 默认 `--ragas-max-contexts` **5**、`--ragas-max-total-context-chars` **3000**（对齐 rerank top-K，消 F3）。
- **范围**：仅评测 / 数据集导入路径；**未改**并行检索、verifier、summary 生产代码。
- **50-case**（同子库、相对 P1-Next-F 前基线）：`context_recall_avg` 约 **+0.12**（如 0.36→**0.48**）、`context_precision_avg` 约 **+0.12**、`faithfulness_avg` 约 **+0.05**、`ragas_e2e_score_avg` 约 **+0.08**。
- 依据：`agent/recall_diagnosis_2026_05_02.md`。

## P1-7 v2.3 verifier 在 rerank_result 内重选 best span ✅ DONE（2026-05-02）

- 文件：`agent/node/match_verifier_node.py`、`agent/node/summary_node.py`、新文件 `agent/test/test_match_verifier_v23.py`（20 例）
- 设计：让 verifier 在 `rerank_result[:8]` 同视频候选里 LLM single-shot 挑 best span，输出 `span_source ∈ {"rerank_reselected", "candidate_top_row"}`，**不调 chroma 二次 fetch**
- LoC: 净 +200，单测 84/84 全过
- env flags: `AGENT_VERIFIER_RESELECT_SPAN`, `AGENT_VERIFIER_CANDIDATE_LIMIT`, `AGENT_VERIFIER_CROSS_VIDEO_TOP_N`, `AGENT_MATCH_VERIFIER_USE_LLM`
- 50-case 验证（grounder OFF）：14 case existence 中 2 case 真重选；指标在 RAGAS 噪声范围内（±0.04）
- 50-case 验证（grounder ON）：context_recall +0.033、context_precision +0.02、faithfulness +0.016；factual_correctness -0.04（受 follow-up bug 影响）
- 12 个原 No-matching 子集 factual avg：0.2083 → **0.2500**（+0.042 真实净贡献，对照组锁死无 RAGAS 噪声）

## P1-7 v2.3 follow-up：summary mismatch × rerank_reselected ✅ DONE（2026-05-02）

- **问题**：grounder ON 时 `decision=mismatch` 仍可能带 `span_source=rerank_reselected`；原逻辑优先用 verifier span 写 Yes，与 mismatch 冲突。
- **修复**：`_build_factual_summary` 在 `AGENT_ENABLE_EXISTENCE_GROUNDER=1` 且上述两条件时返回 `No matching clip is expected.`；`_canonicalize_summary` 对 LLM 输出的 Yes 行在同条件下改回该结论。grounder OFF 不变。
- 单测：`test_match_verifier_v23.DownstreamConsumptionTests`（grounder on/off）、`test_summary_node_bail_out.CanonicalizeSummaryTests.test_p1_7_llm_yes_demoted_when_mismatch_rerank`。

## P1-5 + P3-3 全手术清理 legacy_router ✅ DONE（2026-05-02）

- 删除 8 个文件（约 -123KB）：`tool_router_node` / `router_prompts` / `reflection_node` / `cot_engine` / `query_optimizer` / `error_classifier` + 2 个 .cover artifacts
- 删除 `SQLiteGateway` 类、`merged_result` state 字段、`graph_builder._build_legacy_router_graph`
- 9 篇文档同步更新
- 净 LoC: -4000 / +50
- commit hash: `d0dc7f1`
- 影响：完全废弃 `AGENT_EXECUTION_MODE=legacy_router` 模式（旧脚本设此 env 无效但向后兼容）

## P1-Next-D chunk 方案重审 ✅ DONE（2026-05-02，纯调研无代码）

- 完整调研报告：`agent/data_audit_2026_05_02.md`
- 关键发现：UCFCrime child = event = 1:1（4331/4331 records）；entity_hint 是顺序编号非真 entity track ID；retrieval top-K 56% case 全是同一视频
- 决策：方案 A（不动数据，承认现状）；entity_hint 重做迁至 P1-Next-E

## P1-Next-A 收紧 summary_node bail-out ✅ DONE（2026-05-02）

- 文件：`summary_node.py` 三道锁同步打掉、`graph_builder.py` 加 `AGENT_DISABLE_VERIFIER_NODE` flag、新文件 `test_summary_node_bail_out.py` 20 例
- 50-case 关键 KPI：`No matching clip is expected.` case 数 **12 → 0**；12 case 子集 factual avg 0.1667 → 0.2083（+25% rel，对照组锁死）
- env flag：`AGENT_SUMMARY_BAIL_OUT_STRICT=0/1`（默认 1=新行为）
- 详见 `agent/调试记录.md` §10

## P1-3 query embedding LRU + 磁盘缓存 ✅ DONE（2026-05-02）

- 文件：`agent/tools/llm.py` 重写 + 新增 `test_embedding_cache.py` 10 例
- 自实现 OrderedDict LRU + sha256 disk cache + 指数退避重试（3 次 / 0.5s 1s 2s）
- 单条 / 批量统一查询路径，批量 cache miss 合并成一次 batch API call
- env flags: `AGENT_EMBEDDING_CACHE_DIR`, `AGENT_EMBEDDING_CACHE_LRU_SIZE`, `AGENT_EMBEDDING_CACHE_DISABLED`
- 在线烟测：3 query × 3 round 验证 LRU/disk/remote 三层

## P1-1 SQLite FTS5 ✅ DONE

- 文件：`agent/db/schema.py` + `sqlite_builder.py` + `parallel_retrieval_fusion_node.py`
- 外部内容虚表 + AFTER INSERT/UPDATE/DELETE 三个触发器；tokenizer=`unicode61 remove_diacritics 1`
- env flag: `AGENT_SQL_USE_FTS5=0/1`（默认 1）
- 已知边界：`AGENT_USE_LLAMAINDEX_SQL=1` 时 SQL 分支走 LlamaIndex 不经过 FTS5（P2 后续）

## P1-2 去伪 BM25，让 hybrid 真正 hybrid ✅ DONE

- 新增 `agent/tools/bm25_index.py` 全量 BM25Okapi（k1=1.5, b=0.75）+ RRF 融合
- `ChromaGateway.search` 改为纯 vector，删除 subset BM25
- env flags: `AGENT_HYBRID_BM25_FUSED`, `AGENT_HYBRID_VECTOR_OVERSAMPLE`, `AGENT_HYBRID_BM25_OVERSAMPLE`

## P1-6 路由收敛：信号驱动 weighted_rrf ✅ DONE（2026-05-01）

- classifier 输出 `signals = {metadata_hits, relation_cues, multi_step_cues, existence_cues}`
- `weighted_rrf_fuse` 按证据数量对 `{sql, hybrid}` 权重做 soft-bias（±0.2 封顶）
- `parallel_retrieval_fusion_node` 把 signals 透传 + `fusion_meta.signals` 留痕
- 注：原 `AGENT_LEGACY_DISABLE_PURE_SQL_TERMINAL` 灰度口已随 P1-5/P3-3 删除

## P1-7 基础设施（grounder 雏形）✅ DONE（早期）

- classifier `answer_type` / `match_verifier_node` 接入图 / `final_answer_node` grounder 分支 / AgentState fields
- 后续优化已合并到 P1-7 v2.3

## P0-1 关闭默认 parent projection ✅ DONE

- `parent_projection_enabled()` 默认返回 False，`rerank_result` 直接是 child 行
- env flags: `AGENT_ENABLE_PARENT_PROJECTION=1`（回滚口）、`AGENT_DISABLE_PARENT_PROJECTION=1`（兼容旧脚本）

## P0-2 新增 event-level Chroma collection ✅ DONE

- 三层 collection（child / parent / event）+ namespace 化（`AGENT_CHROMA_NAMESPACE`）
- env flags: `AGENT_CHROMA_NAMESPACE`, `AGENT_CHROMA_RETRIEVAL_LEVEL`
- 注：UCFCrime 上 child=event=1:1（详见 P1-Next-D / P1-Next-E）

## P0-3 放松 structured_zero_guardrail ✅ DONE

- 三路软降级分支（`sql=0+hybrid>0` / `sql=0+hybrid=0` / `sql>0`）+ `degraded_reason` 标注

## P0-4 修 SQL 文本 token 抽取停用词 ✅ DONE

- `_SQL_TOKEN_STOPWORDS` 只保留功能词；`_PLURAL_TO_SINGULAR` 显式映射；上限 4 → 6
- 单测 `test_extract_text_tokens_for_sql.py` 10 例

---

# ❌ 取消（决策已固化）

## P1-4 ~~summary 输出分 strict / natural 两档~~ ❌ 取消（2026-05-02）

> 取消理由：被 P1-Next-A 取代（`AGENT_SUMMARY_BAIL_OUT_STRICT` env flag 已提供灰度回滚口）

## P1-Next-A.5 ~~fallback 加 scene description~~ ❌ 取消（2026-05-02）

> 取消理由：被 P1-Next-F R2 取代。R2 把 evaluator note 从 reference 剥离后，scene 不再是 RAGAS reference 期望的 fact，给 fallback 加 scene 反而会引入 hallucination 风险

## P1-Next-B ~~verifier 多片段输入~~ ❌ 已合并（2026-05-02）

> 合并理由：核心思想"verifier 看 multi-chunk 候选"已合并到 P1-7 v2.3

---

> P2 / P3 历史 todo 已于 2026-05-02 清理（用户决策：超出当前范围，不维护）。如需查阅，从 git history 找此次 commit 之前的 `agent/todo.md` 即可。

