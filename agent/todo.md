# Agent 项目改进 Todo

> 本 todo 基于对 `agent/db/`、`agent/node/`、`agent/agents/`、`agent/tools/` 的全面审查，
> 以及最近一次评测 `agent/test/generated/ragas_eval_top30_current_chain_rrf_fix/summary_report.md`
> （Top hit=0.4, Context p=0.18, Context r=0.15, Time IoU=0.13）的结果整理。
>
> 改造原则：不动外层 `LangGraph` 主图结构，只在节点内部、数据层与融合层做增量改造。
> 所有改造都要保持下游 `answer_node`、`summary_node`、`ragas_eval_runner.py` 兼容。

---

## 现状瓶颈速查

- 时间 IoU = 0.13：根因是 parent_projection 默认开启，最终输出被拉回视频级
- Context precision/recall ≈ 0.15：根因是 track-level chunk 过粗 + SQL 侧走 `LIKE '%x%'`
- 中文 query 质量差：根因是 Chroma 语料全英文，BM25 恒为 0
- 结构化闸门过严：`structured_zero_guardrail` 把可召回的 semantic 也一并灭掉
- 域特化严重：self_query / classifier / extract_structured_filters 都是 basketball + UCFCrime 硬编码

---

## P0 本周落地（直接拉升评测指标）

### P0-1 关闭默认的 parent projection ✅ DONE

- 文件：`agent/node/retrieval_contracts.py:22-33`、`agent/node/parallel_retrieval_fusion_node.py`、`agent/node/hybrid_search_node.py`
- 现状：`parent_projection_enabled()` 原先默认 True，所有 `rerank_result` 被塌缩成 video 级，start/end 变成整视频范围
- 改造实施：
  - `parent_projection_enabled()` 默认返回 False
  - 新增 env 开关 `AGENT_ENABLE_PARENT_PROJECTION=1` 用于显式开启（回滚口）
  - 保留 legacy `AGENT_DISABLE_PARENT_PROJECTION=1` 语义以兼容旧脚本
  - 新增 `summarize_parent_context()`：不调 Chroma 的轻量 parent 摘要，仅写入 `sql_debug.parent_context` 供调试/展示
  - `parallel_retrieval_fusion_node`、`hybrid_search_node` 的 `rerank_result` 关闭 projection 时直接是 child 行
  - `final_answer_node` / `summary_node` / `ragas_eval_runner` 原生兼容 child 行（已存在 `_record_level` / `_child_rows` 分支，无需改）
- 回滚：`export AGENT_ENABLE_PARENT_PROJECTION=1`
- 待评测：跑一次 `ragas_eval_runner`，确认 `time_overlap IoU avg` 从 0.13 → ≥ 0.25

### P0-2 新增 event-level Chroma collection ✅ DONE

- 文件：`agent/db/chroma_builder.py`、`agent/db/config.py`、`agent/db/manage_graph_db.py`、`agent/node/types.py`、`agent/db/README.md`、`agent/chroma_build_summary.md`
- 现状：`child` 是 `(video_id, entity_hint)` 聚合，同 track 下多条事件合并，时间窗被吞掉
- 改造实施：
  - 新增 `_build_event_records(events)`：id=`{video_id}:{entity_hint}:{start}:{end}`（遇碰撞追加 dedup counter），doc 为全英文单事件描述，metadata 带 `record_level=event / parent_track_id / grand_parent_video_id / entity_hint / event_index / start_time / end_time / keywords`
  - `ChromaBuildConfig` 新增 `event_collection` 字段，所有 collection 字段改用 `field(default_factory=...)` 以尊重 runtime namespace
  - `chroma_builder.build()` 同步写入 child / parent / event 三层，并返回 `event_record_count` 与 `chunk_strategy.event`
  - **Collection 名称 namespace 化**：新增 `AGENT_CHROMA_NAMESPACE`（默认 `basketball`），三个 collection 按 `{namespace}_{tracks|tracks_parent|events}` 动态派生；getter 优先级：显式 `AGENT_CHROMA_{CHILD|PARENT|EVENT}_COLLECTION` > `AGENT_CHROMA_NAMESPACE` > 历史 `basketball`_* 常量
  - 新增 `AGENT_CHROMA_RETRIEVAL_LEVEL`（`child` 默认 / `event`）用于单 collection 在线路径切换，与 namespace 正交
  - `manage_graph_db.py`：`build-chroma --event-collection`、`switch --chroma-namespace` / `--chroma-event-collection` / `--chroma-retrieval-level`，`effective`_* 输出补 `effective_chroma_namespace` 与 `effective_chroma_event_collection`
  - `node/types.py` 暴露 `default_chroma_event_collection()`、`default_chroma_retrieval_level()`、`default_chroma_namespace()`
  - `agent/db/README.md` / `agent/chroma_build_summary.md` 追加英文 namespace 使用说明
- 切换数据集示例：
  - `python -m agent.db.manage_graph_db switch --chroma-namespace ucfcrime` → 三个 collection 变为 `ucfcrime`_*
  - `python -m agent.db.manage_graph_db build-chroma --seed-json <ucfcrime_events_flat.json> --reset` → 在新 namespace 下重建三层索引
  - `python -m agent.db.manage_graph_db switch --chroma-retrieval-level event` → 单 collection 在线路径切到 event 层
