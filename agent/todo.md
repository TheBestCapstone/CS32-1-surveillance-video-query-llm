# Agent 项目改进 Todo

> 改造原则：不动外层 LangGraph 主图结构，只在节点内部、数据层与融合层做增量改造。所有改造保持下游 `answer_node` / `summary_node` / `ragas_eval_runner.py` 兼容。
>
> 配套文档：
>
> - `agent/handoff.md` — 上 session 末尾接力快照
> - `agent/调试记录.md` — 全 session 完整复盘
> - `agent/data_audit_2026_05_02.md` — 父子索引架构调研
> - `agent/recall_diagnosis_2026_05_02.md` — context_recall 低值诊断 ⭐

---

## 当前已知瓶颈（截至 2026-05-02 P1-7 v2.3 实测后）


| 指标                                | 起点   | 当前        | 目标         | 真因                                                                         |
| --------------------------------- | ---- | --------- | ---------- | -------------------------------------------------------------------------- |
| `top_hit_rate`                    | 0.40 | **0.94**  | ≥ 0.95     | (P0/P1 已修)                                                                 |
| `context_precision_avg`           | 0.18 | 0.58      | ≥ 0.65     | reranker 把弱相关 chunk 排进 top-3                                               |
| `**context_recall_avg`**          | 0.15 | **0.36**  | **≥ 0.55** | **F1+F2+F3 评测/接口问题（详见 `recall_diagnosis_2026_05_02.md`），不是 retrieval 召不到** |
| `time_iou_avg`                    | 0.13 | 0.23      | ≥ 0.40     | rerank 排序错 + 长视频中段被错过                                                      |
| `factual_correctness_avg` (RAGAS) | 0.48 | 0.58-0.62 | (废)        | 用 P1-Next-C `custom_correctness` 替代                                        |


---

# 🚧 未完成（按优先级排序）

## ⭐ P1-Next-F evaluator-only 修复（**最高优先级**，单一 PR ≤ 1 天）

> 来源：`agent/recall_diagnosis_2026_05_02.md` R1+R2+R3。
> 三个改动**全部在 evaluator 端，不动产品代码**（retrieval / verifier / summary 一行不动），与 P1-7 v2.3 / P1-Next-A / P1-Next-C 完全正交。
> 预期 context_recall: 0.36 → **0.55-0.65**；同时把"评测信号 / 噪声比"拉起来，让后续任何 retrieval 改造的真实收益可观测。

### R1 给 RAGAS 看到的 context 强制带 video_id + 时段头

- 文件：`agent/test/ragas_eval_runner.py:120-127` (`_row_context_text`)
- 改动：返回 `f"Video {row['video_id']}. Time {row['start_time']:.1f}s-{row['end_time']:.1f}s. " + 现有 event_summary_en`
- 当前数据：56% (84/150) chunk 缺 `Video <id>` 前缀，导致参考里 `In <video> around <time>` 直接归因失败
- 预期收益：消灭 F2 失败模式，**+0.10~0.15 absolute recall**
- 工作量：< 30min

### R2 把 evaluator note 从 reference_answer_rich 剥离

- 文件：`agent/test/agent_test_importer.py:509-538` (`_build_reference_answer_rich`)
- 改动：clean ref `f"Yes. In {video_id} around {time}."`；`recall_challenge` 单独放 metadata，不拼进 reference
- 当前数据：35/50 case 的 reference 含评测备注（"Minimal" / "Must link X to Y" / "Bystander has no actions; easily overlooked..."）；含备注组 avg recall=0.333 vs clean 组 0.422
- ⚠️ `agent/challenge.md §5.1` "default-on rich reference" 的设计假设**事实错误**，rich 多出来的 scene 是 evaluator 备注污染。建议同时把 `--ragas-no-rich-reference` 改成默认或加 ablation
- 预期收益：消灭 F1 失败模式，**+0.05~0.10 absolute recall**
- 工作量：< 1h（含 dataset 重生成，不需要重跑 retrieval）

### R3 提升 RAGAS 看到的 chunk 数到 5

- 文件：`agent/test/ragas_eval_runner.py:822` (`--ragas-max-contexts` 3 → 5) + 同步把 `--ragas-max-total-context-chars` 1800 → 3000
- 当前数据：rerank top-K = 5，但 RAGAS 只看 3 个 chunk，多 fact 答案没机会被多 chunk 同时支撑
- 预期收益：消灭 F3 失败模式，**+0.03~0.05 absolute recall**
- 工作量：< 5min

