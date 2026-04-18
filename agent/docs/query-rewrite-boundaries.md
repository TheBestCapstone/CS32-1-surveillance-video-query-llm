# Query Rewrite 增强边界梳理

## 目的
- 约束 `self_query_node` 的改写行为，避免“帮用户改意图”。
- 在保持 `保守 rewrite` 的前提下，明确哪些增强允许做，哪些不允许做。
- 为后续测试、审计和回归提供统一判断标准。

## 适用范围
- 默认主图中的 `self_query_node`
- 反思重试中的 `optimized_query`
- 与检索前 query 规范化相关的轻量增强逻辑

## 当前实现口径
- 真源文件：
  - `agent/node/self_query_node.py`
  - `agent/node/types.py`
- 当前行为：
  - 先做轻量规范化：空白折叠、首尾噪声清理
  - 对清晰短 query 走 `fast path`
  - 仅在复杂或模糊 query 时走 `LLM + structured output`
  - 强调“不要 broaden scope、不要替换关键领域词”

## 核心原则

### P1. 保持原意优先
- 改写后的 query 必须保持用户原意。
- 不允许把“过滤型请求”改写成“开放语义探索型请求”。
- 不允许把“存在性查询”改写成“描述性摘要查询”。

### P2. 约束显式保留
- 明确出现的对象、颜色、地点、动作词要尽量保留原词。
- 若必须标准化，只允许做“同义标准化”，不允许做“语义扩写”。

### P3. 默认做规范化，不默认做扩写
- 默认允许：
  - 空白折叠
  - 标点噪声清理
  - 大小写归一
  - 明显等价表述标准化
- 默认不允许：
  - 添加未提及的属性
  - 自动补时间范围
  - 自动补地点层级
  - 自动补对象类别

## 允许做的增强

### A. 可直接启用
- 空白、大小写、标点规范化
- `parking area -> parking` 这类字段标准化
- `dark-clothed persons -> dark persons` 这类不改变语义核心的轻量规整
- 将明显口语句式收紧为检索友好的简洁表达

### B. 允许做，但必须受限
- 已知枚举值标准化
  - 前提：字段值在数据字典或 enum 校准结果中可验证
- 轻量歧义标注
  - 可以在 `ambiguities` 字段里写出，不应擅自替用户决定
- 用户需求摘要
  - 可以写到 `user_need`，但不能覆盖原 query

## 不允许做的增强

### A. 不允许的扩写
- 自动添加用户未说过的颜色、动作、地点
- 自动把“person”扩成“player/referee/fan”
- 自动引入时间条件，如 `first half`、`10 seconds later`
- 自动引入因果或先后关系

### B. 不允许的改意图
- `Show me a person in the parking area`
  - 不允许改成偏语义关系检索
- `Did you see any person in the database?`
  - 不允许改成“总结数据库里有哪些人”
- `Are there any cars in the database?`
  - 不允许改成“找相似车辆运动片段”

### C. 不允许的策略性补全
- 不允许默认启用 `HyDE`
- 不允许默认启用 `multi-query`
- 不允许默认启用 query decomposition
- 这些能力若未来接入，必须作为显式可控特性，而不是 rewrite 默认行为

## 按意图类型的 rewrite 约束

### Structured
- 目标：尽量保留过滤条件
- 允许：
  - 保留 object/color/zone 词
  - 轻量清洗和标准化
- 不允许：
  - 改成描述型语义 query
  - 删除结构化约束

### Semantic
- 目标：保留语义关系核心
- 允许：
  - 保留 `near / around / similar / moving / after / before`
  - 轻量语法规整
- 不允许：
  - 擅自去掉关系词
  - 把复杂语义压平为纯属性过滤

### Mixed
- 目标：同时保留结构化约束和语义核心
- 允许：
  - 重排词序
  - 压缩冗余表达
- 不允许：
  - 只保留其中一半意图

## 输出字段约束

### `rewritten_query`
- 必须短于原 query 的 `1.5x`
- 若原 query 已清晰，优先与原文接近
- 不得包含未在原 query 中出现的强约束词

### `user_need`
- 允许总结用户真实需求
- 不得与原 query 冲突

### `intent_label / retrieval_focus`
- 必须与 rewrite 一致
- 若无法确定，优先保守给 `mixed`

### `ambiguities`
- 可列出“需要用户进一步澄清”的点
- 不得在这里偷改用户需求

## 未来增强的准入规则

### `HyDE`
- 当前状态：禁止默认启用
- 准入条件：
  - 有独立 feature flag
  - 有 A/B 测试或评测集验证
  - 可观测性可区分是否使用 HyDE

### `multi-query`
- 当前状态：禁止默认启用
- 准入条件：
  - 有 token budget 保护
  - 有 query fan-out 上限
  - 有召回收益证据

### `query decomposition`
- 当前状态：禁止默认启用
- 准入条件：
  - 明确只针对复合问题
  - 子 query 与原 query 之间可追溯
  - 有独立 trace 字段

## 测试建议
- 对 rewrite 做回归时，至少验证：
  - 原始 query
  - `rewritten_query`
  - `intent_label`
  - `retrieval_focus`
  - 最终 route / 检索结果是否发生意外偏移

### 必测样例
- `Did you see any person in the database?`
- `Show me dark persons.`
- `Show me a person in the parking area.`
- `Find a person near the left bleachers.`
- `Look for a person moving on the sidewalk.`

## 一句话规则
- `self_query_node` 的目标不是“帮用户想得更聪明”，而是“在不改意图的前提下，让检索更稳定”。
