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

## 当前已知瓶颈（截至 2026-05-03，Tier 1+2 27-case）


| 指标                   | 15-case | 全量 155-case | Tier1+2 27-case | 目标     |
| -------------------- | ------- | ----------- | --------------- | ------ |
| `top_hit_rate`       | 0.867   | 0.207       | 0.852           | ≥ 0.50 |
| `context_precision`  | 0.697   | 0.537       | 0.509           | ≥ 0.70 |
| `context_recall`     | 0.700   | 0.674       | **0.667**       | ≥ 0.75 |
| `custom_correctness` | 0.763   | 0.456       | 0.685           | ≥ 0.70 |
| `ragas_e2e_score`    | 0.690   | 0.590       | **0.643**       | ≥ 0.70 |


> Tier 1（video collection）+ Tier 2（scene boost）已落地。27-case recall +0.056，e2e +0.019。
> 瓶颈根因：52 个 Normal_Videos 语义高度重叠。全量 155-case 尚未重跑 T1+T2。
> 优化计划见下方「全量检索瓶颈与优化计划」。

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

## 全量检索瓶颈与优化计划

> 触发：Part4 全量 155-case 上 `top_hit_rate=0.21`、`precision=0.54`（15-case 子集上 top_hit=0.87）。
> 根因：52 个 Normal_Videos 语义高度重叠，893 个 chunk 的向量空间严重拥挤。
> 审查结论：chunk 文本缺视频级区分度、向量搜索无结构化过滤、parent collection 闲置。
> 详见 `agent/全量测试分析.md`。

### 当前检索链路

```
query → self_query(rewrite+expansion) → classification(structured/semantic/mixed)
  → parallel:
      SQL(FTS5, limit=80)      ┐
      hybrid(Chroma cosine, oversample 3x=top15, +BM25 RRF) ┘
  → weighted RRF fusion → rerank(ms-marco, top-5) → answer
```


| #   | 瓶颈                                   | 代码位置                                      | 影响                        |
| --- | ------------------------------------ | ----------------------------------------- | ------------------------- |
| 1   | chunk 文本缺视频级区分度                      | `chroma_builder._build_child_document`    | 893 chunk 语义重叠，cosine 不可靠 |
| 2   | 向量搜索无 where 过滤，pass_filters 通常为空     | `hybrid_tools` line 133                   | 52 video 全在候选池            |
| 3   | parent collection（82 时间桶）闲置          | `parallel_retrieval_fusion_node` line 315 | 粗筛信息未利用                   |
| 4   | oversample 仅 3x（top-15 / 893 = 1.7%） | `db_access.ChromaGateway.search` line 119 | 大量相关 chunk 在候选外           |


### Tier 1（首选）：Video Collection + Chroma where 过滤 ✅ DONE

> 已落地：`video_discriminator.py`、`chroma_builder._build_video_records()`、`_coarse_video_filter()`。
> 27-case 验证：coarse filter 每 query ~200ms，latency +0.4s。全量 155-case 待验证。

**建 video collection**，每条 = LLM 生成的视频区分度 summary。检索时先查 video_collection → top-3 video_ids → child_collection 加 `where video_id IN [...]`。

```
chroma_builder 新增 _build_video_records():
  输入 per-video events → LLM →
  "Convenience store. Fish tank on right wall. Square white floor tiles.
   Blue trash bin near entrance. Counter area on left."

检索改造:
  Step 1: query → video_collection (embedding, 52 docs) → top-3 video_ids
  Step 2: query → child_collection (embedding, where video_id IN [v1,v2,v3]) → top-K
```

**优势**：候选池 893→~50 chunk，噪声 -94%。利用 Chroma 原生 `where`，不改 embedding。

- 改动：`chroma_builder.py` + `hybrid_tools.py` + `parallel_retrieval_fusion_node.py` + 新增 `agent/tools/video_discriminator.py`
- 代价：~4h | 预期：top_hit 0.21→0.50+，precision 0.54→0.70+

### Tier 2：结构化场景过滤（soft structured filter）✅ DONE