### 验收

- 跑一次 50-case eval，对比 P1-Next-A baseline 的 context_recall：从 **0.36 → ≥ 0.55**
- top_hit_rate / context_precision / faithfulness 不退步（P1-Next-F 不改 retrieval 一行）
- factual_correctness 可能因 reference 干净而提升（次要预期）

---

## ⚠️ P1-7 v2.3 follow-up: summary_node mismatch bug（中优先，30min + 25min eval）

> 触发：P1-7 v2.3 grounder ON 50-case eval 暴露了 PART1_0021 退步（factual 0.5 → 0.0）。verifier 给出 mismatch + span_source=rerank_reselected + 跨视频选错（Arrest046 而非 expected Arrest043），但 `summary_node._build_factual_summary` 看到 `span_source=="rerank_reselected"` 就直接用 verifier 的 `(video_id, start, end)` 写出 "The most relevant clip is in Arrest046..."，**覆盖了 grounder 的 mismatch 语义**。

- 文件：`agent/node/summary_node.py:138-176` (`_build_factual_summary`)
- 改动思路：增加判断 ——
  ```python
  if (
      verifier_result.get("decision") == "mismatch"
      and verifier_result.get("span_source") == "rerank_reselected"
      and grounder_enabled
  ):
      return "No matching clip found."  # 不用 verifier 的 video_id/start/end
  ```
  保留 grounder OFF 行为不变（rows>0 强制 Yes）
- 验收：重跑 P1-7 v2.3 grounder ON 50-case，PART1_0021 不再 factual=0；其它 case 不退步
- 工作量：30min 代码 + 25min eval

---

## P1-Next-C 评测指标改造（实施时机：R1+R2+R3 之后）

> 触发：sanity check 发现 RAGAS factual_correctness 单次评测随机抖动 ±0.10-0.15。
> 实施时机：**先做 P1-Next-F 拉真信号 → 再做 P1-Next-C 替换 factual**（顺序换了不影响最终目标）。

### 保留的 RAGAS 指标

- `context_precision` / `context_recall` / `faithfulness`（不动）

### 移除指标

- ❌ `factual_correctness`（被自定义"准确性"指标完全替代）

### 新增 `custom_correctness`（规则型，0 LLM 调用）

```
yes_no_score    = 1.0 if predicted_answer_label == expected_answer_label else 0.0
video_id_score  = 1.0 if predicted_video_id == expected_video_id else 0.0
time_iou_score  = max(0, IoU((pred_start, pred_end), (exp_start, exp_end)))
time_bonus      = 0.2 if time_iou_score >= 0.5 else 0.0

# 默认权重（有 expected_time）
custom_correctness = 0.4 × yes_no + 0.4 × video_id + 0.2 × min(1.0, time_iou + time_bonus)

# expected_time 缺失时
custom_correctness = 0.5 × yes_no + 0.5 × video_id
```

### RAGAS LLM 评分参数变更

- `temperature=0`（runner 里 `LangchainLLMWrapper(ChatOpenAI(model="...", temperature=0))`）
- 仍保留 retry，但失败计入 `metric_errors`

### 实施前讨论清单

- `expected_answer_label="no"` 时 video_id_score 跳过（"no"问题没有正确视频），权重重分配到 yes_no 和 time
- `predicted_answer_label` 从 response 抽：正则 `"No matching" / "Yes." / "The most relevant clip"` 三类
- `expected_time` 模糊（如"约 0:01:00"）扩 ±5s tolerance
- 旧 baseline 数字反向计算：runner 加 `--rescore-only` 模式

### 改造范围

- 文件：`agent/test/ragas_eval_runner.py` 新建 `_score_custom_correctness()` + 替换 factual_correctness 注入点 + 设 `temperature=0`
- 新文件 `agent/test/test_custom_correctness.py`
- `agent/challenge.md` 加一节描述 custom_correctness 含义

### 工作量：1.5-2h

---

## P1-Next-G retrieval 真实改造（按 ROI 排序，先做 P1-Next-F 后启动）

> 这一组改动会动 retrieval 真实链路。需要 P1-Next-F 把评测噪声降下来后才能可靠 A/B。来源：`recall_diagnosis_2026_05_02.md` R4-R8。

### R4 reranker 升级 / metadata 净化

