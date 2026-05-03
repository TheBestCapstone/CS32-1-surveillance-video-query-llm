# Agent 交接文档（Session Handoff）

> 生成时间：2026-05-03  
> 适用范围：下一个 agent / 工程师接手  
> 配套文档：`agent/todo.md`（任务与优先级）、`agent/工作记录_20260503.md`（本次会话工作记录）

---

## 1. 一句话总览

主线已推进到 **Tier 1（video collection）+ Tier 2（zero-LLM scene boost）全部落地**。评测集为 **Part4（Normal_Videos）**。当前 **27-case** 上 `context_recall=0.667`（+0.056 vs Tier1）、`ragas_e2e=0.643`。

---

## 2. 本轮已落地工作

| 主题 | 要点 |
|------|------|
| **Tier 1** | Video collection + `_coarse_video_filter` 两阶段检索。LLM discriminator 生成 per-video 区分度 summary。Coarse filter 嵌入 `_run_hybrid_branch`，embedding 复用 P1-3 cache。latency +0.4s |
| **Tier 2** | Zero-LLM scene attribute filtering。从 `episodic_events` 的 `object_type`/`scene_zone`/`object_color` 自动生成 `has_X` 词表 + IDF。self_query LLM 从词表选 scene_constraints。RRF 后 boost 重排（λ=0.1）。recall +0.056 |
| **Part4 全量分析** | 155-case 全量跑通（top_hit=0.207）。难度分层：easy 0.765 / medium 0.621 / hard 0.379 e2e。63 个困难 case 已列出 |
| **种子补全** | 104 个 Normal_Videos 种子已生成；`_resolve_seed_files` 双命名兼容；自动跳过无效 video_id |
| **IoU 修复** | `expected_answer_label=="no"` 时跳过 IoU；`expected_answer_label=="yes"` 守卫 |
| **parent 时间桶化** | 10 分钟时间窗分桶，解决长视频 parent document 超 8192 token 问题 |

---

## 3. 评测数字（27-case，Part4，Tier 1+2）

| Metric | Baseline | Tier1 | Tier1+2 | Δ(T1+2 vs Baseline) |
|---|:--:|:--:|:--:|:--:|
| `top_hit_rate` | 0.852 | 0.852 | 0.852 | — |
| `context_precision` | 0.479 | 0.517 | 0.509 | +0.030 |
| `context_recall` | 0.630 | 0.611 | **0.667** | **+0.037** |
| `faithfulness` | 0.707 | 0.682 | 0.710 | +0.003 |
| `custom_correctness` | 0.685 | 0.685 | 0.685 | — |
| `ragas_e2e_score` | 0.625 | 0.624 | **0.643** | **+0.018** |
| `avg_latency` | 11.9s | 12.3s | 12.0s | +0.1s |
| errors | 0 | 0 | 0 | — |

输出目录：`agent/test/generated/ragas_eval_tier12_n27/`

> 注：全量 155-case 尚未重跑 T1+T2。27-case 仅覆盖 9 个 Normal_Videos。52 视频全量预期效果更显著。

---

## 4. 待办优先级

1. **跑 Part4 全量 T1+T2** — `bash run_part4_50.sh` + `AGENT_BUILD_VIDEO_COLLECTION=1`，输出到新目录
2. **Tier 3（oversample 10x + parent coarse filter）** — 如果全量 top_hit 仍低
3. **R4 Step2（ulin abstention）** — reranker 顶加校准层
4. **R6 expansion 扩大触发面**
5. **P1-Next-E entity_hint**
6. **P1-Next-G R7 hybrid alpha sweep** — 留到最后

---

## 5. 已知坑与 fragile 点

### 5.1 Reranker 配置

- `AGENT_RERANK_METADATA_IN_QUERY` **默认 OFF**
- 默认模型 `cross-encoder/ms-marco-MiniLM-L-6-v2`
- `Keywords:` 剥离逻辑在 `rerank.py:_strip_keywords()`

### 5.2 Tier 1 video collection

