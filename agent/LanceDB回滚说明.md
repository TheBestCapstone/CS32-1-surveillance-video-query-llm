# LanceDB 回滚说明（仅用于应急）

## 当前状态
- 主链路已切换到 Chroma（`hybrid_tools -> ChromaGateway`）。
- LanceDB 相关代码保留为“可回滚资产”，默认不再维护。

## 涉及文件（LanceDB 相关）
- [db_access.py](file:///home/yangxp/Capstone/agent/tools/db_access.py)
  - `LanceDBGateway`
  - `ChromaGateway`（当前在用）
- [py2sql.py](file:///home/yangxp/Capstone/agent/tools/py2sql.py)
  - LanceDB 检索实现（`SQLVideoSearchTool`）
- [hybrid_tools.py](file:///home/yangxp/Capstone/agent/tools/hybrid_tools.py)
  - 当前使用 Chroma；回滚时需改回 LanceDB 调用
- [config.py](file:///home/yangxp/Capstone/agent/db/config.py)
  - `AGENT_LANCEDB_PATH` 与 `AGENT_CHROMA_*` 配置共存
- [manage_graph_db.py](file:///home/yangxp/Capstone/agent/db/manage_graph_db.py)
  - `switch` 支持设置 `lancedb/chroma`
- [types.py](file:///home/yangxp/Capstone/agent/node/types.py)
  - `default_db_path()`（LanceDB）
  - `default_chroma_path()/default_chroma_collection()`

## 回滚触发条件
- Chroma 存储不可用、检索延迟异常、或线上策略要求恢复旧链路。

## 一键配置回滚（仅配置层）
```bash
python -m agent.db.manage_graph_db switch \
  --lancedb-path /home/yangxp/Capstone/data/lancedb
```

## 代码层回滚步骤（必要时）
1. 在 [hybrid_tools.py](file:///home/yangxp/Capstone/agent/tools/hybrid_tools.py) 中：
- `ChromaGateway` 改回 `LanceDBGateway`
- `gateway.search(...)` 改回旧的 LanceDB 检索调用参数

2. 保持 [db_access.py](file:///home/yangxp/Capstone/agent/tools/db_access.py) 中 `LanceDBGateway` 可用：
- `SQLVideoSearchTool` 依赖可导入
- `lancedb` 依赖已安装

3. 环境变量建议：
- 保留 `AGENT_LANCEDB_PATH`
- 可暂时忽略 `AGENT_CHROMA_PATH`、`AGENT_CHROMA_COLLECTION`

## 回滚后验收
1. 冒烟：`TC01` 必须通过（主链路不受影响）
2. 混合链路：执行 `TC04`，要求“可运行无异常”（结果可为 0）
3. 工具直调：`dynamic_weighted_vector_search` 返回字符串且不抛异常

## 备注
- 当前项目策略：默认走 Chroma，LanceDB 仅保留应急回滚路径。
- 后续需求无明确回滚诉求时，不再迭代 LanceDB 功能。