> 已落地：`scene_attrs.py`（SQL 提取 + IDF）、`self_query_node` scene_constraints、`_apply_scene_boost()`。
> 27-case 验证：recall +0.056，e2e +0.019。零 LLM 成本。

**核心思路**：用预定义属性词表把"场景"显式编码，查询时做 soft boost（非 hard filter）。

**设计决策（已锁定）**：


| 决策              | 选择                                    | 理由                     |
| --------------- | ------------------------------------- | ---------------------- |
| Schema          | `**has_X` boolean**，自动从 SQL 字段生成      | 零 LLM，与数据完全对齐          |
| 过滤方式            | **Boost（非 Filter）**                   | 泛 query 不被误伤           |
| Distinctiveness | **Corpus IDF**（SQL 直算）LLM 定方向、IDF 定力度 | 高频属性不淹没稀有属性            |
| 词表来源            | `**SELECT DISTINCT` 每次重新生成**          | 永不漂移，新视频自动扩展           |
| self_query      | **LLM 从词表选择**（复用现有调用）                 | 语义推断 "sedan"→has_car   |
| Boost 位置        | **RRF 融合后、reranker 前**                | 候选池更干净，reranker 输入质量更高 |


#### Scoring 方程

```
final_score = vector_score + λ · Σ(query_weight_i · idf_i)
```

- `λ = 0.1`（保守先验，后续扫参对比 λ=0 vs λ=0.1）
- `idf_i = log(N / df_i) / log(N)`，归一到 [0,1]。λ=0.1 下 max boost ≤0.09，不会主导向量排序
- `query_weight_i`：LLM 输出（0.7-0.95）
- Boost 时机：RRF 融合后的 candidate pool 上 apply，然后送 reranker
- `attr_score < threshold` → 退回纯向量（threshold=0，即始终 apply）

#### 词表（零 LLM，从 SQL schema 自动生成）

词表**不手写、不用 LLM**，直接从 `episodic_events` 表的已有字段自动提取：

```sql
SELECT DISTINCT object_type, scene_zone_en, object_color_en
FROM episodic_events
GROUP BY video_id
```

当前 Part4 实际数据：

```
object_type:   car (38/52视频)  person (34)  child (1)  unknown (24)
scene_zone:    road (23)        store (8)    room (14)  bedside (1)  unknown (42)
object_color:  black (33)  white (26)  red (19)  blue (19)  silver (5)  gray (7)  green (8)  yellow (6)  purple (4)  pink (3)
motion_level:  空
event_type:    空
```

自动映射规则：

```python
SQL_TO_VOCAB = {
    "object_type":  {"car": "has_car", "person": "has_person", "child": "has_child"},
    "scene_zone_en": {"road": "has_road", "store": "has_store", "room": "has_room", "bedside": "has_bedside"},
    "object_color_en": {c: f"has_{c}" for c in colors},  # has_black, has_white, ...
}
# unknown → 不生成属性（无信号）
```

**优势**：

- 零 LLM 调用、零 hallucination
- 新增视频/视频类型时词表**自动扩展**（跑一次 SQL 即可）
- IDF 直接 SQL 算：`df = COUNT(DISTINCT video_id WHERE object_type='car')`
- 与现有 `sqlite_builder._init_profile`（已聚拢 per-video object_types/colors/keywords）完全对齐

#### 入库阶段（全自动）

1. sqlite_builder 建库后 → 跑 `SELECT DISTINCT object_type/scene_zone/color GROUP BY video_id`
2. 自动生成 `video_scene_attrs(video_id, attr_name, idf)` 表
3. IDF = `log(N / COUNT(DISTINCT video_id WHERE attr=true)) / log(N)`
4. 全量重跑时自动更新，无需手工维护

#### 查询阶段

