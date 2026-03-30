# Episodic Memory 数据库模块

本目录 (`src/agent/memory/episodic`) 用于存放和管理基于 LanceDB 的情景记忆（Episodic Memory）数据库。

## 目录结构

- `lancedb/`: LanceDB 数据库目录（需通过 `src/indexing/db_setup.py` 初始化并导入数据后生成）。
- `test.py`: 用于测试检索功能（语义检索和混合检索）的独立脚本。
- `skill.md`: 指导 Agent 如何将此数据库封装为工具供系统调用的规范说明。

## 数据库架构

采用 LanceDB 存储，包含单张表：
1. **`episodic_events`**: 存储所有的结构化字段（如视频ID、起止时间、对象类别、文本摘要、边界框坐标等），以及 1024 维的 Embedding 向量，支持快速的向量搜索和结构化过滤。

## 使用说明

### 1. 依赖安装
确保在虚拟环境中安装了以下依赖：
```bash
pip install lancedb pandas pyarrow openai python-dotenv
```

### 2. 环境变量
需要在项目根目录的 `.env` 文件中配置百炼的 API Key，用于调用 Qwen-Embedding 模型：
```env
DASHSCOPE_API_KEY="sk-xxxxxxxxxxxxx"
```

### 3. 测试检索
直接在此目录下运行测试脚本：
```bash
python test.py
```