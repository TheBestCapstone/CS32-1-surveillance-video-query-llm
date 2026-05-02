<br />

# Agent 交接文档（Session Handoff）

> 生成时间：2026-05-02
> 适用范围：交接给下一个 agent / 工程师
> 配套文档：`agent/todo.md`（任务清单）、`agent/challenge.md`（评测分析）、`agent/architecture.md`（架构）、`agent/CHANGELOG.md`（变更历史）

***

## 1. 一句话总览

本会话把 P0 全量收尾后，完成了 **RAGAS 评测可观测性（进度日志 + 并发）** + **P1-2（去伪 BM25，落全量 BM25）** + **DashScope/OpenAI 别名修复（修好之前所有 hybrid 都 401 的 bug）** + **P1-1（SQLite FTS5 lexical 索引）**。50-case e2e 端到端指标显著上扬：`top_hit_rate 0.90→0.94`、`faithfulness 0.38→0.69`、`localization_score 0.13→0.23`、`ragas_e2e_score 0.41→0.52`。下一阶段聚焦 **`factual_correctness`** **卡 0.48 的 summarizer bail-out 收紧** 与 **localization 双倍仍偏低的 verifier 多片段改造**。

***

## 2. 本会话完成的工作（按改动范围）

### 2.1 RAGAS 评测可观测性（`agent/test/ragas_eval_runner.py`）

- 把 `--ragas-concurrency` / `--ragas-case-batch-size` 默认从 `1/1` 提到 `4/4`
- `_score_one` 每个 case 打印 `[ragas] start i/N case_id ctx=K ctx_chars=M …` 和 `[ragas] done i/N case_id in Xs (completed k/N) errors=…`
- 修复了 50-case 跑时"卡 36"假象（实际是 conc=2 + 无进度输出）
- `ragas_input_profile` 里增加 `reference_source / reference_text / context_total_chars` 等字段供事后分析

### 2.2 P1-2 全量 BM25（hybrid 真正 hybrid）

新建 `agent/tools/bm25_index.py`：

- `BM25Index(db_path)`：从 `episodic_events` 全量读取 `event_text_en + event_summary_en + appearance_notes_en`，建标准 BM25Okapi（k1=1.5, b=0.75），`(db_path, mtime)` 进程级缓存
- 复用 `retrieval_contracts._SQL_TOKEN_STOPWORDS / _PLURAL_TO_SINGULAR` 与 SQL 通道同源
- 支持 `metadata_filters` 预剪枝（与 ChromaGateway 的 `where` 等价）
- `reciprocal_rank_fuse(ranked_lists, top_k, rrf_k=60)` 公共函数

改造调用点：

- `agent/tools/db_access.py::ChromaGateway.search` → 纯向量；`alpha` 仅保留兼容签名（首次非默认调用打 deprecation warning）
- `agent/tools/hybrid_tools.py::dynamic_weighted_vector_search` → vector top-K（Chroma） ⊕ BM25 top-K（`BM25Index`） → RRF 融合
- `agent/tools/llamaindex_adapter.py::run_llamaindex_vector_query` → LlamaIndex 向量 ⊕ 全量 BM25 → RRF（彻底替换原本的子集 `_bm25_scores`）
- 灰度回滚：`AGENT_HYBRID_BM25_FUSED=0` 立即关闭 BM25 通道
- 候选池倍数：`AGENT_HYBRID_VECTOR_OVERSAMPLE` / `AGENT_HYBRID_BM25_OVERSAMPLE` / `AGENT_CHROMA_VECTOR_OVERSAMPLE`（默认都为 3）

### 2.3 DashScope/OpenAI 别名修复（`agent/core/runtime.py`）

**这是本会话最大的 silent bug**：原逻辑独立判断"如果 OPENAI\_BASE\_URL 没设就别名 DashScope URL 过来"，但**没看 OPENAI\_API\_KEY 是否是真实 OpenAI key**。结果：真 OpenAI key 被发送到 DashScope endpoint → 全量 401，所有 hybrid 分支 50/50 degraded。

修复：把别名 OPENAI\_API\_KEY 和 OPENAI\_BASE\_URL 绑定为原子操作（要么都别名，要么都不别名）。