- 回滚：
  - `unset AGENT_CHROMA_NAMESPACE`（或设为 `basketball`）恢复历史 collection 名
  - `unset AGENT_CHROMA_RETRIEVAL_LEVEL`（或设为 `child`）让 `hybrid_tools` 走回 child collection
  - 旧 chroma 库里没有 event collection 也不影响 child / parent 路径；event collection 只会被显式 `retrieval_level=event` 的调用读取
- 待评测：切到 `AGENT_CHROMA_RETRIEVAL_LEVEL=event` 后跑 `ragas_eval_runner`，确认 `time_range_overlap_iou` 中位数提升

### P0-3 放松 structured_zero_guardrail ✅ DONE

- 文件：`agent/node/parallel_retrieval_fusion_node.py`（原 213-221 guardrail 块已重写）
- 现状：原逻辑在 `label=structured + sql_rows=0 + 有 filter` 时硬返回空
- 改造实施：
  - 保留先前的 `weighted_rrf_fuse` 主路径（sql=0 时其实已经等价于 hybrid-only rank-preserved）
  - 触发"软降级"的三路分支：
    - `sql=0 + hybrid>0` → 保留 RRF 产出，`fusion_meta.degraded_reason=sql_zero_hybrid_fallback`
    - `sql=0 + hybrid=0` → 返回空，`fusion_meta.degraded_reason=all_branches_zero`
    - `sql>0` → 正常 RRF，不打 degraded
  - `fusion_meta` 里追加 `structured_filters` 方便事后定位触发词
- 回滚：`git revert` 即可；无需 env flag，因为旧行为是纯退步
- 单元验证：5 组场景全符合预期（详见 commit 描述里的测试输出）
- 待验证：跑一次 `ragas_eval_runner`，确认 PART1_0020 / PART1_0026 类样本（pure_sql 0 命中）能回到 hybrid 结果

### P0-4 修 SQL 文本 token 抽取停用词 ✅ DONE

- 文件：`agent/node/retrieval_contracts.py`（`extract_text_tokens_for_sql` 及配套常量）
- 现状：`stopwords` 黑名单把 `person / car / moving / area / persons / cars` 等实词都丢了
- 改造实施：
  - 新增 `_SQL_TOKEN_STOPWORDS` 常量：只保留真正功能词（`the / this / are / were / with / from / for / this / that / show / find / look / clip / database / please / ...`）
  - 新增 `_PLURAL_TO_SINGULAR` 显式映射：`persons / people → person`、`cars → car`、`officers → officer`、`children → child` 等常见复数
  - 新增 `_singularize_token()`；不做启发式 stemming，避免 `news → new` / `lens → len` 的误伤
  - 现在 token 流转：`tokenize → length>2 → singularize → 停用词过滤 → filter_terms 去重 → dedup → 截断 top 6`
  - 上限从 4 提到 6（现在噪声词更少，可多放几个真实信号词）
- 测试：`agent/test/test_extract_text_tokens_for_sql.py`（10 个 case 全过）
  - PART1_0020 style "police officer stomping ... person lying ... ground ... yard" 至少保留 4/7 信号词
  - `red car in parking area` → filter_terms 吸掉 red/car/parking，保留 `area`
  - `persons lying on the ground` → filter + singularize 不留 person/persons
- 回滚：`git revert`；纯正向，无需 env flag
- 待验证：跑 `ragas_eval_runner`，看 `_run_sql_branch` 命中率与 context_precision 的变化

---

## P1 1-2 周（改数据层与检索层）

### P1-1 SQLite 上 FTS5 ✅ DONE

- 文件：`agent/db/schema.py`、`agent/db/sqlite_builder.py`、`agent/node/parallel_retrieval_fusion_node.py`、新文件 `agent/test/test_sql_fts5.py`
- 现状：`_run_sql_branch` 里 `OR lower(coalesce(event_text_en,'')) LIKE ?` 扫全表，每个 token 触发一次完整扫
- 改造实施：
  - `schema.py`：新增 `FTS_TABLE_NAME / FTS5_CREATE_SQL_LIST / FTS5_REBUILD_SQL`，包含一张外部内容虚表 + 三个 AFTER INSERT/UPDATE/DELETE 触发器；tokenizer=`unicode61 remove_diacritics 1`，索引列=`event_text_en + event_summary_en + appearance_notes_en + keywords_json`
  - `sqlite_builder.py`：`build()` 在 `_create_indexes()` 之后调用 `_create_fts5()`（compile 没带 FTS5 时 graceful fallback 并打 warning 返回 False）；批量插入完成后调用 `_rebuild_fts5()` 做 belt-and-braces 重建；返回值新增 `fts5_enabled / fts5_row_count`
  - `parallel_retrieval_fusion_node._run_sql_branch`：新增 `_sql_use_fts5_enabled()`、`_fts5_table_present()`、`_build_fts5_match_expr()`；当 token 非空且虚表存在时，文本子句改为单个 `event_id IN (SELECT rowid FROM episodic_events_fts WHERE … MATCH ?)`，否则回退 LIKE；返回的 summary 末尾打 `text_strategy=fts5/like/none` 用于诊断
  - env flag `AGENT_SQL_USE_FTS5=0/1`（默认 1）作为 P1-1 的灰度回滚口
