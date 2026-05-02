# Agent 交接文档（Session Handoff）

> 生成时间：2026-05-03  
> 适用范围：下一个 agent / 工程师接手  
> 配套文档：`agent/todo.md`（任务与优先级）、`agent/调试记录.md`（全 session 复盘）

---

## 1. 一句话总览

主线已推进到 **P1-Next-G R4 Step1 fix + R6 query expansion**。评测集从 Part1 切换到 **Part4（Normal_Videos）**，IoU 口径修复。当前 **Part4 15-case** 上 `context_precision=0.697`、`context_recall=0.70`、`ragas_e2e=0.69`。

---

## 2. 本轮已落地工作

| 主题 | 要点 |
|------|------|
| **导入切换** | `DEFAULT_INCLUDE_SHEETS = ["Part4"]`；104 个 Normal_Videos 种子已补全 |
| **P1-Next-G R4** | `Keywords:` 剥离、reranker A/B 结论（ms-marco > bge-v2-m3）、**Step1 fix**：禁用 `AGENT_RERANK_METADATA_IN_QUERY`（默认 OFF），消除跨视频噪声。precision 0.673→0.697 |
| **P1-Next-G R6** | self_query_node 扩展 `expansion_terms`，LLM 对抽象 query 生成具体替代词。recall +0.04 |
| **IoU 修复** | 切 Part4 后 14/15 eligible（IoU 0.594）；修 expected_answer_label=="no" 时不应算 IoU 的 bug |
| **种子兼容** | `_resolve_seed_files` 兼容 `Normal_Videos594` 和 `Normal_Videos_594` 双命名 |

---

## 3. 评测数字（Part4 15-case，Step1 fix 后）

| Metric | Value | 备注 |
|---|:--:|---|
| `top_hit_rate` | 0.867 | Part4 比 Part1 难（Normal_Videos 语义更细） |
| `context_precision_avg` | **0.697** | R4 Step1 fix 后 +0.024 |
| `context_recall_avg` | **0.700** | R6 expansion +0.04 |
| `faithfulness_avg` | 0.600 | RAGAS 噪声范围内 |
| `factual_correctness_avg` | 0.767 | Part4 rich reference 全面覆盖 |
| `custom_correctness_avg` | 0.763 | 规则型指标 |
| `time_range_overlap_iou_avg` | 0.594 | 14/15 eligible ✅ |
| `video_match_score_avg` | 0.714 | Part4 瓶颈 |
| `ragas_e2e_score_avg` | 0.690 | custom_correctness 替代 factual |
| scoring error cases | 0 | 稳定 |

输出目录：`agent/test/generated/ragas_eval_e2e_n15_p4_step1_v1/`

---

## 4. 待办优先级

1. **跑 Part4 全量** — `bash run_part4_50.sh`，输出到 `agent/test/generated/ragas_eval_e2e_p4_full/`
2. **R4 Step2（ulin abstention）** — reranker 顶加校准层，兜底 negative query（详见 `todo.md` R4）
3. **R6 expansion 扩大触发面** — 目前仅 3-5/27 case 触发，可降低门槛
4. **P1-Next-E entity_hint** — 长期方向，UCFCrime 数据侧
5. **P1-Next-G R7 hybrid alpha sweep** — 独立项，留到最后

---

## 5. 已知坑与 fragile 点

### 5.1 Reranker 配置

- `AGENT_RERANK_METADATA_IN_QUERY` **默认 OFF**。不要改回 ON——会导致跨视频噪声（已 A/B 验证）
- 默认模型 `cross-encoder/ms-marco-MiniLM-L-6-v2`，bge-v2-m3 在我们的数据上更差
- `Keywords:` 剥离逻辑在 `rerank.py:_strip_keywords()`

### 5.2 种子文件命名

- 生成器输出 `Normal_Videos594_x264_events_vector_flat.json`（无下划线）
- xlsx 引用 `Normal_Videos_594_x264`（有下划线）
- `_resolve_seed_files` 已兼容两种格式

### 5.3 import 路径

`agent/node`、`agent/tools` 多用 bare `from node.x` / `from tools.x`（依赖 `agent/` 在 `sys.path`）。新测试请照现有文件写法。

### 5.4 DashScope / OpenAI 别名（`agent/core/runtime.py`）

必须 `OPENAI_API_KEY` 与 `OPENAI_BASE_URL` **成对缺失**才别名到 DashScope，否则真 OpenAI key 打到 DashScope → 401。

---

## 6. 关键文件地图

```
agent/
├── node/
│   ├── self_query_node.py          R6 expansion_terms；expansion 拼到 rewritten_query
│   ├── summary_node.py             bail-out、existence、factual
│   │   match_verifier_node.py       v2.3 多候选 span 重选
│   └── graph_builder.py            仅 parallel fusion；可选关 verifier
├── tools/
│   ├── rerank.py                   R4：Keywords: 剥离、metadata-in-query OFF、_enrich_query_with_metadata
│   └── llm.py                      embedding LRU + 磁盘缓存
├── test/
│   ├── ragas_eval_runner.py          RAGAS 入口；_resolve_seed_files 双命名兼容
│   ├── agent_test_importer.py        默认 Part4-only
│   ├── ucfcrime_transcript_importer.py  种子生成
│   └── eval_report_tables.py         REPORT_TABLES.md
├── lightingRL/
│   └── prompt_registry.py           self_query system prompt（含 expansion 指令）
├── todo.md
├── 调试记录.md
└── ../run_part4_50.sh               Part4 50-case 一键脚本
```

---

## 7. 常用命令

```bash
# Part4 全量评测（156 case）
bash /home/yangxp/Capstone/run_part4_50.sh
# 输出：agent/test/generated/ragas_eval_e2e_p4_full/

# 单测
cd /home/yangxp/Capstone
python -m pytest agent/test/test_*.py -v

# 灰度开关
# AGENT_RERANK_METADATA_IN_QUERY=1   # 回滚到旧行为（不推荐）
# AGENT_DISABLE_VERIFIER_NODE=1      # 关 verifier
# AGENT_ENABLE_EXISTENCE_GROUNDER=1  # 开 grounder
```

---

## 8. 交接后建议

1. 先跑 `bash run_part4_50.sh`，拿到 Part4 全量基线
2. 读 `agent/test/generated/ragas_eval_e2e_p4_full/REPORT_TABLES.md` 和 `summary_report.json`
3. 再读 `agent/todo.md` 未完成区，决定下一步优先级