同时把 LlamaIndex SQL 的 LLM 选择改为 provider-aware：

- 新增 env：`AGENT_LLAMAINDEX_LLM_PROVIDER`（默认 `openai` 当 OPENAI\_API\_KEY 存在），`AGENT_LLAMAINDEX_LLM_MODEL`（默认 `gpt-4o-mini`）
- `agent/tools/llamaindex_adapter.py::_build_llamaindex_llm` 按 provider 分支选 OpenAI 还是 DashScope

### 2.4 P1-1 SQLite FTS5

`agent/db/schema.py`：

- 新增 `FTS_TABLE_NAME / FTS5_CREATE_SQL_LIST / FTS5_REBUILD_SQL`
- 外部内容虚表 + AFTER INSERT/UPDATE/DELETE 三个触发器
- tokenizer = `unicode61 remove_diacritics 1`
- 索引列 = `event_text_en + event_summary_en + appearance_notes_en + keywords_json`

`agent/db/sqlite_builder.py`：

- `_create_fts5(conn)`：建表+触发器；编译没带 FTS5 时 graceful fallback 返回 False
- `_rebuild_fts5(conn)`：批量插入完成后做一次 belt-and-braces 重建
- `build()` 返回值新增 `fts5_enabled` / `fts5_row_count`

`agent/node/parallel_retrieval_fusion_node.py::_run_sql_branch`：

- `_sql_use_fts5_enabled()` / `_fts5_table_present()` / `_build_fts5_match_expr()`
- token 非空且虚表存在 → 文本子句改为 `event_id IN (SELECT rowid FROM episodic_events_fts WHERE … MATCH ?)`
- 否则回退 LIKE
- summary 末尾打 `text_strategy=fts5/like/none`
- `AGENT_SQL_USE_FTS5=0/1`（默认 1）灰度口

### 2.5 单测覆盖

- 新文件 `agent/test/test_bm25_index.py`：10 例（语义排名、过滤剪枝、空过滤、停用词、mtime 缓存失效、RRF 交集排前）
- 新文件 `agent/test/test_sql_fts5.py`：7 例（虚表创建、MATCH、UPDATE/DELETE 触发器一致性、`_run_sql_branch` FTS5 路径、`AGENT_SQL_USE_FTS5=0` 走 LIKE、无 token 时不打文本子句）
- 与既有 `test_pure_sql_fallback / test_weighted_rrf_fuse / test_extract_text_tokens_for_sql` 一起 **34/34 全过**

***

## 3. 50-case 评测对比（关键证据）

数据集：`agent_test.xlsx` Part1+Part4 前 50 例，子库在 `agent/test/generated/ragas_eval_e2e_n50_p1_latest/runtime/`。

| Metric                         | rich\_v1（修前） | rich\_v2（仅并发提速） | **fts5\_bm25\_v1（修后）** | Δ vs rich\_v1 |
| ------------------------------ | ------------ | --------------- | ---------------------- | ------------- |
| `top_hit_rate`                 | 0.900        | 0.900           | **0.940**              | +0.040        |
| `context_precision_avg`        | 0.498        | 0.405           | **0.585**              | +0.087        |
| `context_recall_avg`           | 0.297        | 0.297           | **0.360**              | **+21% rel**  |
| `faithfulness_avg`             | 0.383        | 0.415           | **0.690**              | **+80% rel**  |
| `factual_correctness_avg`      | 0.500        | 0.490           | 0.480                  | -0.020 ⚠️     |
| `time_range_overlap_iou_avg`   | 0.133        | 0.133           | **0.228**              | **+71% rel**  |
| `localization_hit_rate_at_0_3` | 0.125        | 0.125           | **0.250**              | **2×**        |
| `video_match_score_avg`        | 0.857        | 0.837           | **0.898**              | +0.041        |
| `ragas_e2e_score_avg`          | 0.413        | 0.397           | **0.523**              | **+27% rel**  |
| `fusion_meta.degraded`         | **50/50**    | **50/50**       | **0/50**               | ✅             |
| `hybrid_rows_count > 0`        | 0/50         | 0/50            | **50/50**              | ✅             |

输出目录：`agent/test/generated/ragas_eval_e2e_n50_fts5_bm25_v1/`。