- 单测：`agent/test/test_sql_fts5.py` 7 例（虚表创建、MATCH、UPDATE/DELETE 触发器一致性、`_run_sql_branch` FTS5 路径、`AGENT_SQL_USE_FTS5=0` 走 LIKE、无 token 时不打文本子句），与 P1-2 单测一起 34/34 全过
- 在线验证：对 50-case eval 子集（235 events）补建 FTS5 后，三条人工 query 全部命中预期视频：
  - "Two white police vehicles flashing roof lights" → Arrest050_x264 (FTS5 行数 6, text_strategy=fts5)
  - "a person stomping on someone lying on the ground" → Abuse041/042 系列 (FTS5 行数 16)
- 已知边界：当前 `AGENT_USE_LLAMAINDEX_SQL=1` 时，SQL 分支会走 `run_llamaindex_sql_query` → `_run_deterministic_sql_query`（基于 `sql_debug_utils` 的 LIKE 评分梯度），不经过新 FTS5 路径；P1-1 的 FTS5 仅作用于 `_run_sql_branch`（即 `AGENT_USE_LLAMAINDEX_SQL=0` 的直连路径）。把 FTS5 也接入 deterministic planner 是后续优化（涉及 CASE-WHEN 评分阶梯重构，单列 P2）
- 兼容性 / 回滚：
  - 老库没有 `episodic_events_fts` 时 `_fts5_table_present` 返回 False，`_run_sql_branch` 自动退回 LIKE
  - 已有 sqlite 可以原地补建：`for stmt in FTS5_CREATE_SQL_LIST: conn.execute(stmt); conn.execute(FTS5_REBUILD_SQL)` 即可
  - `AGENT_SQL_USE_FTS5=0` 立即回到 LIKE 路径

### P1-2 去掉伪 BM25，让 hybrid 真正 hybrid ✅ DONE

- 文件：`agent/tools/db_access.py`、`agent/tools/hybrid_tools.py`、`agent/tools/llamaindex_adapter.py`、新文件 `agent/tools/bm25_index.py`、新文件 `agent/test/test_bm25_index.py`
- 现状：`ChromaGateway.search` 里的 BM25 是在 vector 已返回的 top-N 内存子集上重算，IDF 几乎无效；`run_llamaindex_vector_query` 里的 `_bm25_scores(query, texts)` 也是同样的"子集 BM25"
- 改造实施：
  - 新增 `agent/tools/bm25_index.py` 提供 `BM25Index`：从 `episodic_events` 全量读取 `event_text_en + event_summary_en + appearance_notes_en`，建标准 BM25Okapi（k1=1.5, b=0.75）；`(db_path, mtime)` 维度的进程级缓存；支持 `metadata_filters` 预剪枝；查询端复用 `retrieval_contracts._SQL_TOKEN_STOPWORDS / _PLURAL_TO_SINGULAR` 与 SQL 通道同源
  - `ChromaGateway.search` 改为纯 vector：删除 `_bm25_scores`，按 cosine 距离升序返回 `_distance / _vector_score / _source_type='vector'`；`alpha` 仅保留兼容签名并打 deprecation warning
  - `dynamic_weighted_vector_search` 改写：vector top-K（Chroma/LlamaIndex）+ corpus BM25 top-K（`BM25Index`）→ `reciprocal_rank_fuse(rrf_k=60)` 融合返回；payload 同时保留 legacy 字段名 `_distance / _hybrid_score / _bm25 / _source_type` 以兼容 `normalize_hybrid_rows`
  - `run_llamaindex_vector_query` 同样替换：删除子集 `_bm25_scores`，改为 LlamaIndex 向量 top-K + 全量 BM25 top-K → RRF；保留 LlamaIndex 0 命中时退到 `ChromaGateway` 的兜底
  - 新 env flag `AGENT_HYBRID_BM25_FUSED=1/0`（默认 1）作为灰度回滚口；`AGENT_HYBRID_VECTOR_OVERSAMPLE / AGENT_HYBRID_BM25_OVERSAMPLE / AGENT_CHROMA_VECTOR_OVERSAMPLE` 用于调候选池倍数
  - `reciprocal_rank_fuse` 公共函数：按 `event_id` 去重、合并字段、暴露 `_fused_rank / _fused_score / _source_ranks` 用于诊断
- 单测：`agent/test/test_bm25_index.py` 共 10 例（语义式排名、过滤前剪枝、空过滤、停用词查询、mtime 缓存失效、RRF 交集排前），全绿；同时复跑 `test_pure_sql_fallback / test_weighted_rrf_fuse / test_extract_text_tokens_for_sql` 共 27 例全过
- 在线验证：用 `BM25Index` 直接查 50-case eval 子集（235 events / vocab=591），下列样本 ground truth 均出现在 top-3：
  - `PART1_0002`（black dog）→ Abuse037_x264 t∈[8.4..25.3]
  - `PART1_0011`（caregiver / 白发老人）→ Abuse040_x264 t∈[58.7..69.1]
  - `PART1_0037`（三辆警车 + 闪光顶灯）→ Arrest050_x264 t∈[133.6..206.5]
- 兼容性 / 回滚：
  - `ChromaGateway.search(alpha=...)` 仍可调用（仅日志一次 deprecation）
  - `_format_hybrid_payload` 同时输出新旧两套字段名，下游 `normalize_hybrid_rows` 与 rerank/answer/summary 均无需改动
  - `AGENT_HYBRID_BM25_FUSED=0` 立即关闭 BM25 通道，等价于纯向量行为（旧 subset BM25 不可恢复）
