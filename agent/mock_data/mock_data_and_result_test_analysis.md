# Mock Data & Result 测试分析与优化方案

## 1. mock_data 现状梳理

## 1.1 文件清单与职责

- `mock_data/data/video_events_mock.json`
  - mock 数据主文件，结构为 `[{video_id, events:[...]}]`。
- `mock_data/data/generate_mock_data.py`
  - 随机增量生成器；读取旧 JSON 并追加新视频与事件。
- `mock_data/data/mock_server.py`
  - FastAPI 服务，提供 `/api/v1/video/events` 查询接口。
- `mock_data/data/openapi.yaml`
  - API 结构定义，供 Apifox 导入与 Mock。
- `mock_data/data/test.py`
  - 通过 HTTP 访问 mock_server 的联调脚本。

## 1.2 数据结构定义方式

- 顶层：视频列表。
- 事件字段核心：
  - `video_id/start_time/end_time/object_type/object_color_cn/scene_zone_cn/event_text_cn`
  - bbox、关键词、entity_hint 等辅助字段。
- 生成器中对象类型与颜色为固定枚举；场景区域为固定中文枚举。

## 1.3 初始化/生成流程

1. 读取 `video_events_mock.json`（不存在或异常则空列表）。
2. 随机生成若干 `video_id` 与每视频事件序列。
3. 与旧数据合并后写回同文件。
4. `mock_server.py` 运行时按 `video_id` 返回单视频事件集。

## 1.4 风险点

- 随机生成无 seed，结果不可复现，影响回归稳定性。
- 生成器为“追加式”，长期运行可能造成数据分布漂移。
- API 层与检索层字段并不完全同构（SQLite 中无 `scene_zone_cn`），会造成测试误判。

## 2. 旧 result 测试问题

- 用例硬编码在脚本中，维护成本高。
- 断言弱：主要记录输出，缺少结构化 PASS/FAIL 判定。
- 覆盖弱：缺少 route 正确性、字段完整性、最小命中数等断言。
- 报告弱：仅 Markdown 文本，不产出机器可读报告。
- 与 mock_data 协调不足：未展示 mock 数据分布特征，难以解释失败原因。

## 3. 已实施优化

## 3.1 数据驱动测试

- 新增 `agent/test/result_cases.json`
  - 每个用例配置：
    - `question`
    - `expected_answer`
    - `expected_routes`
    - `min_results`
    - `required_top_fields`

## 3.2 统一测试运行器

- 新增 `agent/test/result_test_runner.py`
  - 自动加载 case 配置
  - 执行整图测试
  - 断言：
    - 无运行时异常
    - 路由命中预期
    - 无 `tool_error`
    - 最小结果数
    - Top 结果关键字段完整性
  - 输出：
    - `result.md`（可读报告）
    - `result_report.json`（机器可读）
  - 附带 mock 数据画像（对象类型/颜色/场景样本）

## 3.3 SQL 字段兼容修复

- 在 `pure_sql_node` 中新增字段合法性过滤：
  - 自动读取表字段（PRAGMA）
  - 跳过不存在列的 where 条件并记录 `skipped_filters`
  - 防止 `no such column` 异常导致误失败

## 3.4 测试框架增强

- 新增 `agent/test/test_result_runner.py`
  - 使用 fake graph 验证数据驱动 runner 与报告输出逻辑。

## 4. 持续改进建议

- 为 `generate_mock_data.py` 增加 `--seed`，固定回归数据。
- 增加 mock schema 合规校验脚本（字段、类型、取值域）。
- 在 `result_report.json` 增加趋势指标：
  - pass_rate、route 分布、p95、tool_error 分类占比。
