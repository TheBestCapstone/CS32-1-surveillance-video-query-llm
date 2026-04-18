# 文档总索引

## 目的
- 统一汇总当前 `agent/docs` 下的审计、治理、数据字典与运行约束文档。
- 提供推荐阅读顺序，方便后续开发、测试、审计与交接。
- 将文档与 `todo` 编号建立映射，减少查找成本。

## 当前状态
- 混合 RAG 架构审计已完成
- 审计后 `P0 / P1 / P2` 治理项已完成首轮收口
- 默认主图已统一为：
  - `self_query -> query_classification -> parallel_retrieval_fusion -> final_answer -> summary`

## 推荐阅读顺序

### 1. 先看全局判断
- [rag-audit.md](file:///home/yangxp/Capstone/agent/docs/rag-audit.md)
- 适合场景：
  - 快速了解当前混合 RAG 完整性现状
  - 看 P0/P1/P2 问题分级
  - 看需要拍板的架构决策

### 2. 再看字段与数据口径
- [data-dictionary.md](file:///home/yangxp/Capstone/agent/docs/data-dictionary.md)
- 适合场景：
  - 查 SQLite 真表字段含义
  - 查 Chroma / Hybrid 输出字段
  - 查运行态统一检索契约
  - 避免 `event_id`、`scene_zone_en`、`object_color_en` 等字段误用

### 3. 再看 query 前处理边界
- [query-rewrite-boundaries.md](file:///home/yangxp/Capstone/agent/docs/query-rewrite-boundaries.md)
- 适合场景：
  - 修改 `self_query_node`
  - 评估 rewrite 是否改坏用户意图
  - 判断 `HyDE / multi-query / decomposition` 是否允许接入

### 4. 再看 prompt 治理
- [prompt-governance.md](file:///home/yangxp/Capstone/agent/docs/prompt-governance.md)
- [prompt-registry.json](file:///home/yangxp/Capstone/agent/docs/prompt-registry.json)
- 适合场景：
  - 盘点当前 prompt 资产
  - 查 `prompt_id / version`
  - 评估某次 prompt 变更是否需要升版

### 5. 最后看 streaming 与预算
- [streaming-token-budget.md](file:///home/yangxp/Capstone/agent/docs/streaming-token-budget.md)
- 适合场景：
  - 评估用户级 streaming
  - 评估 token budget / candidate budget
  - 规划未来 multi-query 或更强 rewrite 能力

## 文档与 todo 对应关系
| todo | 状态 | 文档 |
|---|---|---|
| `13` 混合 RAG 架构完整性审计 | `DONE` | [rag-audit.md](file:///home/yangxp/Capstone/agent/docs/rag-audit.md) |
| `19` 数据字典与字段语义文档 | `DONE` | [data-dictionary.md](file:///home/yangxp/Capstone/agent/docs/data-dictionary.md) |
| `20` Query rewrite 增强边界梳理 | `DONE` | [query-rewrite-boundaries.md](file:///home/yangxp/Capstone/agent/docs/query-rewrite-boundaries.md) |
| `21` Prompt 模板与版本化治理 | `DONE` | [prompt-governance.md](file:///home/yangxp/Capstone/agent/docs/prompt-governance.md)、[prompt-registry.json](file:///home/yangxp/Capstone/agent/docs/prompt-registry.json) |
| `22` 流式输出与上下文预算治理 | `DONE` | [streaming-token-budget.md](file:///home/yangxp/Capstone/agent/docs/streaming-token-budget.md) |

## 按角色查阅

### 开发者
- 先看：
  - [data-dictionary.md](file:///home/yangxp/Capstone/agent/docs/data-dictionary.md)
  - [query-rewrite-boundaries.md](file:///home/yangxp/Capstone/agent/docs/query-rewrite-boundaries.md)
  - [prompt-governance.md](file:///home/yangxp/Capstone/agent/docs/prompt-governance.md)

### 测试 / 审计
- 先看：
  - [rag-audit.md](file:///home/yangxp/Capstone/agent/docs/rag-audit.md)
  - [data-dictionary.md](file:///home/yangxp/Capstone/agent/docs/data-dictionary.md)
  - [streaming-token-budget.md](file:///home/yangxp/Capstone/agent/docs/streaming-token-budget.md)

### Prompt 调优
- 先看：
  - [prompt-governance.md](file:///home/yangxp/Capstone/agent/docs/prompt-governance.md)
  - [prompt-registry.json](file:///home/yangxp/Capstone/agent/docs/prompt-registry.json)
  - [query-rewrite-boundaries.md](file:///home/yangxp/Capstone/agent/docs/query-rewrite-boundaries.md)

## 当前建议的使用方式
- 遇到字段歧义，先查 `data-dictionary`
- 想改 rewrite，先查 `query-rewrite-boundaries`
- 想改 prompt，先查 `prompt-governance` 和 `prompt-registry`
- 想做 streaming / multi-query / 扩写增强，先查 `streaming-token-budget`
- 想判断全局风险和后续优先级，先查 `rag-audit`

## 一句话总结
- `agent/docs` 现在已经形成一套围绕混合 RAG 的“审计 -> 契约 -> 边界 -> prompt -> 预算”的完整文档链，可以作为当前系统的治理入口。