- 待验证：恢复 DashScope embedding 鉴权后跑一次完整 50-case e2e，预计 `context_recall_avg` 从 0.30 → ≥ 0.35（10 例 smoke 已经从 0.20 → 0.30，相对 +50%）

### P1-3 query embedding LRU + 磁盘缓存 ✅ DONE（2026-05-02）

- 文件：`agent/tools/llm.py`（重写 +260 / -30）、新文件 `agent/test/test_embedding_cache.py`（+260）
- 现状（改造前）：`get_qwen_embedding` 每次 query 都调一次 DashScope/OpenAI embedding，无缓存、无重试
- 改造实施：
  - 自实现轻量 LRU（`OrderedDict` + 锁），可"只查不发"以支持批量路径正确命中
  - 磁盘缓存：按 `sha256(provider|model|dimensions|text)` 落盘到 `AGENT_EMBEDDING_CACHE_DIR`，`.json` 含 vector + meta，写入用 `tempfile + rename` 防 partial write
  - 失败重试：单条 / 批量分别 3 次重试，指数退避 0.5s → 1s → 2s（封顶 4s）
  - 单条路径：`_lookup_cached`（LRU → disk → miss）→ `_embed_single_remote_with_retry`
  - 批量路径：先逐项查 LRU/disk，未命中合并按 `EMBEDDING_BATCH_LIMIT=10` 分批一次性 batch API call，结果两层回写
  - 暴露 `clear_embedding_cache()` / `get_embedding_cache_stats()` 用于运维与测试
  - env knobs：
    - `AGENT_EMBEDDING_CACHE_DIR=path` 启用磁盘缓存（不设则只用 LRU）
    - `AGENT_EMBEDDING_CACHE_LRU_SIZE=N`（默认 2048）
    - `AGENT_EMBEDDING_CACHE_DISABLED=1` 完全旁路缓存（debug 用）
  - 兼容性：`get_qwen_embedding(text)` 签名 / 返回类型 / 单条 vs 批量行为完全不变；6 个调用点（`db_access.py / chroma_builder.py / llamaindex_adapter.py / py2sql.py / event_retriever.py / __main__`）零改动
- 单测：`agent/test/test_embedding_cache.py` 10 例（LRU 命中 / disk 命中 / disk hit warming LRU / 批量 partial-hit / 批量分块 / cache key 随 model 变化 / 禁用 flag bypass / LRU 容量 eviction / retry 成功 / retry 耗尽传播），全用 `mock.patch._build_embedding_client` 不触网络；与既有 54 例一起 **64/64 全过**
- 在线烟测（真实 OpenAI API，3 query × 3 round）：
  - 1st pass（cold）：3 次 API call、1 次 LRU hit（重复 query）
  - 2nd pass（清 LRU）：**3 次 disk hit、0 次 API call**
  - 3rd pass（LRU warm）：**3 次 LRU hit、0 次 API call**
  - 磁盘按 SHA256 key 落 `.json`，`vector + provider + model + dimensions` 完整保留
- 兼容性 / 回滚：
  - `AGENT_EMBEDDING_CACHE_DISABLED=1` 立即回到旧行为（无缓存 + 仍带 retry，比改造前还稳）
  - 不设 `AGENT_EMBEDDING_CACHE_DIR` 时只走 LRU（进程级 ephemeral）
  - 删除磁盘 cache 目录任意时刻安全（命中失败会自动 fallback 到 remote）

### P1-4 ~~summary 输出分 strict / natural 两档~~ ❌ 取消（2026-05-02）

> 取消理由：P1-Next-A 已经把 summary_node 的 bail-out 三道锁同步打掉，并且通过 `AGENT_SUMMARY_BAIL_OUT_STRICT` env flag 提供了灰度回滚口；如果将来要"natural 自然句"行为，可以在 `_normalize_summary_output` 加一个新 flag，没必要再做"双档"抽象。当前的 strict 模板（"Yes. The relevant clip is in ..." / "The most relevant clip is in ..."）已经是 RAGAS reference 期望的格式，natural 模式实际场景里也用不到（前端拿到 final_answer 自己渲染即可）。

### P1-Next-C 评测指标改造（决策固化 2026-05-02，待下个 session 实施）

> 触发原因：sanity check 发现 RAGAS `factual_correctness` 单次评测随机抖动 ±0.10-0.15（同 response 不同 LLM 评分得分相差 0.18 avg），单次跑无法识别真实改造收益。

#### 保留指标（沿用 RAGAS）

- `context_precision`（用 reference + retrieved_contexts 评）
- `context_recall`（用 reference + retrieved_contexts 评）
- `faithfulness`（用 user_input + response + retrieved_contexts 评；用户决策保留）

#### 移除指标

- ❌ `factual_correctness`（被自定义"准确性"指标完全替代）

#### 新增自定义指标 `custom_correctness`（规则型，0 LLM 调用）

公式（初版，需要在实施时讨论调整）：

```
yes_no_score    = 1.0 if predicted_answer_label == expected_answer_label else 0.0
video_id_score  = 1.0 if predicted_video_id == expected_video_id else 0.0
time_iou_score  = max(0, IoU((pred_start, pred_end), (exp_start, exp_end)))   # 缺失则 None
time_bonus      = 0.2 if time_iou_score >= 0.5 else 0.0                       # 命中阈值奖励

# 默认权重（有 expected_time）
custom_correctness =
    0.4 × yes_no_score
  + 0.4 × video_id_score
  + 0.2 × min(1.0, time_iou_score + time_bonus)

# 当 expected_time 缺失时（重分配最后一项的 0.2 权重）
custom_correctness =
    0.5 × yes_no_score
  + 0.5 × video_id_score
```

