# Capstone FastAPI Deploy Guide

## 目标

- 部署当前仓库里的 `FastAPI` Web 界面与 API 服务。
- 服务目录位于 `fastapi/`。
- 默认启动入口是仓库根目录的 `quick_start.sh`。

## 部署前提

- 机器已拉取当前仓库到目标目录。
- 已安装 `conda`，并存在可用的 `capstone` 环境。
- 目标机器具备当前项目运行所需的模型、数据库与 API key。
- 如果需要公网访问，已准备反向代理或端口开放策略。

## 推荐方式

- 本地开发或单机验证：
  - 使用 `quick_start.sh`
- 长期驻留：
  - 使用 `systemd`
- 容器化：
  - 使用 `fastapi/docker-compose.yml`

## 本地快速启动

在仓库根目录执行：

```bash
chmod +x quick_start.sh
./quick_start.sh
```

可选环境变量：

```bash
HOST=127.0.0.1 PORT=8010 OPEN_BROWSER=0 ./quick_start.sh
```

默认访问地址：

```text
http://127.0.0.1:8001/
```

## 手动启动

```bash
source ~/.bashrc
conda activate capstone
uvicorn main:app --app-dir /absolute/path/to/Capstone/fastapi --host 0.0.0.0 --port 8001
```

如果你要固定单机路径，可以直接运行：

```bash
/home/yangxp/Capstone/fastapi/run_uvicorn.sh
```

## systemd 部署

当前仓库已提供：

- `fastapi/capstone-agent-fastapi.service`
- `fastapi/deploy_systemd.sh`

安装步骤：

```bash
chmod +x fastapi/deploy_systemd.sh fastapi/run_uvicorn.sh
./fastapi/deploy_systemd.sh
```

常用命令：

```bash
sudo systemctl status capstone-agent-fastapi.service
sudo systemctl restart capstone-agent-fastapi.service
sudo journalctl -u capstone-agent-fastapi.service -f
```

## Docker 部署

部署文件：

- `fastapi/Dockerfile`
- `fastapi/docker-compose.yml`
- `fastapi/.env.example`

步骤：

```bash
cd fastapi
cp .env.example .env
docker compose up --build -d
```

如果你已经部署过旧版本，当前又同步了新的前后端代码，使用：

```bash
cd fastapi
docker compose up --build -d
```

这一步不能省略。当前 `docker-compose.yml` 只挂载运行数据目录，不会把仓库源码实时映射进容器；不重新 `build` 的话，容器里仍然会是旧的前端脚本和旧的后端逻辑。

查看日志：

```bash
docker compose logs -f
```

停止服务：

```bash
docker compose down
```

## 必要环境变量

常见变量：

- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `AGENT_USE_LLAMAINDEX_SQL`
- `AGENT_ENABLE_RERANK`
- `AGENT_DISABLE_VERIFIER_NODE`
- `AGENT_SUMMARY_BAIL_OUT_STRICT`
- `AGENT_EMBEDDING_CACHE_DIR`
- `AGENT_EMBEDDING_CACHE_LRU_SIZE`
- `FASTAPI_MAX_UPLOAD_MB`
- `HOST`
- `PORT`

如果依赖视频精炼或线上模型能力，目标环境必须提供对应的 API key。

## 验证步骤

启动后优先检查：

```bash
curl http://127.0.0.1:8001/healthz
```

然后在浏览器打开：

```text
http://127.0.0.1:8001/
```

推荐验证流程：

1. 打开页面确认前端可访问。
2. 选择一个数据库。
3. 执行一次查询。
4. 上传一个或一批视频。
5. 确认系统自动切换到新数据库。
6. 确认新上传的数据集会立即出现在可选数据库列表中。
7. 确认上传进度条会在完成后自动回到 `0%`。
8. 继续执行一次查询，确认新库可直接使用。

## 常见问题

- 页面打不开：
  - 检查 `HOST`、`PORT`、防火墙与反向代理配置。
- 服务能起但查询失败：
  - 检查 API key、数据库路径、模型依赖和 `capstone` 环境。
- 上传失败：
  - 检查文件格式、单文件大小限制和服务端日志。
- 上传成功但新数据集没有出现在列表里：
  - 如果是 `Docker` 部署，优先执行 `docker compose up --build -d`，确认容器已更新到最新镜像。
  - 再检查 `fastapi/data` 是否正确挂载并持久化到宿主机。
  - 需要时执行 `docker compose logs -f`，确认上传任务完成且没有容器内异常。
- `uvicorn` 启动失败：
  - 优先确认是否使用了新的目录入口：
  - `uvicorn main:app --app-dir /.../Capstone/fastapi`

## 相关文件

- `quick_start.sh`
- `fastapi/run_uvicorn.sh`
- `fastapi/README.md`
- `fastapi/capstone-agent-fastapi.service`
- `fastapi/docker-compose.yml`