- 文件：`agent/tools/rerank.py:17, 20-33`
- 选项：
  - (a) `BAAI/bge-reranker-v2-m3` 替换 `cross-encoder/ms-marco-MiniLM-L-6-v2`（多语 + 对 metadata-rich 文本更好）
  - (b) `_build_pair_text` 把 metadata 段移到 query 侧
  - (c) 剥掉 doc 文本里 `Keywords:` 段
- 预期：救 F5（reranker 排错），**+0.02~0.05 recall + 显著 localization 改善**
- 工作量：(a) 1-2 天 / (b)(c) 半天

### R5 长视频按时间窗 hard split chunking

- 文件：`agent/db/chroma_builder.py:208-257, 356-438`
- 改动：新增按 30s 时间窗聚合多 events 的 child 策略（与现有 entity_hint 策略并存或替换）
- 预期：救 F4（长视频中段被错过），**+0.05 recall + localization 显著改善**
- 工作量：中-大（改 builder + 重建索引 + 验证）
- 与 P1-Next-E 的关系：互斥但都有效；**推荐先做 R5（简单可控），entity_hint 重做留作后续**

### R6 Query 改写 / expansion

- 文件：新增 `agent/node/query_rewriter_node.py` 或扩展 `self_query_node`
- 改动：LLM 把抽象 question（"neglect" / "bystander" / "excessive force"）改写为可观察 chunk 关键词
- 预期：救 F6（negative-behavior / 抽象描述），**+0.02~0.04 recall**
- 工作量：中（新节点 + prompt 调优）

### R7 Hybrid alpha sweep

- 文件：`agent/node/retrieval_contracts.py:15-17` (`hybrid_alpha=0.7`, `hybrid_fallback_alpha=0.9`)
- 改动：跑 0.5 / 0.7 / 0.9 三档 + dense-only ablation 对比
- 预期：**+0.01~0.03 recall**（不确定）
- 工作量：低

### R8 交叉验证用 NonLLM/IDBased recall（诊断辅助）

- 文件：`agent/test/ragas_eval_runner.py:521-532`
- 改动：加跑 `IDBasedContextRecall`（dataset 加 `reference_context_ids = [video_id]` 或 `event_id`）
- 用途：本身不提升数字，但能确认 P1-Next-F 是否真的修对了"评测噪声"
- 工作量：低-中

---

## P1-Next-E entity_hint 字段语义修复（长期，独立路径）

> 触发：UCFCrime source data 的 `entity_hint = segment_<event_index>` 顺序编号，导致 chroma_builder 按 `(video_id, entity_hint)` 聚合时每组仅 1 event，三层架构退化为两层（详见 `data_audit_2026_05_02.md`）。
> 与 P1-Next-G R5 关系：R5 改 child 切分维度为时间窗；本 todo 改 entity_hint 为真实 entity track ID。**两路径互斥**（同一时间只用一种 child 策略），R5 简单可控、本 todo 长期方向。

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

## P1-7 v2.3 verifier 在 rerank_result 内重选 best span ✅ 代码 DONE（2026-05-02）

⚠️ **有 follow-up bug 待修**（见上方"P1-7 v2.3 follow-up"）

- 文件：`agent/node/match_verifier_node.py`、`agent/node/summary_node.py`、新文件 `agent/test/test_match_verifier_v23.py`（20 例）
- 设计：让 verifier 在 `rerank_result[:8]` 同视频候选里 LLM single-shot 挑 best span，输出 `span_source ∈ {"rerank_reselected", "candidate_top_row"}`，**不调 chroma 二次 fetch**
- LoC: 净 +200，单测 84/84 全过
- env flags: `AGENT_VERIFIER_RESELECT_SPAN`, `AGENT_VERIFIER_CANDIDATE_LIMIT`, `AGENT_VERIFIER_CROSS_VIDEO_TOP_N`, `AGENT_MATCH_VERIFIER_USE_LLM`
- 50-case 验证（grounder OFF）：14 case existence 中 2 case 真重选；指标在 RAGAS 噪声范围内（±0.04）
- 50-case 验证（grounder ON）：context_recall +0.033、context_precision +0.02、faithfulness +0.016；factual_correctness -0.04（受 follow-up bug 影响）
- 12 个原 No-matching 子集 factual avg：0.2083 → **0.2500**（+0.042 真实净贡献，对照组锁死无 RAGAS 噪声）

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