实施前讨论清单：

- 当 `expected_answer_label = "no"` 时，`yes_no_score=1.0` 已经能拿 0.4 分；要不要直接给满分？"no" 类问题没有正确视频，不应再要求 video_id（建议：`expected_answer_label="no"` 时 `video_id_score` 跳过，权重重分配）
- "no" 类问题的 `predicted_answer_label` 怎么从 response 抽？目前 `summary_node` 输出 `"No matching clip is expected."` 是显式信号，但其他模板都是肯定句 → 用正则识别 `"No matching" / "Yes." / "The most relevant clip"` 三类
- `time_iou` 计算时，`expected_time` 模糊（如"约 0:01:00"）怎么处理？建议把 reference 的时间窗扩 ±5s tolerance
- 是否再加 `confidence` 子项（结合 verifier_decision）作为加成
- 旧 baseline 数字（0.48 等）能否反向计算？需要从 e2e_report 里重抽 fields 重新算（runner 加 `--rescore-only` 模式）
- predicted_answer_label / predicted_video_id / predicted_start_sec / predicted_end_sec 这些字段 runner 已经写出，无须改 agent 输出

#### RAGAS LLM 评分参数变更

- `temperature=0`（runner 里 `LangchainLLMWrapper(ChatOpenAI(model="...", temperature=0))`，当前未显式传，跟 client 默认）
- 仍保留 retry，但失败计入 `metric_errors`，不被 silent drop

#### `ragas_e2e_score_avg` 重定义

```
ragas_e2e_score = mean([
    context_precision,        # RAGAS retrieval
    context_recall,           # RAGAS retrieval
    faithfulness,             # RAGAS generation
    custom_correctness,       # task-native (替代 factual_correctness)
])
```

#### 改造范围（实施时）

- 文件：
  - `agent/test/ragas_eval_runner.py`：新建 `_score_custom_correctness()` + 替换 `factual_correctness` 注入点 + LLM `temperature=0`
  - 新文件 `agent/test/test_custom_correctness.py`：覆盖 yes/no 路径、video 错、time_iou 边界、缺失 expected_time、加权
  - `agent/challenge.md`：新增一节描述 `custom_correctness` 含义与权重出处
- 兼容性：保留旧 e2e_report 字段名（`factual_correctness` 写 None），加新字段 `custom_correctness`

#### 预期收益

- `custom_correctness` 跨次评测**完全确定**（同 response 永远同分），可清晰识别 ±0.005 级别的改造收益
- RAGAS 子集（precision/recall/faithfulness）+ temperature=0 → 抖动从 ±0.15 降到 ±0.05 量级（推测）

#### 决策时机

下个 session（不在本次 commit 内）。本次 commit 只把决策记录到 `todo.md` 与本节。

### P1-5 + P3-3 清理"僵尸代码 / legacy 死路径" ✅ DONE（2026-05-02）

> 用户决策：全手术 —— 一次性清掉 `SQLiteGateway` + `merged_result` + 整个 `legacy_router` 链路（`tool_router_node` / `reflection_node` / `cot_engine` / `router_prompts` / `query_optimizer` / `error_classifier`）。

#### 删除的文件（8 个，约 -123KB）
- `agent/node/tool_router_node.py`（19580 bytes）
- `agent/node/router_prompts.py`（2205 bytes）
- `agent/node/reflection_node.py`（37435 bytes）
- `agent/node/cot_engine.py`（12051 bytes）
- `agent/node/query_optimizer.py`（3254 bytes，零外部 import）
- `agent/node/error_classifier.py`（3132 bytes，仅被 query_optimizer 引）
- `agent/node/tool_router_node.cover`、`agent/node/cot_engine.cover`（coverage artifacts）

#### 删除的代码段
- `agent/tools/db_access.py`：删 `SQLiteGateway` 类（`object_color_cn` 已脱 schema，零外部调用），同步删 `import sqlite3`
- `agent/node/types.py`：删 `merged_result` 字段定义 + `EPHEMERAL_FIELDS` 中的默认值
- `agent/node/parallel_retrieval_fusion_node.py`：返回 dict 中两处 `"merged_result": ...` 删除
- `agent/node/hybrid_search_node.py`：返回 dict 中 `"merged_result": ...` 删除；`execution_mode="legacy_router"` → `"parallel_fusion"`
- `agent/node/pure_sql_node.py`：`execution_mode="legacy_router"` → `"parallel_fusion"`
- `agent/node/summary_node.py / answer_node.py / match_verifier_node.py`：`_select_rows` / `_select_final_rows` 里的 `merged_result` fallback 分支删除
- `agent/test/ragas_eval_runner.py`、`agent/test_somke/result_test_runner.py`、`agent/test_somke/comprehensive_test_runner.py`：同上 fallback 分支删除

#### graph_builder.py 简化
- 删 3 个 legacy import：`reflection_node` / `tool_router_node` / `agents.build_*`
- 删整个 `_build_legacy_router_graph` 函数
- `build_graph` 简化：直接返回 `_build_parallel_fusion_graph`；`init_prompt_text` 参数保留但 `del` 掉，兼容老调用方

