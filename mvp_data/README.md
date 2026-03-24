# 视频事件数据 API Mock 与 Apifox 使用指南

本文档详细说明了如何在 Apifox 中导入并使用提供的视频事件 JSON 数据进行 API Mock，以及如何在 `capstone` 虚拟环境中运行本地 Python Mock 服务器（可选）。

## 目录结构
在 `~/capstone/Capstone/agent/memory` 目录下包含以下文件：
- `video_events_mock.json`: 原始提供的 Mock 数据。
- `openapi.yaml`: OpenAPI 接口描述文件（专为导入 Apifox 准备）。
- `mock_server.py`: （可选）基于 FastAPI 的本地 Mock 服务器脚本。
- `README.md`: 本使用指南。

---

## 方案一：在 Apifox 中直接使用高级 Mock（推荐）

这是最快捷的方法，不需要编写代码或启动本地服务，直接利用 Apifox 内置的 Mock 引擎。

### 1. 导入接口至 Apifox
1. 打开 Apifox，进入你的项目。
2. 点击左侧菜单栏的 **“项目设置”** -> **“导入数据”**。
3. 选择 **“OpenAPI / Swagger”** 格式。
4. 将本目录下的 `openapi.yaml` 文件拖入或选择上传导入。
5. 导入成功后，在接口列表中会看到 `GET /api/v1/video/events` (获取视频事件列表)。

### 2. 配置 Apifox 高级 Mock
为了让接口直接返回我们指定的 JSON 数据：
1. 在 Apifox 接口列表中点击刚导入的 `获取视频事件列表` 接口。
2. 切换到 **“高级 Mock”** 标签页。
3. 点击 **“新建期望”**。
4. **期望名称**：可以命名为“默认返回完整事件”。
5. **响应内容 (Body)**：将 `video_events_mock.json` 里的全部 JSON 内容复制，并粘贴到此处。
6. 点击 **“保存”**。

### 3. 测试 Mock 接口
1. 切换到 **“运行”** 标签页。
2. 环境选择为 **“本地 Mock”** 或者 **“云端 Mock”**。
3. 点击 **“发送”**，你即可在下方响应结果中看到完美的 JSON Mock 数据。

---

## 方案二：在 `capstone` 虚拟环境中使用 Python 本地 Mock

如果你需要一个本地服务来接收请求（例如在代码里直接调用调试，或通过 Apifox 连接本地服务调试），可以使用提供的 `mock_server.py`。

### 1. 激活 `capstone` 虚拟环境
假设你的虚拟环境已创建，请先激活它（具体命令视你的本地配置而定）：
```bash
# 如果使用 conda:
conda activate capstone

# 如果使用 venv (假设 venv 目录在其他位置):
source /path/to/venv/bin/activate
```

### 2. 安装依赖包
在虚拟环境中安装 FastAPI 和 Uvicorn：
```bash
pip install fastapi uvicorn
```

### 3. 运行 Mock 服务器
进入当前目录并启动服务：
```bash
cd ~/capstone/Capstone/agent/memory
python mock_server.py
```
终端会输出 `Starting Mock Server on http://0.0.0.0:8000`。

### 4. 使用 Apifox 测试本地服务
1. 在 Apifox 中创建一个新环境（例如名为“本地开发环境”），将前置 URL 设置为 `http://127.0.0.1:8000`。
2. 打开 `获取视频事件列表` 接口，选择“本地开发环境”。
3. 点击发送。
4. Apifox 会请求你的本地 Python 服务，并返回 `video_events_mock.json` 中的数据。
