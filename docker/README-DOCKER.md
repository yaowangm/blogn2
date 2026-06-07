# BlogN2 Docker 部署指南

本文档说明分层镜像构建、手动导出/加载、以及远程 `docker run` 部署的完整流程。

## 架构

| 组件 | 说明 |
|------|------|
| **blogn2-base** | Python 3.12 + PyTorch(CPU) + pip 依赖（约 1.23GB） |
| **blogn2-app** | 在 base 上叠加业务代码（`docker images` 显示约 1.25GB，含父层） |
| **PostgreSQL / Redis** | 容器外，经 `DATABASE_URL`、`CACHE_REDIS_*` 连接 |
| **BERT 模型** | 容器外，经 volume 挂载到 `/app/.cache/models/bert-model-hub` |

应用配置通过 **volume 挂载的配置文件** 注入（`BLOGN_CONFIG_FILE=/app/config.env`），不要把 `BLOGN_CONFIG_FILE` 写进 `.env` 文件内容里。

---

## 工作流程速查

### 本地（构建机）

```bash
cd /path/to/blogn2
chmod +x docker/*.sh

# 首次或改 requirements-prod.txt / PyTorch
./docker/build-base.sh

# 日常改代码
./docker/build-app.sh latest

# 导出（默认输出到当前目录）
cd ~/docker    # 建议放在项目外，勿放在 docker/docker/ 下
/path/to/blogn2/docker/save-images.sh base
/path/to/blogn2/docker/save-images.sh app latest
```

### 远程（生产机）

```bash
cd ~/docker
cp -r /path/to/blogn2/docker/load-images.sh /path/to/blogn2/docker/lib .

# 首次
./load-images.sh base
./load-images.sh app latest

# 启动（见「启动容器」一节完整 docker run 命令）
sudo docker rm -f blogn2-app 2>/dev/null
# sudo docker run -d ... 见下文
```

### 日常发版（远程已有 base）

```bash
# 构建机
./docker/build-app.sh latest
cd ~/docker && /path/to/blogn2/docker/save-images.sh app latest
# 上传 blogn2-app-latest-delta.tar.gz（约 5–20MB）

# 远程
./load-images.sh app latest
sudo docker rm -f blogn2-app && sudo docker run -d ...   # 完整命令见「启动容器」
```

---

## 脚本一览

| 脚本 | 作用 |
|------|------|
| `build-base.sh` | 构建 `blogn2-base:1.0`（版本见 `BASE_VERSION`） |
| `build-app.sh [tag]` | 构建 `blogn2-app:[tag]`，**须先有 base** |
| `build-legacy.sh [tag]` | 一体镜像 `docker/Dockerfile`（兼容旧流程） |
| `save-images.sh base` | 导出完整 base 包 `blogn2-base-1.0.tar.gz`（约 380MB） |
| `save-images.sh app [tag]` | 导出**增量**包 `blogn2-app-{tag}-delta.tar.gz`（约 5–20MB） |
| `save-images.sh app-full [tag]` | 导出完整 app 包（约 380MB，远程无 base 时用） |
| `save-images.sh all [tag]` | base + app 增量 |
| `load-images.sh base` | 加载 base 包 |
| `load-images.sh app [tag]` | 加载 app 增量包（**须先 load base**） |
| `save_app_delta.py` | 增量导出实现（由 `save-images.sh app` 调用） |
| `lib/archive_paths.sh` | 导出/加载路径解析与包校验 |

**环境变量**

| 变量 | 默认 | 说明 |
|------|------|------|
| `BASE_VERSION` | `docker/BASE_VERSION`（当前 `1.0`） | base 镜像 tag |
| `OUT_DIR` | 当前目录 | `save-images.sh` 默认输出目录 |
| `DIST_DIR` | — | `load-images.sh` 额外搜索目录 |
| `DOCKER_BUILDKIT` | `0`（脚本内强制） | 使用经典 `docker build`，无需 buildx |

---

## 构建镜像

### 分层构建（推荐）

```bash
# 1) 基础镜像（改 requirements-prod.txt 或 PyTorch 时才需要）
./docker/build-base.sh

# 2) 应用镜像（每次发版）
./docker/build-app.sh latest
```

**构建缓存**：Dockerfile 将 torch 安装在 `COPY requirements-prod.txt` **之前** 的独立层；`python:3.12-slim` 已固定 digest，避免 tag 浮动导致缓存失效。依赖未变时第二次 `build-base.sh` 应显示 `CACHED`。