#### 文档同步
- `agent/architecture.md`：删 legacy_router 子图，加 verifier 节点说明
- `agent/routing_rules.md`：彻底重写，去 RR-LEGACY-* 三条
- `agent/graph_structure.md`：单一 parallel_fusion 子图
- `agent/agents/README.md`：去掉 `AGENT_EXECUTION_MODE=legacy_router` 提示
- `agent/node/README.md`：重写文件清单 + 已删除清单
- `agent/test_somke/01_测试模块汇总.md`：删 §4（tool_router）、§5（reflection），加 verifier 段
- `agent/test_somke/02_测试要求规格说明书.md`：`merged_result` → `rerank_result`
- `agent/lightingRL/todo.md`：删 legacy 备注
- `deploy.md`：删 `AGENT_EXECUTION_MODE`，补当前活跃 env flags

#### 验证
- `python -m pytest agent/test/test_*.py`：**64/64 全过**（既有 + 新加 P1-Next-A 单测 + P1-3 单测）
- graph compile smoke（默认 + `AGENT_DISABLE_VERIFIER_NODE=1` 两种模式）：✅ 全过；reflection_node / tool_router_node 已不在 nodes 列表

#### 影响范围 / 已知边界
- **完全废弃 `AGENT_EXECUTION_MODE=legacy_router` 模式**；旧脚本设此 env 无效（默认仍走 parallel_fusion，behaviour 兼容）
- `pure_sql_node.py` / `hybrid_search_node.py` 文件保留（仍是 sub-agent 接口），但不再被默认 graph 引用
- 全 codebase 净减约 -4000 / +50 LoC
- 详细复盘见 `agent/调试记录.md` §11

#### 回滚
- 无灰度 flag —— 此次为终态删除。如需恢复 legacy_router，必须 `git revert` 整个 commit。建议先确认线上无 `AGENT_EXECUTION_MODE=legacy_router` 残留再 push。

### P1-6 路由收敛：SQL 只做融合通道，不再作终态分支 ✅ DONE（2026-05-01 完成；P1-5/P3-3 后描述已过时）

> 历史描述：本段落原描述按 `AGENT_LEGACY_DISABLE_PURE_SQL_TERMINAL` 等灰度口"不破坏 legacy_router"做收敛。
> 2026-05-02 P1-5/P3-3 把整个 `legacy_router` 链路一次性废弃了（见上方对应段），所以 `AGENT_LEGACY_DISABLE_PURE_SQL_TERMINAL` 等灰度口已不再需要、相关代码删除。本段落保留作历史归档。

- 文件：`agent/agents/shared/query_classifier.py`、`agent/agents/shared/fusion_engine.py`、`agent/node/parallel_retrieval_fusion_node.py`
- 改造已落地的部分：
  - 新增 `multi_hop` classifier label，`classify_mode_from_label` 映射为 hybrid 兼容模式
  - 分类器输出 `signals = {metadata_hits[], relation_cues[], multi_step_cues[], existence_cues[]}`，fast-path 从"句式白名单"改为"信号型证据"
  - `weighted_rrf_fuse` 新增可选 `signals` 关键字参数，按证据数量对 `{sql, hybrid}` 权重做 soft-bias（±0.2 封顶）
  - `parallel_retrieval_fusion_node` 把 `signals` 透传给 `weighted_rrf_fuse`，并在 `fusion_meta.signals` 中留痕
- 验收：
  - 默认图走 parallel_fusion 时，10 例 e2e 结果 `fusion_meta.signals` 非空
  - `test_weighted_rrf_fuse.py` / `test_extract_text_tokens_for_sql.py` / `test_pure_sql_fallback.py` 全绿

### P1-7 存在性 grounder：retrieve → verifier → answer

- 文件：`agent/node/#match_verifier_node.py`（恢复成 `match_verifier_node.py`）、`agent/node/answer_node.py`、`agent/node/query_classification_node.py`、`agent/node/types.py`、`agent/graph_builder.py`、`agent/agents/shared/query_classifier.py`
- 现状：默认图是 `parallel_retrieval_fusion_node → final_answer_node`，没有"这些 chunk 是否真能回答 yes/no"这一步，这是 faithfulness 偏低与存在性问题偏乐观的主要原因之一
- 改造：
  - classifier 新增 `answer_type ∈ {existence, list, description, count, unknown}`，通过 prompt + 启发式同时填（"Is there / Did you see / 有没有" → existence）
  - `query_classification_node` 把 `answer_type` 写到 `state.answer_type`，并在 `classification_result` 里保留一份
  - `#match_verifier_node.py` 搬回 `match_verifier_node.py`；仅当 `answer_type == "existence"` 时才跑 LLM/启发式裁决，其他情况直接 pass-through，不动 rerank 结果
  - `final_answer_node`：
    - 非 existence：保持原"列出 top-5 结果"行为
    - existence + verdict=mismatch：返回结构化的 "No matching clip found."
    - existence + verdict=exact/partial：返回 "Yes. Video=, start=, end=. Summary=..."，形成 RAGAS/E2E 评测期待的格式
  - `graph_builder._build_parallel_fusion_graph` 插入 `match_verifier_node` 到 `parallel_retrieval_fusion_node → final_answer_node` 之间
  - `AgentState` 新增 `answer_type / verifier_result` 字段，并加入 `StateResetter.EPHEMERAL_FIELDS`