1. **self_query_node**（复用现有 LLM 调用）新增 `scene_constraints` 输出：
  - prompt 列出当前词表（Phase 1 step 5 生成的 JSON），LLM 只做选择不生成新属性
  - 输出 `[{attr_name, weight}]`，weight 由 LLM 估计（0.7-0.95）
  - 例："a black car drove to the refueling spot" → `[{has_car: 0.95}, {has_black: 0.9}]`
  - "refueling spot" 不在词表中 → LLM 不输出（受限于词表）
2. **Boost 应用**：RRF 融合后、reranker 前，对 candidate pool 每行按 `video_scene_attrs` 查匹配，apply boost 后送 reranker
3. 无匹配 → fallback 纯向量（`attr_score=0`）
4. Dump `attr_score`、命中 attrs、各 attr IDF 到 debug 日志

#### 实施（~3.5h）


| 步骤                                         | 时间    |
| ------------------------------------------ | ----- |
| `video_scene_attrs` 表 + SQL 提取 + IDF       | 0.5h  |
| 词表 JSON 导出（`--prepare-subset-db` 时自动）      | 0.25h |
| self_query 加 scene_constraints（LLM 从词表选）   | 1h    |
| retrieval boost 集成（RRF 后 reranker 前，λ=0.1） | 1h    |
| debug 日志 + λ=0 vs λ=0.1 ablation           | 0.75h |


> 每次 `--prepare-subset-db` 自动重新生成词表。不持久化、不手工维护。

**预期**：在 Tier1 基础上，有场景线索的 query precision +0.10~0.15。

### Tier 3：Oversample 扩大 + Parent 粗筛

oversample 3x→10x（top-50）；用 parent collection（82 时间桶）做粗筛。代价：~2h

### Tier 4：Chunk 去重合并

相邻时间段 chunk 去重。代价：~1h

### Tier 5：Hybrid Alpha 动态调优

代价：~0.5h，微调项

### 执行优先级

```
Tier 1 ✅ → Tier 2 ✅ → 跑全量 155-case 验证 → Tier 3（oversample + parent coarse）→ Tier 4/5 微调
```

Tier 1+2 预期 top_hit 0.21→0.55-0.75。

### 评测与 Ablation 规范

每次 Tier 上线后产出：


| Metric                                                                                             | baseline | current | Δ   | vector_only (λ=0) |
| -------------------------------------------------------------------------------------------------- | -------- | ------- | --- | ----------------- |
| top_hit_rate / precision_avg / recall_avg / e2e_score_avg / custom_correctness / video_match / IoU |          |         |     |                   |


按 query 类型分桶（presence / temporal / object-search / negative）。Tier 2 额外加 `attr_coverage` 和 `avg_attr_score`。

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

### R9 Weighted RRF 消融：**去掉 RRF 再跑一遍评测** 🚧 待做

> **动机**：RRF 不是唯一融合方式；在「向量侧跨视频假阳性多、一路列表很长」时，RRF 仍可能把噪声稳定送进候选池，伤害 **context precision**（见架构讨论）。需用同一批 case **实证** baseline（weighted RRF）vs 无 RRF 变体。

**实施（建议顺序）**

1. **融合模式开关**（`parallel_retrieval_fusion_node` + env）：例如 `AGENT_FUSION_MODE=weighted_rrf`（默认，现状）| `hybrid_only` | `sql_only` | `concat_dedupe`（两路结果去重按序截断至 `fused_limit`，**不经过 RRF**；具体语义实现时写死一版对照）。
2. **下游不变**：Tier2 Scene Boost、Cross-Encoder Rerank、final answer 链路不变，只替换「进入 boost 前的 fused 列表」如何生成。
3. **退化路径**：仅一路失败时行为与今天一致（fallback 单路），避免消融与稳定性混淆。

**评测**

- 与当前 **同一评测集**（如 Part4 `run_chunks` 已跑 chunk、或固定 `--case-ids-file` / `--limit` 子集），每档 fusion 各跑一遍。
- **必看**：`context_precision_avg`、`top_hit_rate`、`context_recall_avg`、`ragas_e2e_score_avg`；可选按 `difficulty_level` 分层（见 `pooled_*_difficulty_strata.json` 做法）。
- **产出**：表格 baseline vs 各变体 + 简短结论写入 `调试记录.md` / `handoff.md`。