- 日常发版只用 `build-app.sh`，**不要**每次跑 `build-base.sh`
- 不要用 `docker build --no-cache`
- 本环境不使用 BuildKit / buildx

### 一体构建（兼容）

```bash
./docker/build-legacy.sh latest
# 等价于: DOCKER_BUILDKIT=0 docker build -f docker/Dockerfile -t blogn2-app:latest .
```

### docker-compose

```bash
./docker/build-base.sh
docker compose -f docker/docker-compose.yml build
docker compose -f docker/docker-compose.yml up -d
```

---

## 导出与加载

### 输出文件

| 命令 | 输出文件 | 压缩后（约） | 何时使用 |
|------|----------|--------------|----------|
| `save-images.sh base` | `blogn2-base-1.0.tar.gz` | 380MB | 远程首次部署 / 依赖升级 |
| `save-images.sh app latest` | `blogn2-app-latest-delta.tar.gz` | **5–20MB** | 日常发版 |
| `save-images.sh app-full latest` | `blogn2-app-latest.tar.gz` | 380MB | 远程无法/load base 时 |

### 路径

未指定路径时，**在当前目录**查找/输出。也可显式指定：

```bash
./save-images.sh app latest /home/wy/docker/blogn2-app-latest-delta.tar.gz
./load-images.sh app latest /home/wy/docker/blogn2-app-latest-delta.tar.gz
```

查找顺序（`load-images.sh`）：显式路径 → 当前目录 → `DIST_DIR` → 项目 `docker/dist/`。

### 增量导出原理

`save_app_delta.py` 对比 `blogn2-app` 与 `blogn2-base` 的镜像层：只打包 app 多出来的层 + 新 config。远程须已 `load` 同版本 `blogn2-base`，再 `load` 增量包。

**前提**：`blogn2-app` 必须由 `./docker/build-app.sh` 从当前 `blogn2-base` 构建。若用一体 `Dockerfile` 或旧 base 构建，增量会退化为数百 MB 并可能 load 失败。

### 校验增量包

```bash
ls -lh blogn2-app-latest-delta.tar.gz    # 正常约 5–20MB，>100MB 多半有问题
gunzip -c blogn2-app-latest-delta.tar.gz | tar -tf - | head -10
# 应含: manifest.json  blobs/sha256/...  index.json  oci-layout
```

### base 包校验

```bash
gunzip -c blogn2-base-1.0.tar.gz | tar -tf - | grep -E 'manifest|oci-layout|repositories'
```

仅有 `blobs/` 无 `manifest.json` 说明导出损坏，须用更新后的 `save-images.sh base`（`docker save -o` 再 gzip）重新导出。

---

## 启动容器

生产环境推荐命令（多行续行时，**每行末尾的 `\` 后不能有空格**，否则会出现 `invalid reference format`）：

```bash
sudo docker rm -f blogn2-app 2>/dev/null

sudo docker run -d \
  --name blogn2-app \
  --restart unless-stopped \
  --network host \
  -e BLOGN_CONFIG_FILE=/app/config.env \
  -p 127.0.0.1:8000:8000 \
  -v /home/wy/blogn_docker.cnf:/app/config.env:ro \
  -v /home/wy/pic/blogn_pic/upload:/app/uploads \
  -v /home/wy/pic/blogn_pic/userlogo:/app/avatars \
  -v /home/wy/docker/models--sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2:/app/.cache/models/bert-model-hub:ro \
  blogn2-app:latest
```

验证：

```bash
sudo docker logs blogn2-app
curl -s http://127.0.0.1:8000/health
```

| 参数 | 说明 |
|------|------|
| `--network host` | 访问本机 PostgreSQL、Redis、sendmail |
| `-p 127.0.0.1:8000:8000` | 可与 host 网络同时使用；host 模式下应用已直接监听 8000，此项主要便于文档/习惯一致 |
| `-v ...cnf:/app/config.env:ro` | 配置文件须含 `DATABASE_URL`；路径为**运行 docker 的那台机**上的文件 |
| `-v ...:/app/uploads` / `avatars` | 上传与头像持久化 |
| `-v ...:/app/.cache/models/bert-model-hub:ro` | BERT hub（含 `snapshots/` 或根目录 `config.json`） |
| `blogn2-app:latest` | 显式指定 tag |

entrypoint 会从配置文件加载 `DATABASE_URL` 等变量；`docker exec blogn2-app env` **看不到**这些变量是正常的（只传给 uvicorn 进程）。

---

## 配置说明

### 配置文件示例（`blogn_docker.cnf` / `.env`）

```env
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/blogn
CACHE_REDIS_HOST=localhost
CACHE_REDIS_PORT=6379
BASE_URL=https://yourdomain.com
SECRET_KEY=your-secret-key
```

密码含 `#` 时整条须加双引号；含 `@`、`:` 等须 URL 编码。详见下文「故障排查」。