- 验收：
  - 10 例 e2e 回归：existence 子集上 `faithfulness` 均值 ≥ 0.55（当前 ~0.375），且 `top_hit_rate` 不退步
  - `ragas_eval_runner` 的 e2e_report 每条带有 `verifier_result`（mismatch/partial/exact + reason）
  - 非 existence 问题行为与改造前完全一致（`rerank_result` 未修改）

### P1-Next-A 收紧 summary_node bail-out ✅ DONE（2026-05-02）

- 文件：`agent/node/summary_node.py`、新文件 `agent/test/test_summary_node_bail_out.py`、`agent/graph_builder.py`（附带 `AGENT_DISABLE_VERIFIER_NODE` sanity flag）
- 现状（改造前）：`summary_node` 里有**3 道串联锁**导致 retrieval-correct case 输出 "No matching clip is expected."
  - 锁 1（`summary_node.py:212-227`）：LLM prompt 里 `"answer exactly: No matching clip is expected."` 主观 bail-out 指令
  - 锁 2（`_normalize_summary_output`）：字符串短路 —— LLM 输出含此短语就强制返回此短语
  - 锁 3（`_canonicalize_summary`）：normalize 输出是 `"No matching"` 时直接放行
- 改造实施：
  - prompt 按 `len(rows)` 分支构造：`rows == 0` 才有"No matching"指令；`rows > 0` 显式禁止 LLM 输出该短语
  - `_normalize_summary_output(text, fallback, *, allow_no_match=True)`：新增参数；False 时把 `"No matching"` 字符串短路 demote 为 fallback
  - `_canonicalize_summary(..., answer_type, verifier_decision, grounder_enabled, bail_out_strict)`：新增 4 个上下文参数；`_allow_no_match_decision()` 真值表函数判断是否允许放行
  - 真值表：`rows==[] | bail_out_strict=False | (grounder_ON & answer_type==existence & verifier=mismatch)` → 允许；其他 → demote
  - env flag `AGENT_SUMMARY_BAIL_OUT_STRICT=0/1`（默认 1=新行为）作为灰度回滚口
  - 同步加 `AGENT_DISABLE_VERIFIER_NODE=0/1`（默认 0），在 `_build_parallel_fusion_graph` 里 short-circuit `match_verifier_node`，用于 sanity 测试 / 节省 LLM quota
- 单测：`agent/test/test_summary_node_bail_out.py` 20 例（`AllowNoMatchDecisionTests` 6 + `NormalizeSummaryOutputTests` 3 + `CanonicalizeSummaryTests` 4 + `SummaryNodeIntegrationTests` 6 + `SummaryNodeNoLLMFallbackTests` 1），含 prompt 内容断言（用 `_StubLLM` 捕获 prompt 验证 rows>0 时不含 bail-out 指令）；与既有 34 例一起 **54/54 全过**
- 在线验证（50-case e2e，`agent/test/generated/ragas_eval_e2e_n50_p1_next_a_v1/`）：
  - **`No matching clip is expected.` case 数：12 → 0（确定性消除，核心 KPI）**
  - **12 个原 No-matching 子集 factual avg：0.1667 → 0.2083（+25% rel，对照组锁死无 RAGAS 噪声）**
  - `factual_correctness_avg`：0.48 → 0.60（+0.12，含 RAGAS 评分本身 ±0.10-0.15 的随机噪声）
  - `top_hit_rate / context_precision / localization` 全部不变 → 改造无副作用
- 已知边界 / 后续 P1-Next-A.5：
  - 4 个 case（PART1_0018/_0022/_0036/_0039）改造后输出正确 video_id 但 factual 仍 0，因为 reference 含 scene 描述（rich 模板`"Yes. In <video> around <time>, <scene>."`），当前 fallback 只给 video+time
  - P1-Next-A.5 待办：`_build_factual_summary` 加 `event_summary_en[:80]` 截取，预期再 +0.04 fc avg
- 兼容性 / 回滚：
  - `AGENT_SUMMARY_BAIL_OUT_STRICT=0` 立即回到旧 bail-out 全允许
  - `AGENT_DISABLE_VERIFIER_NODE=1` 从 graph 中剔除 verifier（advisory 模式无效果差异，仅省 LLM quota）
  - 详细复盘见 `agent/调试记录.md` §10

---

## P2 中期（1 个月内，增加自修复与跨语言能力）

### P2-1 引入 verifier + 二次检索

- 文件：`agent/node/#match_verifier_node.py`（当前冻结）→ 恢复为 `match_verifier_node.py`
- 改造：
  - 默认图改为：`parallel_retrieval_fusion_node → match_verifier_node → final_answer_node`
  - verifier 判断：
    - 结果数=0 → 放宽 filter / 切换 query 改写 / 再跑一次 parallel（最多 1 次）
    - 结果数>0 但 rerank 置信度低 → 触发 parent→event 下钻
  - retry 次数写进 `state.retry_count`，避免死循环
- 验收：`top_hit_rate` 提升 ≥ 5 个百分点

### P2-2 SQLite schema 归一化

- 文件：`agent/db/schema.py`、`sqlite_builder.py`
- 现状：单表塞所有字段，无 JOIN 能力，`metadata_json` 冗余
- 改造（破坏性，需要评测前后对比）：
  - 拆成 `videos / tracks / events` 三张表，FK 串联
  - 去掉 `metadata_json` 字段
  - `keywords_json` 和 `semantic_tags_json` 合并为一份
  - 增加 Alembic 或手写 migration 脚本，真正用起 `schema_version`
