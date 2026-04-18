# db 模块说明

## 目录职责
- 管理结构化数据库构建、路径配置、切换与测试脚本。

## 文件职责
- `config.py`：SQLite/LanceDB 路径配置读取与持久化。
- `schema.py`：SQLite 表结构与索引真源。
- `sqlite_builder.py`：建表、索引、seed 导入、初始化提示词生成。
- `manage_graph_db.py`：CLI 入口（build/switch）。
- `chorma_test_runner.py`：Chroma 检索策略测试脚本。

## 对外接口（典型）
- `python -m agent.db.manage_graph_db build ...`
- `python -m agent.db.manage_graph_db switch ...`
- `SQLiteDatabaseBuilder.build(seed_files=...)`

## 依赖关系
- `node/types.py` 通过 `config.py` 读取默认库路径。
- `test` 与运维脚本通过 `manage_graph_db.py` 执行数据库管理。

## 约定
- 字段变更优先修改 `schema.py` 与 `sqlite_builder.py` 的映射。
- 建库失败必须保留可定位日志。