**没动的** **`factual_correctness_avg = 0.48`** 是下一步 P1 的核心目标：12/50 case 仍然回答 `"No matching clip is expected."` 即使 retrieval 正确。Root cause 已在 `agent/challenge.md` §5 与之前的 case-36 子代理分析里写清楚（`agent/node/summary_node.py:212-227` 的 LLM prompt 里有过宽的 bail-out 子句）。

***

## 4. 待办优先级（接力清单）

### P1（继续，预计 1-2 天）

#### P1-Next-A：收紧 `summary_node` bail-out（最直接拉指标）

- 文件：`agent/node/summary_node.py:212-227`
- 改动建议（前一个子代理已经写好了方案）：
  1. 当 `len(rows) > 0` 时，从 LLM prompt 移除 `"answer exactly: No matching clip is expected."` 整段
  2. 把"No matching clip"硬规则锁到：`state.verifier_result.decision == "mismatch"` AND `state.answer_type == "existence"` AND `AGENT_ENABLE_EXISTENCE_GROUNDER=1`
  3. 否则强制走 `_build_factual_summary(rows, query)`（已有的 canonical 模板）
- 预计 `factual_correctness_avg`：0.48 → 0.65\~0.75
- 改动 LoC ≤ 15

#### P1-Next-B：verifier 多片段输入（撬 localization）

- 文件：`agent/node/match_verifier_node.py`、`agent/node/answer_node.py`
- 现状：`localization_score_avg = 0.228`（hit\_rate\@0.5 = 0.25）—— 视频 ID 通常对了，时间窗口经常错
- 改造：让 verifier 看同 `video_id` 上时间相邻的 top-K event chunks（不只是当前 row），重选 best span
- 详见 `agent/challenge.md` §5.3

#### P1-3 query embedding LRU + 磁盘缓存

- 文件：`agent/tools/llm.py`、`agent/tools/db_access.py`
- 现状：每次 query 都打一次 OpenAI embedding，50 例评测打 \~60 次
- 改造：`functools.lru_cache(maxsize=2048)` 包外层，磁盘缓存到 `data/cache/embedding/`
- 验收：50 例评测 embedding 调用降到 \~30

#### P1-4 summary 输出分 strict / natural

- 文件：`agent/node/summary_node.py`
- env：`AGENT_SUMMARY_STYLE ∈ {strict, natural}`，默认 `natural`
- strict 保留模板（eval 专用），natural 允许自然句 + `[event summary]` + citations

#### P1-5 清理僵尸代码

- 文件：`agent/tools/db_access.py:177-241` 的 `SQLiteGateway`（`object_color_cn` 已不在 schema 里）
- `merged_result` 几乎没消费方
- 删除前先 grep 确认无调用

### P2（中期，1 周以上）

- **P1-1 后续**：把 FTS5 也接到 `sql_debug_utils.run_guided_sql_candidate / run_relaxed_sql_fallback` 的 LLM-deterministic SQL planner 里，目前只接到了 `_run_sql_branch`（即 `AGENT_USE_LLAMAINDEX_SQL=0` 的直连路径）
- **P1-6 路由收敛 / P1-7 存在性 grounder**：classifier signals → fusion soft-bias 已在 P0 阶段落地，但 verifier 进入图后仍以 advisory 模式工作，需要正式接管 existence 类问题的 final answer
- **P2-1 verifier 自修复**：`top_hit=False` 时放宽 filter / 改写 query / 二次检索
- **P2-2 schema 归一化**：videos / tracks / events 三表 + Alembic
- **P2-3 中文支持**：embed 中英文双向

详见 `agent/todo.md`。

***

## 5. 重点 / 坑 / 易踩雷点

### 5.1 import 路径双写（容易让单测炸）