- 验收：
  - 新 schema 下所有 SQL 测试通过
  - 增量 ingestion 支持 upsert 而不是 truncate

### P2-3 中文支持

- 文件：`agent/db/chroma_builder.py`、`agent/node/self_query_node.py`
- 方案 A（推荐）：
  - `_build_child_document` 追加 `event_summary_cn / appearance_notes_cn` 字段（若源数据含中文）
  - 同一条记录同时 embed 中英文文本（拼接）
- 方案 B：
  - `self_query_node` 在改写后强制翻译到英文再检索，原始 query 仅保留在 summary 阶段
- 验收：中文 query 的 top hit 率提升

### P2-4 ThreadPoolExecutor → asyncio

- 文件：`agent/node/parallel_retrieval_fusion_node.py:162-173`
- 现状：`timeout` 后线程不会真正停止，积累僵尸请求
- 改造：
  - 两条分支提供 async 版本（`_run_sql_branch_async / _run_hybrid_branch_async`）
  - 用 `asyncio.wait_for` + `task.cancel()`
  - SQLite 查询走 `asyncio.to_thread`，embedding 走 async HTTPX client
- 验收：超时后 process 级不再有残留连接

### P2-5 统一 RetrievalTrace 可观测对象

- 新文件：`agent/node/retrieval_trace.py`
- 改造：
  - 定义 dataclass `RetrievalTrace`，包含 `sql_branch / hybrid_branch / fusion / rerank / verifier / final` 六段
  - 所有节点统一写入 `state["retrieval_trace"]`，不再散落在 `sql_debug / routing_metrics / metrics / search_explain`
  - `ragas_eval_runner.py` 输出 per-case trace JSON，方便事后分析 bad case
- 验收：单个 case 的所有阶段信息可以从一个字段读出

---

## P3 架构级（按需排期）

### P3-1 配置中心化

- 新文件：`agent/config/retrieval.yaml`
- 现状：检索参数散落在
  - 环境变量 `AGENT_`*
  - `retrieval_contracts.DEFAULT_SEARCH_CONFIG`
  - `fusion_engine.load_fusion_weights`
  - 各 node 内部常量
- 改造：
  - 单一 YAML 真源，启动时 load 到 state
  - env 变量只保留 overrides
  - 每个节点从 state 读配置，不再直接 `os.getenv`

### P3-2 self-query / classifier 改为 seed profile 驱动

- 文件：`agent/node/self_query_node.py:70-89`、`agent/agents/shared/query_classifier.py:49-79`
- 现状：fast-path 关键字硬编码 basketball + UCFCrime 域
- 改造：
  - 建库时已生成 `agent/init/agent_init_profile.json`（object_types / colors / keywords）
  - fast-path 规则从 profile 动态载入，而不是写死在代码
  - 跨域只需要重建库 + 重生成 profile，代码层零改动
- 验收：切换到非 basketball 数据集时 self-query / classifier 仍可用

### P3-3 删除冗余路径 / 死代码 ✅ DONE（2026-05-02，与 P1-5 合并执行）

> 与 P1-5 一起做的"全手术"清理。详见 `### P1-5 + P3-3 清理"僵尸代码 / legacy 死路径"` 段落上面。
> 总结：6 个 legacy 节点文件删除、`SQLiteGateway` 删除、`merged_result` 字段删除、`legacy_router` 模式整体废弃、graph_builder 简化、9 篇文档同步、64/64 单测通过。

---

## 阶段性验收

### 阶段一（P0 完成）

- Time IoU avg ≥ 0.25（现在 0.13）
- Top hit rate ≥ 0.5（现在 0.4）
- 不引入新的失败 case

### 阶段二（P1 完成）

- Context precision avg ≥ 0.3（现在 0.18）
- Context recall avg ≥ 0.3（现在 0.15）
- 评测 latency 下降 ≥ 30%

### 阶段三（P2 完成）

- 引入 verifier 后自修复至少拯救 10% bad case
- 中文 query 的 top hit 率不低于英文 -10%

### 阶段四（P3 完成）

- 切换到新数据集零代码改动可复用

---

## 风险与回滚

- **P0-1 关闭 parent_projection**：如果 eval 出现回归，用 `AGENT_DISABLE_PARENT_PROJECTION=0` 立即恢复
- **P0-2 event collection**：只新增 collection，不影响 child / parent 现有行为
- **P1-1 FTS5**：已落地；建库失败时 `_create_fts5` 自动降级为 False；运行时 `AGENT_SQL_USE_FTS5=0` 立即回退 LIKE
- **P1-2 去伪 BM25**：feature flag `AGENT_HYBRID_BM25_FUSED=0/1`（默认 1）已落地，需要回滚时 `export AGENT_HYBRID_BM25_FUSED=0` 即可退回纯向量
- **P2-2 schema 归一化**：必须保留旧表建库入口作为回滚口，至少一个 release 周期

---

## 交付清单

- P0 PR：parent_projection default off + event collection + guardrail 放宽 + 停用词修复
- P1 PR：FTS5 + hybrid 真 hybrid + embedding cache + summary 双档 + 僵尸代码清理
- P2 PR：verifier 节点 + schema 归一化 + 中文支持 + asyncio + RetrievalTrace
- P3 PR：配置中心化 + profile 驱动 + archive 清理
- 每个 PR 必须附：一次完整 `ragas_eval_runner` 的前后指标对比表