- 需要 `AGENT_BUILD_VIDEO_COLLECTION=1` 才会在 `--prepare-subset-db` 时构建
- video collection 名从 child collection 自动派生（如 `ucfcrime_eval_child` → `ucfcrime_eval_video`）
- discriminator LLM 使用 `build_default_llm()`（qwen3-max via DashScope）
- coarse filter 嵌入 `_run_hybrid_branch`，embedding 经 P1-3 LRU 缓存复用

### 5.3 Tier 2 scene boost

- 词表从 SQL 自动生成（`tools/scene_attrs.py`），零 LLM、零手工
- `video_scene_attrs` 表和 `scene_attrs_vocab.json` 在 `--prepare-subset-db` 时自动生成
- `AGENT_SCENE_ATTRS_VOCAB_PATH` env var 在 `_load_graph_with_runtime_env` 自动设置
- `AGENT_SCENE_BOOST_LAMBDA` 默认 0.1
- boost 在 RRF 融合后、reranker 前应用

### 5.4 种子文件命名

- 生成器输出 `Normal_Videos594_x264_events_vector_flat.json`（无下划线）
- xlsx 引用 `Normal_Videos_594_x264`（有下划线）
- `_resolve_seed_files` 已兼容两种格式

### 5.5 import 路径

`agent/node`、`agent/tools` 多用 bare `from node.x` / `from tools.x`（依赖 `agent/` 在 `sys.path`）。

### 5.6 parent 文档

10 分钟时间窗分桶，`parent_id = {video_id}_{bucket_start}s`。parent_projection 默认 OFF。

---

## 6. 关键文件地图

```
agent/
├── node/
│   ├── self_query_node.py             R6 expansion + Tier2 scene_constraints
│   ├── parallel_retrieval_fusion_node.py  Tier1 coarse_filter + Tier2 _apply_scene_boost
│   ├── summary_node.py                bail-out、existence、factual
│   └── graph_builder.py               仅 parallel fusion
├── tools/
│   ├── video_discriminator.py         Tier1: LLM per-video discriminator
│   ├── scene_attrs.py                 Tier2: SQL 提取 + IDF + 词表
│   ├── rerank.py                      R4: Keywords 剥离、metadata-in-query OFF
│   ├── hybrid_tools.py                video_filter → Chroma $in where
│   └── llm.py                         embedding LRU + 磁盘缓存
├── db/
│   ├── chroma_builder.py              Tier1: _build_video_records + parent 时间桶
│   └── config.py                      video_collection config
├── test/
│   ├── ragas_eval_runner.py            Tier1/2 build pipeline 集成
│   └── agent_test_importer.py          默认 Part4-only
├── todo.md
├── 调试记录.md
├── 全量测试分析.md                     Part4 全量分析（难度分层 + 困难 case）
└── 工作记录_20260503.md               本次会话完整工作记录
```

---

## 7. 常用命令

```bash
# Part4 全量评测（需 Tier 1 video collection）
cd /home/yangxp/Capstone/agent/test
AGENT_BUILD_VIDEO_COLLECTION=1 python ragas_eval_runner.py --limit 155 \
  --prepare-subset-db \
  --seed-dir /home/yangxp/Capstone/agent/test/generated/datasets/ucfcrime_events_vector_flat \
  --output-dir /home/yangxp/Capstone/agent/test/generated/ragas_eval_p4_tier12_full

# 灰度开关
# AGENT_BUILD_VIDEO_COLLECTION=0      # 跳过 video collection 构建
# AGENT_SCENE_BOOST_LAMBDA=0          # 关闭 scene boost
# AGENT_RERANK_METADATA_IN_QUERY=1    # 不推荐
```

---

## 8. 交接后建议

1. 跑 Part4 全量 T1+T2（上面命令），拿到 52-video 真实效果
2. 读 `agent/todo.md` 未完成区
3. 如果全量 top_hit < 0.5，做 Tier 3（oversample 10x + parent coarse）
4. 如果 recall 还不达标，做 R4 Step2（ulin abstention）
