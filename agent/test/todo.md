# agent/test 今日任务维护

## 当前目标

- 用 `RAGAS` 搭建 `retrieval`、`generation`、`end-to-end` 三类评估流程。
- 当前 `xlsx` 评测标签只纳入 `Part1` 和 `Part4`。
- 评估流程需要能复用 `UCFCrime` 标准化事件数据，并支持最小样本快速验证。

## 阶段计划

### 阶段 1：评测数据收口

- 工作目标：
- 将 `agent_test.xlsx` 的输入范围收敛到 `Part1` 和 `Part4`。
- 为评测流程准备统一 case 视图。
- 交付内容：
- 可按 sheet 过滤的导入配置
- `Part1/Part4` 专用评测样本视图
- 当前状态：已完成
- 已交付：
- `agent_test_importer.py` 已支持 `--include-sheets`
- `Part1/Part4` 过滤后数据规模：`468` 条 case，其中 `310` 条可用于 `e2e/generation`

### 阶段 2：评估执行器

- 工作目标：
- 搭建统一 `RAGAS eval runner`
- 同时输出 `retrieval`、`generation`、`end-to-end` 的逐样本结果与汇总结果
- 交付内容：
- 可执行评估脚本
- JSON 报告
- Markdown 报告
- 当前状态：已完成
- 已交付：
- 新增 `agent/test/ragas_eval_runner.py`
- 可输出 `retrieval_report.json`
- 可输出 `generation_report.json`
- 可输出 `e2e_report.json`
- 可输出 `summary_report.json`
- 可输出 `summary_report.md`

### 阶段 3：测试库准备

- 工作目标：
- 支持按选中 case 的 `video_id` 自动构建最小 `SQLite/Chroma` 子集库
- 让简单测试可以快速跑通
- 交付内容：
- 子集 seed 选择逻辑
- 子集数据库构建逻辑
- 当前状态：已完成
- 已交付：
- 支持按选中 case 的 `video_id` 自动收集 `events_vector_flat` seed
- 支持自动构建子集 `SQLite`
- 支持自动构建父子 `Chroma`

### 阶段 4：最小验证

- 工作目标：
- 跑一个简单的 `RAGAS` 评测样本验证流程
- 校验 `retrieval`、`generation`、`end-to-end` 三类结果都能落盘
- 交付内容：
- 最小测试结果
- `work.md` 阶段记录更新
- 当前状态：已完成
- 已交付：
- 已执行 `--limit 2 --prepare-subset-db` 的 smoke test
- 三类评估结果已成功落盘到 `agent/test/generated/ragas_eval_smoke/`