# RAGAS GPT-4o 优化与时间测试报告

## 目标
- 将 `RAGAS` 评估模型切换为 `GPT-4o`
- 使用环境变量 `OPENAI_API_KEY`
- 评估并发加速与上下文裁剪后的时间表现
- 给出全量评估的时间预估与优化建议

## 当前生效配置

### RAGAS 模型与 API
- `RAGAS LLM`：
- 模型：`gpt-4o`
- API：`OpenAI API`
- 端点：`https://api.openai.com/v1`
- 鉴权：`OPENAI_API_KEY`

### RAGAS embedding
- 模型：`text-embedding-3-small`
- API：`OpenAI API`
- 端点：`https://api.openai.com/v1`
- 鉴权：`OPENAI_API_KEY`

### Agent 主图模型
- 模型：`qwen3-max`
- API：`DashScope` OpenAI-compatible API
- 说明：
- 当前优化只替换了 `RAGAS` 评估侧模型
- Agent 主图推理模型未改动

## 已实现的优化

### 并行加速
- 新增 `--ragas-concurrency`
- 当前已验证：
- `concurrency=1`
- `concurrency=3`
- 并行范围：
- `RAGAS` 按 case 并发打分
- 图执行阶段仍保持顺序执行

### 上下文压缩
- 新增：
- `--ragas-max-contexts`
- `--ragas-max-context-chars`
- `--ragas-max-total-context-chars`
- `--ragas-max-response-chars`
- `--ragas-max-reference-chars`
- 当前测试配置：
- `max_contexts = 3`
- `max_context_chars = 700`
- `max_total_context_chars = 1800`
- `max_response_chars = 900`
- `max_reference_chars = 700`

### 指标轻量化
- `AnswerRelevancy`：
- `strictness = 2`
- `FactualCorrectness`：
- 当前使用 `precision` 口径
- 目标：
- 降低 token 消耗
- 缩短单 case 打分时间

### 稳定性优化
- metric 级异常单独记录
- 不让单个 metric 失败直接中断整轮评估
- 运行报告中保留 `metric_errors`

## 时间测试

### 测试口径
- 数据范围：`Part1 + Part4`
- 样本数：`4`
- `top_k = 3`
- 自动构建子集：
- `SQLite`
- 父子 `Chroma`
- 输出目录：
- `agent/test/generated/ragas_eval_gpt4o_c1/`
- `agent/test/generated/ragas_eval_gpt4o_c3/`

### 测试 A：并发度 1
- 命令：
```bash
/usr/bin/time -p python /home/yangxp/Capstone/agent/test/ragas_eval_runner.py \
  --include-sheets Part1 Part4 \
  --limit 4 \
  --top-k 3 \
  --prepare-subset-db \
  --ragas-model gpt-4o \
  --ragas-concurrency 1 \
  --ragas-max-contexts 3 \
  --ragas-max-context-chars 700 \
  --ragas-max-total-context-chars 1800 \
  --ragas-max-response-chars 900 \
  --ragas-max-reference-chars 700 \
  --answer-relevancy-strictness 2 \
  --output-dir /home/yangxp/Capstone/agent/test/generated/ragas_eval_gpt4o_c1
```
- 结果：
- `real = 90.30s`
- `graph_total_ms = 44093.0`
- `ragas_total_ms = 40018.14`
- `wall_total_ms = 85293.56`
- 平均外部墙钟耗时：`22.575s / case`
- 平均内部总耗时：`21.3234s / case`

### 测试 B：并发度 3
- 命令：
```bash
/usr/bin/time -p python /home/yangxp/Capstone/agent/test/ragas_eval_runner.py \
  --include-sheets Part1 Part4 \
  --limit 4 \
  --top-k 3 \
  --prepare-subset-db \
  --ragas-model gpt-4o \
  --ragas-concurrency 3 \
  --ragas-max-contexts 3 \
  --ragas-max-context-chars 700 \
  --ragas-max-total-context-chars 1800 \
  --ragas-max-response-chars 900 \
  --ragas-max-reference-chars 700 \
  --answer-relevancy-strictness 2 \
  --output-dir /home/yangxp/Capstone/agent/test/generated/ragas_eval_gpt4o_c3
```
- 结果：
- `real = 69.50s`
- `graph_total_ms = 42833.87`
- `ragas_total_ms = 20070.93`
- `wall_total_ms = 64074.6`
- 平均外部墙钟耗时：`17.375s / case`
- 平均内部总耗时：`16.0187s / case`

## 加速收益
- 总墙钟时间：
- `90.30s -> 69.50s`
- 总体加速：`23.03%`
- `RAGAS` 打分阶段：
- `40.02s -> 20.07s`
- `RAGAS` 侧加速：`49.85%`
- 图执行阶段耗时变化不大：
- 说明当前主要瓶颈已经从 `RAGAS` 的串行打分转为
- `graph` 执行
- `graph + ragas` 共同耗时

## 时间预估

### 当前可直接运行子集
- 可直接运行样本数：`200`
- 采用优化后配置 `concurrency=3`
- 预计总时长：
```text
200 * 17.375s = 3475s
≈ 57 分 55 秒
```

### 理论全量样本
- 理论全量 `e2e_ready` 样本数：`310`
- 采用优化后配置 `concurrency=3`
- 预计总时长：
```text
310 * 17.375s = 5386.25s
≈ 1 小时 29 分 46 秒
```

### 对照：未并行版本
- `concurrency=1`
- `200` 条样本约 `1 小时 15 分 15 秒`
- `310` 条样本约 `1 小时 56 分 38 秒`

## 当前结论
- `GPT-4o + OpenAI API` 的 `RAGAS` 评估链路已跑通
- `RAGAS` 指标现在可正常返回，不再是空值
- 并行加速有效，当前推荐配置是：
- `ragas_concurrency = 3`
- `top_k = 3`
- 上下文裁剪保持当前口径

## 后续优化建议
- 优化 1：
- 全量评估时不要反复构建子集库，改为复用预构建的全量 `SQLite/Chroma`
- 这样可以减少非评测本身的额外耗时

- 优化 2：
- 增加 `RAGAS` 磁盘缓存
- 对重复 case 或重复 context 的实验复跑会明显加速

- 优化 3：
- 为 `Part1` 和 `Part4` 提前生成固定 `retrieved_contexts snapshot`
- 在只关心生成测时可跳过图执行阶段

- 优化 4：
- 继续尝试 `ragas_concurrency = 4`
- 但需要观察 `OpenAI rate limit` 和失败率

- 优化 5：
- 如果只做趋势对比，可增加 `fast profile`
- 例如：
- 更短上下文
- 更低 `strictness`
- 只跑部分指标