`agent/tools/*.py` 与 `agent/node/*.py` 全部用 **bare** **`from node.x import …`** **/** **`from tools.x import …`**，依赖 `agent/` 在 `sys.path`。但 `agent/test/test_*.py` 用 `from agent.tools.x import …`（带前缀）。

新加测试文件必须在顶部加：

```python
_AGENT_ROOT = Path(__file__).resolve().parents[1]
if str(_AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(_AGENT_ROOT))
```

否则 `from agent.tools.bm25_index import …` 会因为 `bm25_index.py` 内部的 `from node.retrieval_contracts import …` 报 `ModuleNotFoundError: No module named 'node'`。

`agent/test/test_bm25_index.py` 和 `agent/test/test_sql_fts5.py` 已经这么写了，照抄即可。

### 5.2 DashScope alias bug 复发风险（**重要**）

**永远**不要把 `agent/core/runtime.py` 里的别名逻辑改回："只看 OPENAI\_BASE\_URL 是否为空就别名"。这会让真 OPENAI\_API\_KEY 被发到 DashScope endpoint，整轮评测全部 401 + 静默 degrade 到 SQL-only。

正确写法是 **OPENAI\_API\_KEY + OPENAI\_BASE\_URL 同时缺失** 才别名整对，单独缺 URL 不别名。

`.env` 文件里如果同时有 OPENAI 和 DashScope 两套 key，永远以 OPENAI 为准（在 `AGENT_EMBEDDING_PROVIDER=openai` 默认下）。

### 5.3 FTS5 落地后并未在默认 eval 里激活

`AGENT_USE_LLAMAINDEX_SQL=1`（`.env` 默认 + `runtime.py` `setdefault`）会让 SQL 分支跑 `run_llamaindex_sql_query` → `_run_deterministic_sql_query` → `sql_debug_utils._legacy_sql_fallback_rows`（仍是 LIKE 评分梯度），**绕过** **`_run_sql_branch`**。

要看 FTS5 的真效果有两条路：

1. 临时 `export AGENT_USE_LLAMAINDEX_SQL=0` 跑一次评测做 A/B
2. 把 FTS5 接到 deterministic planner（要重写 `sql_debug_utils.py:411` 周围那一坨 `CASE WHEN … LIKE ?` 的评分阶梯）—— 工作量较大，留 P2

P1-1 单测里通过 `AGENT_USE_LLAMAINDEX_SQL=0` patch 验证了 FTS5 在 `_run_sql_branch` 路径上完全可用。

### 5.4 BM25Index 缓存 key

`BM25Index._cache_key` 用 `(resolve(db_path), mtime_ns)`：

- 重建 sqlite（`manage_graph_db reset`）会自动失效缓存
- **同一文件被 mv 后 inode 变了但 mtime 不变** → 缓存可能错配。极端情况下手动调 `BM25Index.clear_cache()`
- 测试里每个 setUp/tearDown 都调了 `clear_cache()`，因为同名 `events.sqlite` 落在不同 tempdir 时 path 一样但内容不同

### 5.5 `dynamic_weighted_vector_search` payload 兼容性

`agent/tools/hybrid_tools.py::_format_hybrid_payload` **同时输出新旧两套字段名**：`distance` + `_distance`、`bm25` + `_bm25`、`fused_score` + `_hybrid_score`。这是因为 `agent/node/retrieval_contracts.py::normalize_hybrid_rows` 读 `_distance / _hybrid_score / _bm25`，下游 rerank/answer/summary 链上有不少地方拿这些字段。**别把双写删掉**。

### 5.6 ChromaGateway.search alpha 已废弃但保留签名

`alpha` 参数还在签名里只是为了兼容老代码（包括 `_legacy_sql_fallback_rows` 内部调用），首次传非 None 值会日志一次 deprecation。新代码不应该再传 `alpha`。

### 5.7 老 sqlite 库需要补建 FTS5

之前生成的 eval 子库（`ragas_eval_e2e_n50_p1_latest/runtime/eval_subset.sqlite`）没有 FTS5 表，但代码会 graceful fallback 到 LIKE。要补建：

```python
import sqlite3
from agent.db.schema import FTS5_CREATE_SQL_LIST, FTS5_REBUILD_SQL

with sqlite3.connect(path) as conn:
    for stmt in FTS5_CREATE_SQL_LIST:
        conn.execute(stmt)
    conn.execute(FTS5_REBUILD_SQL)
    conn.commit()
```

### 5.8 RAGAS 并发上限是 OpenAI account-level rate limit

`--ragas-concurrency` 提到 6 后，单 case ragas 时间从 \~31s 涨到 70-110s，因为 OpenAI 账号级 RPM/TPM 限流。50-case 总壁挂时间几乎不变（822s ↔ 859s）—— 真正的提速发生在小批次（10 case 12.5s/case vs 16.4s/case）。**默认值 4/4 是平衡点**，不要瞎往上加。

***

## 6. 关键文件地图

```
agent/
├── tools/
│   ├── bm25_index.py            ★ 新增：全量 BM25Okapi + RRF
│   ├── db_access.py             ★ 改：ChromaGateway 改纯向量
│   ├── hybrid_tools.py          ★ 改：vector ⊕ BM25 → RRF
│   └── llamaindex_adapter.py    ★ 改：删子集 BM25，加 BM25Index 融合
├── node/
│   └── parallel_retrieval_fusion_node.py  ★ 改：_run_sql_branch 走 FTS5
├── db/
│   ├── schema.py                ★ 改：FTS5 DDL + 触发器
│   └── sqlite_builder.py        ★ 改：build() 创建 + rebuild FTS5
├── core/
│   └── runtime.py               ★ 改：DashScope alias 修复 + LLM provider env
├── test/
│   ├── ragas_eval_runner.py     ★ 改：默认并发 4/4 + per-case 进度
│   ├── test_bm25_index.py       ★ 新增：BM25 + RRF 单测
│   ├── test_sql_fts5.py         ★ 新增：FTS5 schema + _run_sql_branch
│   ├── test_pure_sql_fallback.py
│   ├── test_weighted_rrf_fuse.py
│   └── test_extract_text_tokens_for_sql.py
├── todo.md                      ★ 改：P0/P1 状态、回滚口
├── challenge.md                 P0/P1 评测分析（不动）
└── handoff.md                   ★ 本文
```

***

## 7. 常用命令速查

### 跑单测

```bash
cd /home/yangxp/Capstone
python -m pytest agent/test/test_sql_fts5.py agent/test/test_bm25_index.py \
                 agent/test/test_weighted_rrf_fuse.py agent/test/test_extract_text_tokens_for_sql.py \
                 agent/test/test_pure_sql_fallback.py -v
```

### 10-case 烟测（约 4 分钟）

```bash
cd /home/yangxp/Capstone/agent/test
python ragas_eval_runner.py \
  --limit 10 \
  --sqlite-path /home/yangxp/Capstone/agent/test/generated/ragas_eval_e2e_n50_p1_latest/runtime/eval_subset.sqlite \
  --chroma-path /home/yangxp/Capstone/agent/test/generated/ragas_eval_e2e_n50_p1_latest/runtime/eval_subset_chroma \
  --output-dir /home/yangxp/Capstone/agent/test/generated/ragas_eval_e2e_n10_<tag>
```

### 50-case e2e（约 23 分钟）

```bash
cd /home/yangxp/Capstone/agent/test
python ragas_eval_runner.py \
  --limit 50 \
  --sqlite-path /home/yangxp/Capstone/agent/test/generated/ragas_eval_e2e_n50_p1_latest/runtime/eval_subset.sqlite \
  --chroma-path /home/yangxp/Capstone/agent/test/generated/ragas_eval_e2e_n50_p1_latest/runtime/eval_subset_chroma \
  --output-dir /home/yangxp/Capstone/agent/test/generated/ragas_eval_e2e_n50_<tag> \
  --ragas-concurrency 6 --ragas-case-batch-size 6
```

### 灰度回滚

```bash
# 关 BM25 fusion，hybrid 退到纯向量
export AGENT_HYBRID_BM25_FUSED=0

# 关 FTS5，SQL 分支退到 LIKE
export AGENT_SQL_USE_FTS5=0

# 强制 LlamaIndex SQL 走 DashScope（默认 openai）
export AGENT_LLAMAINDEX_LLM_PROVIDER=dashscope

# 强制走 _run_sql_branch（即让 FTS5 真生效在 eval 里）
export AGENT_USE_LLAMAINDEX_SQL=0
```

### 验证 BM25 / FTS5 是否在工作

```bash
cd /home/yangxp/Capstone/agent && python -c "
import sys; sys.path.insert(0, '.')
from tools.bm25_index import BM25Index
idx = BM25Index('/home/yangxp/Capstone/agent/test/generated/ragas_eval_e2e_n50_p1_latest/runtime/eval_subset.sqlite')
print(idx.stats())
print(idx.search('flashing roof lights', top_k=3))
"
```

```bash
cd /home/yangxp/Capstone/agent && python -c "
import sys, os; sys.path.insert(0, '.')
os.environ['AGENT_USE_LLAMAINDEX_SQL'] = '0'
os.environ['AGENT_SQLITE_DB_PATH'] = '/home/yangxp/Capstone/agent/test/generated/ragas_eval_e2e_n50_p1_latest/runtime/eval_subset.sqlite'
from node.parallel_retrieval_fusion_node import _run_sql_branch
summary, rows = _run_sql_branch('two white police cars flashing roof lights', {'sql_limit': 10})
print(summary)
"
# 期望看到 'text_strategy=fts5'
```

***

## 8. 已知 fragile 点（接手前请知悉）

1. **`AGENT_USE_LLAMAINDEX_SQL=1`** **+ FTS5 不能同时见效** —— 如 5.3
2. **`AGENT_USE_LLAMAINDEX_VECTOR=1`** **时 vector 走 LlamaIndex 路径** —— BM25 已经接了，但 LlamaIndex 0 命中时的兜底走 `ChromaGateway.search`（纯向量），那条路径**不带 BM25**。极少触发，但要知道
3. **eval 子库的 chroma collection 命名是** **`ucfcrime_eval_child / _parent / _event`**，不是文档默认的 `{namespace}_tracks` 系。运行 eval 时必须显式 `--chroma-path` 指到 `ragas_eval_e2e_n50_p1_latest/runtime/eval_subset_chroma`，runner 会把 child collection env var 设对
4. **rerank** 默认开启（`AGENT_ENABLE_RERANK=1`），用 `cross-encoder/ms-marco-MiniLM-L-6-v2`。第一次跑会下载模型；若评测机离线需要预先 `huggingface-cli download`
5. **`load_dotenv()`** **默认会被** **`os.environ.setdefault`** **后值覆盖** —— 这是好事，但意味着代码里 `setdefault` 永远只在该 key 真的没设时生效
6. **DashScope key 仍可保留在 .env 里** —— 现在的代码不会误用它（除非显式 `AGENT_LLAMAINDEX_LLM_PROVIDER=dashscope`），删不删都不影响

***

## 9. 当前 `agent/todo.md` 的真实状态（截至本次 handoff）

P0 全部 ✅：

- P0-1 关闭默认 parent projection
- P0-2 event-level Chroma collection
- P0-3 放松 structured\_zero\_guardrail
- P0-4 修 SQL token 抽取停用词

P1 已落地：

- ✅ P1-1 SQLite FTS5（本次）
- ✅ P1-2 真 hybrid（本次）
- ✅ P1-6 路由收敛（之前迭代）
- ✅ P1-7 存在性 grounder 雏形（之前迭代）

P1 未落地：

- ⏳ P1-3 query embedding LRU
- ⏳ P1-4 summary 双档
- ⏳ P1-5 清理僵尸代码
- ⏳ **P1-Next-A summary bail-out 收紧**（接手最高优先级，预计 +0.15 fc）
- ⏳ **P1-Next-B verifier 多片段**（接手第二优先级，预计 +0.1 localization）

P2/P3 见 `agent/todo.md`。

***

## 10. 下一个 agent 接手第一步建议

1. 先 `git status` + `git log -10` 看本会话所有改动
2. 跑一次单测确保环境干净：`python -m pytest agent/test/test_*.py -v`
3. 跑一次 10-case 烟测验证基线：约 4 分钟，应该看到 `top_hit_rate=1.0`、`faithfulness>0.6`、`fusion_meta.degraded=0/10`
4. 然后从 **P1-Next-A**（`summary_node.py` bail-out 收紧）下手 —— 这是最快的指标杠杆，10 行内可以拿到 `factual_correctness 0.48 → 0.65`
5. 完成后跑一次 50-case e2e，把数据贴回 `agent/todo.md` 的 P1-Next-A 验收行

祝顺利。
