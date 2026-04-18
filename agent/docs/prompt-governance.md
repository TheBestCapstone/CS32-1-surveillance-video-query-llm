# Prompt 模板与版本化治理

## 目标
- 统一当前分散在不同节点和 sub-agent 中的 prompt 资产。
- 建立最小版本治理规则，减少“提示词改了但没人知道”的情况。
- 不改变现有运行逻辑，只建立治理口径。

## 当前 prompt 资产分布

### 1. 系统初始化
- 文件：`agent/init/agent_init_prompt.md`
- 作用：提供全局背景与运行先验
- 当前状态：已接入主图构建逻辑

### 2. 路由与结构化输出
- 文件：`agent/node/router_prompts.py`
- 包含：
  - quadruple 提取 prompt
  - route decision prompt
  - 结构化 JSON schema

### 3. Query rewrite
- 文件：`agent/node/self_query_node.py`
- 特点：
  - prompt 与逻辑写在同一文件中
  - fast path 与 LLM path 共存

### 4. Query classification
- 文件：`agent/agents/shared/query_classifier.py`
- 特点：
  - prompt 直接内联在函数中
  - 同时带少量 fast-path 逻辑

### 5. Final summary
- 文件：`agent/node/summary_node.py`
- 特点：
  - prompt 直接内联
  - 用户可见输出质量高度依赖该 prompt

### 6. SQL / Hybrid sub-agent
- 文件：
  - `agent/agents/pure_sql/sub_agent.py`
  - `agent/agents/hybrid_search/sub_agent.py`
- 特点：
  - prompt 与 agent 执行器耦合
  - 多工具调用上下文嵌在代码逻辑中

## 当前主要问题
- prompt 分散，缺统一清单
- 没有统一的 `prompt_id`
- 没有版本号
- 变更无法快速定位影响范围
- 测试报告里无法直接标记用了哪一版 prompt

## 最小治理模型

### 1. 每个 prompt 都应有唯一标识
建议命名规则：
- `init.global_context`
- `router.quadruple_extract`
- `router.route_decision`
- `rewrite.self_query`
- `classification.query_label`
- `summary.final_answer`
- `subagent.pure_sql.react`
- `subagent.hybrid.react`

### 2. 每个 prompt 都应有版本号
建议格式：
- `v1`
- `v1.1`
- `v2`

### 3. 每个 prompt 都应有 owner 和影响面
最少记录：
- `prompt_id`
- `version`
- `source_file`
- `owner_module`
- `user_visible`
- `downstream_dependencies`

## 版本化原则

### Major 版本升级
适用于：
- 改变任务目标
- 改变输出 schema
- 改变用户可见回答风格
- 改变工具选择策略

### Minor 版本升级
适用于：
- 增加示例
- 优化措辞
- 收紧格式要求
- 不改变 schema 和主要行为

### Patch 级更新
适用于：
- 文案纠错
- 小的语气修正
- 注释补充

## 变更准入规则

### 必须记录的变更
- 修改了用户可见回答质量
- 修改了结构化输出 schema
- 修改了 route / classification 决策提示
- 修改了 sub-agent 的工具使用约束

### 可以不单独升版的变更
- 纯注释
- 与运行逻辑无关的空白格式调整

## 建议的 prompt registry

### 当前建议文件
- `agent/docs/prompt-registry.json`

### registry 最小字段
| 字段 | 含义 |
|---|---|
| `prompt_id` | 唯一标识 |
| `version` | 当前版本 |
| `source_file` | 真源文件 |
| `entry_symbol` | 入口函数或常量 |
| `category` | init / rewrite / routing / classification / summary / subagent |
| `user_visible` | 是否直接影响用户看到的文本 |
| `notes` | 当前治理说明 |

## 测试与观测要求
- 后续测试报告建议增加：
  - `prompt_versions`
  - 至少记录 `rewrite/classification/summary` 三类 prompt 的版本
- 当回答质量回退时，优先检查：
  - prompt 版本是否变化
  - 是否引入新的 schema 要求
  - 是否修改了 few-shot 或输出风格

## 当前建议落地顺序

### 第一阶段
- 建 registry
- 给关键 prompt 分配 `prompt_id`
- 为用户可见 prompt 标版本

### 第二阶段
- 把 prompt 版本接进测试报告
- 对关键 prompt 变更补回归样例

### 第三阶段
- 再考虑把 prompt 从代码内联抽到集中模板层

## 当前治理结论
- 现在不建议立刻做“prompt 全量抽离重构”
- 先做“清单化 + 版本化 + 可追踪”
- 尤其应优先治理：
  - `self_query`
  - `query_classifier`
  - `summary`

## 一句话规则
- prompt 现在可以继续分布在原文件里，但必须先做到“看得见、数得清、变更可追踪”。