### 模型挂载

模型目录须含 `config.json`，或 `snapshots/<hash>/config.json`。entrypoint 会自动解析 `MODEL_MODEL_PATH`。

---

## 代码热更新（临时）

仅改少量文件、不想传镜像时：

```bash
tar czf patch.tgz src/controllers/foo.py
scp patch.tgz remote:/tmp/
ssh remote 'docker cp /tmp/foo.py blogn2-app:/app/src/... && docker restart blogn2-app'
```

正式发版仍应 `build-app.sh` + `save-images.sh app`。

---

## 故障排查

### 构建：每次重新下载 torch

- 确认用 `./docker/build-base.sh`，且第二次应出现 `CACHED`
- 不要用 `--no-cache`
- 日常改代码只用 `build-app.sh`

### 构建：BuildKit / buildx 报错

脚本已设 `DOCKER_BUILDKIT=0`，无需安装 buildx。若手动构建：

```bash
DOCKER_BUILDKIT=0 docker build -f docker/Dockerfile.base -t blogn2-base:1.0 .
```

### 增量包 300MB+

1. **导出包被打进镜像**：勿把 `*.tar.gz` 放在项目 `docker/` 下；`.dockerignore` 已排除 `**/*.tar.gz`、`docker/docker/`
2. **app 不是从当前 base 构建**：先 `build-base.sh` 再 `build-app.sh`，再 `save-images.sh app`
3. 验证：`gunzip -c 包名 | tar -tf - | grep manifest`

### load：缺少 manifest.json

增量包损坏或实为旧版错误导出。在构建机重新 `build-app.sh` + `save-images.sh app`，并同步远程的 `load-images.sh` 与 `lib/`。

### docker run：invalid reference format

多行命令里某行写成 `\ `（反斜杠后有空格）会导致续行失败。确保 **`\` 是该行最后一个字符**，或改用单行命令。见「启动容器」示例。

### 容器启动失败

```bash
docker logs blogn2-app
```

| 日志 | 处理 |
|------|------|
| `配置文件不存在` | 检查 `-v` 宿主机路径是否存在 |
| `DATABASE_URL 未设置` | 配置文件缺少该项或 `#` 未加引号 |
| `Conflict ... name already in use` | `docker rm -f blogn2-app` |
| 模型警告 | 不阻止启动；检查 BERT volume 挂载 |

### 数据库认证失败

1. 配置文件必须是**远程机**可连的库，不是开发机连接串
2. 用启动日志确认：`✅ 已从配置文件加载 DATABASE_URL`
3. 密码特殊字符 URL 编码；含 `#` 的值加双引号

### 图片 404

`docker run` 时确认 `-v` 挂载了正确的宿主机上传/头像目录；entrypoint 会强制 `UPLOAD_DIR=/app/uploads`、`AVATAR_DIR=/app/avatars`。

### 拉取 python 基础镜像超时

配置 `/etc/docker/daemon.json` 的 `registry-mirrors` 后 `systemctl restart docker`。

### 容器反复重启

健康检查 `start-period` 为 90s。排查：`docker inspect blogn2-app --format '{{.State.ExitCode}}'` 与 `docker logs`。

---

## 文件结构

```
docker/
├── BASE_VERSION          # base 版本号（当前 1.0）
├── Dockerfile.base       # 基础镜像
├── Dockerfile.app        # 应用镜像（FROM blogn2-base）
├── Dockerfile            # 一体镜像（兼容）
├── build-base.sh
├── build-app.sh
├── build-legacy.sh
├── save-images.sh
├── load-images.sh
├── save_app_delta.py
├── lib/archive_paths.sh
├── docker-entrypoint.sh
├── docker-compose.yml
├── dist/                 # 可选本地导出目录（已在 .dockerignore）
└── README-DOCKER.md
```

---

## 相关文档

- [INSTALL.md](../INSTALL.md)
- [README.md](../README.md)
- [.env.example](../.env.example)
