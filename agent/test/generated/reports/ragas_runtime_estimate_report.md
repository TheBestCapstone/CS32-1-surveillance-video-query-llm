# RAGAS 评估时间预估报告

## 结论摘要
- 当前基于 `smoke test` 的稳定样本，采用 `Part1 + Part4`、`top-k=3`、`RAGAS retrieval + generation + end-to-end` 全流程时，平均总耗时约为 `72.08s / case`。
- 以这个速度估算：
- 当前理论全量 `e2e_ready = 310` 条样本，预计总时长约为 `22344.8s`，约 `6 小时 12 分 25 秒`。
- 当前可直接运行样本 `200` 条，预计总时长约为 `14416s`，约 `4 小时 0 分 16 秒`。
- 默认 `top-k=5` 的当前实现存在 `RAGAS Faithfulness / FactualCorrectness` 因上下文过长触发 `max_tokens length limit` 的风险，当前不建议直接用默认配置跑全量。

## 抽样依据

### 样本 A：稳定跑通样本
- 命令：
```bash
/usr/bin/time -p python /home/yangxp/Capstone/agent/test/ragas_eval_runner.py \
  --include-sheets Part1 Part4 \
  --limit 4 \
  --top-k 3 \
  --prepare-subset-db \
  --output-dir /home/yangxp/Capstone/agent/test/generated/ragas_eval_estimate_4_top3
```
- 结果：
- `case_count = 4`
- `success_count = 4`
- 整轮墙钟时间：`real 288.32s`
- 平均总耗时：`288.32 / 4 = 72.08s / case`
- 图执行平均耗时：`avg_latency_ms = 11237.89ms`，约 `11.24s / case`
- 由此可粗略估算：
- 图执行约占 `11.24s / case`
- `RAGAS` 评分与编排额外耗时约占 `60.84s / case`

### 样本 B：默认参数风险样本
- 命令：
```bash
/usr/bin/time -p python /home/yangxp/Capstone/agent/test/ragas_eval_runner.py \
  --include-sheets Part1 Part4 \
  --limit 6 \
  --prepare-subset-db \
  --output-dir /home/yangxp/Capstone/agent/test/generated/ragas_eval_estimate_6
```
- 结果：
- 在 `RAGAS Faithfulness` 阶段失败
- 失败原因：`IncompleteOutputException` / `max_tokens length limit`
- 失败前墙钟时间：`real 473.84s`
- 结论：
- 默认 `top-k=5` 下，部分 case 的检索上下文过长，会把 `RAGAS` 的判定 prompt 推得过大
- 这会导致：
- 单 case 时间显著上升
- 多次重试
- 甚至整轮评估直接中断

## 当前数据覆盖情况
- `Part1 + Part4` 导入后：
- 总样本数：`468`
- 可用于 `e2e/generation` 的样本数：`310`
- 唯一 `video_id` 数：`106`
- 当前有标准化事件 seed 的 `video_id` 只覆盖其中一部分
- 当前可直接运行样本数：`200`
- 当前被数据缺口阻塞样本数：`110`
- 当前缺失 seed 的 `video_id` 包括：
- 一组 `Normal_Videos_594_x264` 到 `Normal_Videos_638_x264` 的条目
- 异常值如 `!?4h?!`
- `多摄像头`

## 总时长预估

### 口径 1：当前稳定配置
- 采用：
- `Part1 + Part4`
- `top-k=3`
- `RAGAS retrieval + generation + end-to-end` 全流程
- 平均耗时：`72.08s / case`

### 口径 2：当前可直接运行子集
- 可直接运行样本：`200`
- 预计总时长：
```text
200 * 72.08s = 14416s
≈ 4 小时 0 分 16 秒
```

### 口径 3：理论全量样本
- 理论全量 `e2e_ready` 样本：`310`
- 预计总时长：
```text
310 * 72.08s = 22344.8s
≈ 6 小时 12 分 25 秒
```

### 口径 4：保守估计
- 如果保留当前默认 `top-k=5`
- 或者遇到更多长上下文 case
- 则实际总时长很可能高于上面的稳定估计
- 保守建议按 `6.5 ~ 8 小时` 预留运行窗口
- 且需要接受中途因 `max_tokens` 失败而中断的风险

## RAGAS 评估方式

### Retrieval 侧
- 指标：
- `ContextPrecisionWithReference`
- `ContextRecall`
- 输入：
- `question`
- `retrieved_contexts`
- `reference_answer`
- 作用：
- 判断检索上下文是否有用
- 判断检索上下文是否覆盖参考答案

### Generation 侧
- 指标：
- `Faithfulness`
- `AnswerRelevancy`
- `FactualCorrectness`
- 输入：
- `question`
- `retrieved_contexts`
- `response`
- `reference_answer`
- 作用：
- `Faithfulness`：回答是否能被检索上下文支持
- `AnswerRelevancy`：回答是否真正回应了问题
- `FactualCorrectness`：回答和参考答案在事实层面是否一致

### End-to-End 侧
- 当前实现不是额外再跑一套独立 judge
- 而是把：
- `retrieval`
- `generation`
- 两侧的 `RAGAS` 分数聚合成 `ragas_e2e_score`
- 因此 `end-to-end` 的耗时本质上来自前两部分

## 用到的大模型与 API

### Agent 主图推理模型
- 模型：`qwen3-max`
- 调用方式：`langchain_openai.ChatOpenAI`
- API 端点：读取环境变量 `DASHSCOPE_URL`
- 当前代码口径：`DashScope` 的 OpenAI 兼容接口

### RAGAS 评估模型
- 模型：`qwen3-max`
- 调用方式：`ragas.llms.llm_factory("qwen3-max", client=AsyncOpenAI(...))`
- API 端点：
- 优先读取 `DASHSCOPE_URL`
- 其次读取 `OPENAI_BASE_URL`
- 若未配置，runner 中默认回退到：
```text
https://dashscope.aliyuncs.com/compatible-mode/v1
```

### RAGAS / Chroma 使用的 embedding 模型
- 模型：`text-embedding-v3`
- 维度：`1024`
- 调用方式：`OpenAI / AsyncOpenAI embeddings.create(...)`
- API 端点：
```text
https://dashscope.aliyuncs.com/compatible-mode/v1
```

## 风险与建议
- 风险 1：默认 `top-k=5` 会把部分 `retrieved_contexts` 拉得过长，导致 `RAGAS Faithfulness / FactualCorrectness` 超过 `max_tokens`
- 风险 2：当前 `Part1 + Part4` 中有 `110` 条样本还缺 seed 映射，现阶段无法直接纳入全量评估
- 风险 3：即使不报错，长上下文 case 也会显著拉高平均耗时

## 建议
- 先按 `top-k=3` 跑稳定版全量评估
- 先补齐缺失 seed 的 `39` 个 `video_id`
- 如果后续要恢复 `top-k=5`，建议先对传给 `RAGAS` 的上下文做裁剪或摘要压缩