**工作量**：约 **0.5–1d**（含实现开关与至少 **2 档** 消融跑完）。

### R10 RRF ID 一致性修复：两路 `event_id` 体系不匹配 + 粒度不一致 🚧 待做

> 触发：code review 发现 `weighted_rrf_fuse()` 和 `reciprocal_rank_fuse()` 中两条检索链路的 `event_id` 根本不是同一套 ID 体系，导致 RRF 核心「奖励双路命中」机制完全失效。
> 详见 `agent/agents/shared/fusion_engine.py`、`agent/tools/bm25_index.py`、`agent/tools/db_access.py:138-147`。

#### 根因拆解

| # | 问题 | 代码位置 | 影响 |
|---|------|----------|------|
| 1 | SQL `event_id` = 整数自增主键（如 `42`）；Chroma `event_id` = 字符串 `{video_id}_{entity_hint}`（如 `"video001_car_3"`） | `db_access.py:144`、`fusion_engine.py:84-96` | `_row_key()` 永远不匹配，overlap_count 恒为 0 |
| 2 | SQL 是 **event 级**（单条事件），Chroma 默认 child collection 是 **track 级**（多事件聚合） | `chroma_builder.py:225-274` | 粒度不对齐，即使用 `(video_id, track_id)` 做 key，SQL 端是 N:1 关系 |
| 3 | 内层 `reciprocal_rank_fuse()` 中 vector (Chroma 字符串 ID) + BM25 (SQLite 整数 ID) 同样无法去重 | `bm25_index.py:345-392` | BM25 项能匹配 SQL 分支、Chroma 项不能，非对称行为 |
| 4 | `ChromaGateway.search()` 将 Chroma doc ID 赋给字段名 `event_id`，命名误导 | `db_access.py:144` | 让后续代码误以为这是 SQL `event_id` |
| 5 | SQLite 有 `vector_ref_id` 列（与 Chroma event-level ID 格式一致），但 SQL SELECT 未包含此列，`_row_key()` 也未使用 | `schema.py:50`、`parallel_retrieval_fusion_node.py:128-133` | 已存在的 bridge 闲置 |

#### 实际后果

- `_source_type` 永远不会是 `"fused"`，只能是 `"sql"` / `"hybrid"` / `"bm25"` 等单源标签
- 加权 RRF 退化为**加权秩排序合并**：每个文档只拿单路 `w * 1/(k+rank)` 分，没有双路命中加分
- 如果同一条内容两路都排第 1，本该拿 `wsql/(k+1) + whybrid/(k+1)`，实际只拿了 `max(wsql/(k+1), whybrid/(k+1))`——少了一半融合分

#### 修复方案（3 选 1）

**方案 A：`_row_key()` 多字段 fallback（最小改动，~0.5h）**
- 当 `event_id` 是含下划线的 Chroma 字符串时，fallback 到 `(video_id, track_id/entity_hint)` 做 key
- **局限**：不解决粒度问题（track 级 vs event 级）

**方案 B：切换到 event-level Chroma collection（推荐，~2-4h）**
- 设 `AGENT_CHROMA_RETRIEVAL_LEVEL=event`
- Chroma event ID 格式 `{video_id}:{entity_hint}:{start_time}:{end_time}` 与 `vector_ref_id` 一致
- 在 `_run_sql_branch` 的 SELECT 中加上 `vector_ref_id` 列
- 在 `_row_key()` 中用 `vector_ref_id` 或 `(video_id, track_id, start_time, end_time)` 做 key
- **需要**：确认 event collection 有数据；可能需要改造 `ChromaGateway.search()` 让 metadata 包含 `event_id`

**方案 C：接受现状，重命名为 weighted merge（~0.25h）**
- 不改逻辑，只改文档/变量名，明确这是加权合并而非 RRF 融合

#### 验收

- 构造至少 1 个「同一 doc 在两路都被召回」的 case，确认 `overlap_count > 0` 且 `_source_type == "fused"`


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

