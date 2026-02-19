# BlogN2 Docker 部署指南

本文档说明如何使用 Docker 容器化部署 BlogN2 应用。

> **注意**：本项目使用优化后的 Dockerfile，使用 CPU-only PyTorch，镜像大小约 1.6GB，并优化了构建缓存以提高构建速度。

## 📋 部署架构

BlogN2 容器化部署采用以下架构：

- **应用容器**：运行 FastAPI 应用
- **外部 PostgreSQL**：通过环境变量 `DATABASE_URL` 连接
- **外部 Redis**：通过环境变量 `CACHE_REDIS_HOST` 等连接
- **BERT 模型缓存**：通过环境变量 `MODEL_CACHE_DIR` 配置，容器内缓存

> **注意**：PostgreSQL、Redis 和 BERT 模型缓存不包含在容器中，需要通过环境变量注入配置。

## 🚀 快速开始

### 前置要求

1. **Docker** 已安装，且 **Docker 守护进程（daemon）已运行**
   - Linux：`sudo systemctl start docker` 或 `sudo service docker start`
   - 若构建时报 `permission denied` 或 `connect: connection refused`，请先确认 daemon 已启动：`docker info`
2. **PostgreSQL 数据库**（支持 pgvector 扩展）已部署并可访问
3. **Redis 服务器**已部署并可访问
4. 确保应用容器可以访问上述服务

### 1. 克隆项目并切换到 docker 分支

```bash
git clone https://github.com/yaowangm/blogn2.git
cd blogn2
git checkout docker
```

### 2. 配置环境变量

```bash
# 在项目根目录复制环境变量模板
cp docker/env.docker.example .env

# 编辑配置文件
nano .env
```

**关键配置项**：

```env
# 数据库配置（必须指向可访问的PostgreSQL服务器）
DATABASE_URL=postgresql+asyncpg://用户名:密码@主机:端口/数据库名

# Redis配置（必须指向可访问的Redis服务器）
CACHE_REDIS_HOST=redis-host
CACHE_REDIS_PORT=6379
CACHE_REDIS_PASSWORD=

# BERT模型配置（模型缓存目录，容器内路径）
MODEL_CACHE_DIR=/app/.cache/models

# 应用配置
APP_ENV=production
BASE_URL=https://yourdomain.com
SECRET_KEY=your-super-secret-jwt-key-change-in-production

# 密码重置邮件：使用宿主机 sendmail（宿主机需安装并运行 sendmail）
# 使用 host 网络时填 localhost，容器即可连到宿主机 25 端口
MAIL_FROM=noreply@yourdomain.com
SMTP_HOST=localhost
SMTP_PORT=25
```

### 3. 创建必要的目录

```bash
# 创建上传目录（用于持久化存储）
mkdir -p uploads avatars
chmod -R 755 uploads avatars
```

### 4. 构建和启动容器

> **构建约定**：请勿使用 `docker build --no-cache`。使用默认缓存可只重建变更层，避免重新下载所有依赖；仅在怀疑缓存损坏时再考虑 `--no-cache`。

```bash
# 在项目根目录构建镜像（使用缓存，仅重建变更层）
docker build -f docker/Dockerfile -t blogn2-app .

# 启动容器（在项目根目录执行）
# 注意：需要将实际的图片目录挂载到容器中
# 如果图片在 ../pic/blogn_img/upload，则挂载该目录
docker run -d \
  --name blogn2-app \
  --restart unless-stopped \
  --network host \
  -e BLOGN_CONFIG_FILE=/app/config.env \
  -v $(pwd)/.env:/app/config.env:ro \
  -v /home/wy/pic/blogn_img/upload:/app/uploads \
  -v /home/wy/pic/blogn_img/userlogo:/app/avatars \
  -v /home/wy/.cache/huggingface:/app/.cache/huggingface:ro \
  -v /home/wy/.cache/modelscope:/app/.cache/modelscope:ro \
  blogn2-app

# 查看日志
docker logs -f blogn2-app
```

> **说明**：
> - Dockerfile 使用 CPU-only PyTorch，镜像更小，构建更快。构建时 PyTorch 安装层独立缓存，提高后续构建速度。
> - 模型缓存目录路径 `/home/wy/.cache/huggingface` 和 `/home/wy/.cache/modelscope` 需要根据实际情况修改。

### 5. 验证部署

```bash
# 检查容器状态
docker ps | grep blogn2-app

# 测试健康检查
curl http://localhost:8000/health

# 查看应用日志
docker logs blogn2-app
```

## 🔧 配置说明

### 环境变量配置

所有配置通过环境变量注入，主要配置项包括：

#### 数据库配置
- `DATABASE_URL`: PostgreSQL 连接 URL（必需）
  - 格式：`postgresql+asyncpg://用户名:密码@主机:端口/数据库名`
  - 示例：`postgresql+asyncpg://blogn_user:password@db.example.com:5432/blogn_example`

#### Redis 配置
- `CACHE_REDIS_HOST`: Redis 服务器地址（必需）
- `CACHE_REDIS_PORT`: Redis 端口（默认：6379）
- `CACHE_REDIS_PASSWORD`: Redis 密码（可选）
- `CACHE_REDIS_DB`: Redis 数据库编号（默认：0）

#### BERT 模型配置
- `MODEL_MODEL_NAME`: 模型名称（默认：`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`）
- `MODEL_DEVICE`: 运行设备（`cpu`/`cuda`，默认：`cpu`）
- `MODEL_CACHE_DIR`: 模型缓存目录（默认：`/app/.cache/models`）
- `MODEL_FALLBACK_TO_HUGGINGFACE`: 是否回退到在线下载（默认：`true`）

##### 下载 BERT 模型并获取本地缓存

应用使用的 BERT 模型是 `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`。首次运行时，模型会自动从 Hugging Face 下载。为了加快后续启动速度，可以预先下载模型并获取本地缓存路径。

**方法 1：在宿主机上下载模型（推荐）**

1. **安装 Python 和依赖**
   ```bash
   # 确保已安装 Python 3.8+
   python3 --version
   
   # 安装 sentence-transformers
   pip install sentence-transformers
   ```

2. **下载模型到本地**
   ```bash
   python3 -c "
   from sentence_transformers import SentenceTransformer
   model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
   print('模型已下载到:', model._model_card_vars.get('cache_folder', '默认缓存目录'))
   "
   ```

3. **查找模型缓存路径**
   
   模型通常下载到以下位置之一：
   - Linux: `~/.cache/huggingface/hub/models--sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2`
   - 或者: `~/.cache/torch/sentence_transformers/sentence-transformers_paraphrase-multilingual-MiniLM-L12-v2`
   
   可以通过以下命令查找：
   ```bash
   # 查找模型缓存目录
   find ~/.cache -name "*paraphrase-multilingual-MiniLM-L12-v2*" -type d 2>/dev/null
   
   # 或者查看 Python 缓存目录
   python3 -c "
   from sentence_transformers import SentenceTransformer
   import os
   model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
   cache_path = os.path.expanduser('~/.cache/huggingface/hub')
   print('Hugging Face 缓存目录:', cache_path)
   print('模型应位于:', cache_path + '/models--sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2')
   "
   ```

4. **挂载模型缓存到容器**
   
   使用 **docker-compose** 时，已配置 `MODEL_CACHE_DIR=/app/.cache/huggingface` 与 `HF_HOME=/app/.cache/huggingface`，只要在 `volumes` 中挂载宿主机 `~/.cache/huggingface` 到 `/app/.cache/huggingface`，容器会直接使用该目录中的 BERT 模型，避免出现 “No sentence-transformers model found ... Creating a new one with MEAN pooling”。
   
   若使用 **docker run**，找到模型缓存路径后，在启动容器时挂载：
   ```bash
   docker run -d \
     --name blogn2-app \
     --restart unless-stopped \
     --network host \
     -e BLOGN_CONFIG_FILE=/app/config.env \
     -e MODEL_CACHE_DIR=/app/.cache/huggingface \
     -e HF_HOME=/app/.cache/huggingface \
     -v $(pwd)/.env:/app/config.env:ro \
     -v /home/wy/pic/blogn_img/upload:/app/uploads \
     -v /home/wy/pic/blogn_img/userlogo:/app/avatars \
     -v ~/.cache/huggingface:/app/.cache/huggingface:ro \
     blogn2-app
   ```

**方法 2：在容器内下载模型**

如果容器有网络访问权限，模型会在首次启动时自动下载：

1. **启动容器并等待模型下载**
   ```bash
   docker run -d \
     --name blogn2-app \
     --restart unless-stopped \
     --network host \
     -e BLOGN_CONFIG_FILE=/app/config.env \
     -v $(pwd)/.env:/app/config.env:ro \
     -v /home/wy/pic/blogn_img/upload:/app/uploads \
     -v /home/wy/pic/blogn_img/userlogo:/app/avatars \
     -v blogn2-model-cache:/app/.cache/models \
     blogn2-app
   
   # 查看日志，等待模型下载完成
   docker logs -f blogn2-app
   ```

2. **模型下载完成后，保存缓存**
   ```bash
   # 创建命名 volume 以持久化模型缓存
   docker volume create blogn2-model-cache
   
   # 或者将容器内的缓存复制到宿主机
   docker cp blogn2-app:/app/.cache/models ~/model_cache
   ```

**方法 3：使用 MODEL_MODEL_PATH 指定本地模型路径**

如果模型已经下载到本地特定路径，可以通过环境变量指定：

1. **在 .env 文件中配置**
   ```env
   # 指定本地模型路径（宿主机路径）
   MODEL_MODEL_PATH=/path/to/local/model
   MODEL_PREFER_LOCAL=true
   MODEL_FALLBACK_TO_HUGGINGFACE=false
   ```

2. **挂载本地模型目录**
   ```bash
   docker run -d \
     --name blogn2-app \
     --restart unless-stopped \
     --network host \
     -e BLOGN_CONFIG_FILE=/app/config.env \
     -v $(pwd)/.env:/app/config.env:ro \
     -v /path/to/local/model:/app/.cache/models/paraphrase-multilingual-MiniLM-L12-v2:ro \
     -v /home/wy/pic/blogn_img/upload:/app/uploads \
     -v /home/wy/pic/blogn_img/userlogo:/app/avatars \
     blogn2-app
   ```

**验证模型缓存**

启动容器后，可以通过以下命令验证模型是否已缓存：

```bash
# 检查容器内的模型缓存目录
docker exec blogn2-app ls -la /app/.cache/models

# 查看模型加载日志
docker logs blogn2-app | grep -i model

# 测试模型是否正常工作
docker exec blogn2-app python3 -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
print('模型加载成功！')
"
```

**若仍报错 “couldn't find it in the cached files” / “couldn't connect to huggingface.co”**

说明容器内未在挂载的缓存里找到模型（或无法联网）。当前 compose 已配置为**挂载 HF hub 模型目录**，entrypoint 会自动解析到 `snapshots/<revision>`（无需关心具体 revision 哈希）：

1. **确认宿主机上存在 hub 目录**（含 `snapshots/` 子目录）：
   ```bash
   ls ~/.cache/huggingface/hub/models--sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2/snapshots/
   ```

2. **宿主机路径**：若 BERT 在默认目录（`~/.cache/huggingface/hub/...`），无需改；若在**其它目录**，在项目根目录 `.env` 中增加：
   ```env
   BERT_MODEL_HUB_HOST_PATH=/你的宿主机路径/到含 snapshots 的 hub 目录
   ```
   例如 `/data/models/paraphrase-multilingual-MiniLM-L12-v2`（该目录下需有 `snapshots/<revision>/config.json`）。compose 会读取该变量作为 volume 宿主机路径，无需改 docker-compose.yml。

3. **重新创建并启动容器**：
   ```bash
   cd docker && docker-compose up -d --force-recreate
   ```
   启动日志中应出现「从 hub 解析到 snapshot: ...」和「模型目录有效（含 config.json）」。

**注意事项**

- 模型大小约 420MB，首次下载可能需要一些时间
- 如果网络不稳定，建议使用方法 1 预先下载
- 模型缓存目录建议使用只读挂载（`:ro`）以提高安全性
- 确保模型缓存目录有足够的磁盘空间（至少 500MB）

#### 应用配置
- `APP_ENV`: 应用环境（`development`/`production`/`testing`）
- `BASE_URL`: 应用基础 URL（用于生成链接）
- `SECRET_KEY`: JWT 密钥（生产环境必须修改）
- `LOG_LEVEL`: 日志级别（`debug`/`info`/`warning`/`error`，默认：`warning`）
  - `warning`: 只显示警告和错误（推荐生产环境）
  - `error`: 只显示错误
  - `info`: 显示信息、警告和错误
  - `debug`: 显示所有日志（包括调试信息）

详细配置请参考 `docker/env.docker.example` 文件。

### 网络配置

#### 连接到外部 PostgreSQL 和 Redis

容器默认使用 `--network host` 模式，可以直接访问宿主机上的服务。

**使用主机网络（默认）**

```bash
# 在 docker run 命令中使用 --network host（已在启动命令中包含）
# 然后使用 localhost 或 127.0.0.1 连接数据库和 Redis
```

**使用桥接网络**

如果需要使用 Docker 网络，可以创建网络并连接：

```bash
# 创建网络
docker network create blogn2-network

# 启动容器时指定网络
docker run -d \
  --name blogn2-app \
  --network blogn2-network \
  # ... 其他参数
  blogn2-app
```

**连接到其他容器**

如果 PostgreSQL 和 Redis 也在 Docker 容器中，可以使用容器名称作为主机名：

```bash
# 在 .env 文件中配置
DATABASE_URL=postgresql+asyncpg://user:pass@postgres-container:5432/db
CACHE_REDIS_HOST=redis-container
```

### 数据持久化

#### 上传文件持久化

上传的文件和用户头像通过 volume 挂载持久化。**注意**：需要挂载实际的图片目录，而不是空的目录。

如果图片文件在 `../pic/blogn_img/upload`（相对于项目根目录），则：

```bash
-v /home/wy/pic/blogn_img/upload:/app/uploads
-v /home/wy/pic/blogn_img/userlogo:/app/avatars
```

如果图片文件在其他位置，请根据实际路径修改。

#### 模型缓存

BERT 模型缓存可以通过 volume 挂载持久化：

1. **方法 1：挂载本地目录**（推荐）

```bash
# 在启动命令中添加
-v $(pwd)/model_cache:/app/.cache/models
```

2. **方法 2：使用 Docker volume**

```bash
# 创建命名 volume
docker volume create blogn2-model-cache

# 在启动命令中使用
-v blogn2-model-cache:/app/.cache/models
```

## 🛠️ 常用操作

### 查看日志

```bash
# 查看应用日志
docker logs blogn2-app

# 实时跟踪日志
docker logs -f blogn2-app

# 查看最近 100 行日志
docker logs --tail=100 blogn2-app
```

### 重启服务

```bash
# 重启应用容器
docker restart blogn2-app

# 停止容器
docker stop blogn2-app

# 启动容器
docker start blogn2-app
```

### 进入容器

```bash
# 进入运行中的容器
docker exec -it blogn2-app bash

# 以 root 用户进入
docker exec -it --user root blogn2-app bash
```

### 执行管理命令

```bash
# 创建管理员用户
docker exec blogn2-app python scripts/create_admin_user.py

# 运行数据库迁移（如果有）
docker exec blogn2-app python scripts/init_db.py
```

### 更新应用

```bash
# 拉取最新代码
git pull

# 重新构建镜像
docker build -f docker/Dockerfile -t blogn2-app .

# 停止并删除旧容器
docker stop blogn2-app
docker rm blogn2-app

# 启动新容器（使用与首次启动相同的命令）
docker run -d \
  --name blogn2-app \
  --restart unless-stopped \
  --network host \
  -e BLOGN_CONFIG_FILE=/app/config.env \
  -e UPLOAD_DIR=/app/uploads \
  -e AVATAR_DIR=/app/avatars \
  -v $(pwd)/.env:/app/config.env:ro \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/avatars:/app/avatars \
  -v /home/wy/.cache/huggingface:/app/.cache/huggingface:ro \
  -v /home/wy/.cache/modelscope:/app/.cache/modelscope:ro \
  blogn2-app
```

## 🔍 故障排查

### 构建时报 permission denied / connection refused

- 多为 **Docker 守护进程未运行**。先启动：`sudo systemctl start docker`（或 `sudo service docker start`），再执行 `docker build`。
- 验证：`docker info` 能正常输出即表示 daemon 已就绪。

### 拉取基础镜像超时（Client.Timeout exceeded / request canceled）

- 多为访问 Docker Hub（registry-1.docker.io）网络慢或被限。可配置 **Docker 镜像加速**，让拉取走国内镜像。
- 创建或编辑 `/etc/docker/daemon.json`（若已有该文件，只追加 `registry-mirrors` 即可）：
  ```json
  {
    "registry-mirrors": [
      "https://docker.m.daocloud.io",
      "https://docker.1ms.run"
    ]
  }
  ```
- 保存后重启 Docker：`sudo systemctl restart docker`（或 `sudo service docker restart`）。
- 再执行：`docker build -f docker/Dockerfile -t blogn2-app .`
- 若仍超时，可搜索当前可用的 Docker 镜像加速地址（如阿里云容器镜像服务提供的个人加速器）并替换上述地址。

### 容器无法启动

1. **检查日志**
   ```bash
   docker logs blogn2-app
   ```

2. **检查环境变量**
   ```bash
   docker exec blogn2-app env | grep -E 'DATABASE_URL|CACHE_REDIS|MODEL_|APP_'
   ```

3. **检查数据库连接**
   ```bash
   docker exec blogn2-app python -c "
   import os
   from urllib.parse import urlparse
   url = os.getenv('DATABASE_URL')
   parsed = urlparse(url.replace('postgresql+asyncpg://', 'http://'))
   print(f'数据库主机: {parsed.hostname}:{parsed.port or 5432}')
   "
   ```

### password authentication failed for user "xxx"（远程可手动登录但容器内失败）

1. **为何 `docker exec blogn2-app env | grep DATABASE_URL` 无输出？**
   配置是通过 entrypoint 从**挂载的配置文件**读入并只传给 uvicorn 进程的，不会写回容器的默认环境，所以 `docker exec ... env` 看不到 `DATABASE_URL`，这是预期行为。要确认配置是否被读入，请：
   - 看启动日志：若出现 `✅ 已从配置文件加载 DATABASE_URL 等变量`，说明文件已读且包含 `DATABASE_URL`；若出现 `⚠️ 配置文件已读取，但未包含 DATABASE_URL`，说明文件里没有该键或键名不对。
   - 在容器内用同一份文件检查（不打印密码）：  
     `docker exec blogn2-app python3 -c "
from dotenv import load_dotenv
import os
load_dotenv('/app/config.env')
u = os.getenv('DATABASE_URL','')
if u:
    from urllib.parse import urlparse
    p = urlparse(u.replace('postgresql+asyncpg://','http://'))
    print('DATABASE_URL 已设置  主机:', p.hostname, '端口:', p.port or 5432, '用户:', p.username)
else:
    print('DATABASE_URL 未设置，请检查 /app/config.env 是否存在且含 DATABASE_URL=...')
"`
   - 确认挂载正确：`docker exec blogn2-app cat /app/config.env | head -5` 应能看到你配置的前几行（注意不要在生产环境暴露完整配置）。

2. **确认远程用的是远程库的配置**
   若通过 `-v /home/wy/blogn_docker.cnf:/app/config.env` 挂载，请确认**执行 `docker run` 的那台机**上的 `/home/wy/blogn_docker.cnf` 里写的是**该机可访问的数据库**的地址和密码（与在该机“手动能登录”的凭据一致），而不是本地开发用的连接串。

3. **密码中含特殊字符时必须 URL 编码**
   `DATABASE_URL` 格式为 `postgresql+asyncpg://用户名:密码@主机:端口/数据库名`。密码里若包含 `@`、`#`、`:`、`/`、`?`、`%` 等，必须按 URL 编码写入，否则会被解析错导致认证失败。例如：
   - `@` → `%40`
   - `#` → `%23`
   - `:` → `%3A`
   - `/` → `%2F`
   - `%` → `%25`
   例：密码为 `p@ss#123` 时，URL 中应写 `p%40ss%23123`。

4. **密码里含有 `#` 时必须用引号包住整条值**
   在 `.env` / `config.env` 里，`#` 表示注释，**未加引号时**同一行中 `#` 后面的内容会被忽略。若密码含 `#`，整条值需用双引号包住，例如：  
   `DATABASE_URL="postgresql+asyncpg://wy:pass#123@localhost:5432/blogn"`  
   否则实际传给应用的可能只有 `postgresql+asyncpg://wy:pass`，导致认证失败。

5. **改完配置后重启容器**
   修改挂载的配置文件后需重启容器才能生效：`docker restart blogn2-app`。

### 无法连接数据库

1. **检查网络连接**
   ```bash
   docker exec blogn2-app ping -c 3 <数据库主机>
   ```

2. **检查端口**
   ```bash
   docker exec blogn2-app nc -zv <数据库主机> 5432
   ```

3. **检查 DATABASE_URL 格式**
   - 确保 URL 格式正确
   - 检查用户名、密码、主机、端口、数据库名

### 无法连接 Redis

1. **检查 Redis 连接**
   ```bash
   docker exec blogn2-app python -c "
   import redis
   import os
   r = redis.Redis(
       host=os.getenv('CACHE_REDIS_HOST', 'localhost'),
       port=int(os.getenv('CACHE_REDIS_PORT', '6379')),
       password=os.getenv('CACHE_REDIS_PASSWORD') or None
   )
   print('Redis连接:', r.ping())
   "
   ```

### 图片 /upload/ 或 /avatar/ 返回 404（目录正确、文件在宿主机存在）

- 在 **Docker 容器内**，应用只能访问容器内的路径。若配置里写的是**宿主机路径**（如 `UPLOAD_DIR=/home/wy/pic/blogn_img/upload`），该路径在容器中不存在，`/upload/xxx` 会返回 404。
- **正确做法**：在容器用的配置文件（如 `blogn_docker.cnf`）中设置为**容器内路径**，并通过 `-v` 把宿主机目录挂载到该路径：
  - `UPLOAD_DIR=/app/uploads`，启动时加：`-v /home/wy/pic/blogn_img/upload:/app/uploads`
  - `AVATAR_DIR=/app/avatars`，启动时加：`-v /home/wy/pic/blogn_img/userlogo:/app/avatars`
- 修改后重启容器：`docker restart blogn2-app`。启动日志中若出现“上传目录为宿主机路径…”的提示，说明仍需按上述方式改为容器路径并挂载。

### 模型下载失败

1. **检查网络连接**
   ```bash
   docker exec blogn2-app ping -c 3 huggingface.co
   ```

2. **检查 MODEL_CACHE_DIR 权限**
   ```bash
   docker exec blogn2-app ls -la /app/.cache/models
   ```

3. **手动下载模型**（如果需要）
   - 在宿主机下载模型
   - 挂载到容器的 `MODEL_CACHE_DIR`

### 日志出现 Invalid HTTP request / Unsupported upgrade / 重复重启

1. **Invalid HTTP request received**
   - 通常表示有客户端或反向代理用**非 HTTP** 访问了 8000 端口（例如：用 HTTPS 访问、或做了 TCP 健康检查）。
   - 若前面有 Nginx/Traefik 等反向代理：请确保**到后端的协议是 HTTP**（代理终止 TLS，向后端发 HTTP），不要对 8000 端口直接发 HTTPS。
   - 若使用负载均衡器的「TCP 健康检查」：可改为「HTTP 健康检查」，请求 `http://容器:8000/health`。

2. **Unsupported upgrade request / No supported WebSocket library**
   - 已通过依赖中显式加入 `websockets` 解决。重新构建镜像即可：  
     `docker build -f docker/Dockerfile -t blogn2-app .`

3. **容器反复重启**
   - 健康检查在应用未完全就绪时可能失败（如 BERT 加载较慢）。当前 Dockerfile 已把健康检查的 `start-period` 设为 90 秒、`retries` 设为 5。
   - 若仍重启，可先临时去掉健康检查排查：  
     `docker run ... --no-healthcheck blogn2-app`  
   - 查看退出原因：`docker inspect blogn2-app --format '{{.State.ExitCode}}'` 和 `docker logs blogn2-app`。

## 📊 性能优化

### 1. 使用多 worker

在启动容器时，可以通过覆盖默认命令来使用多个 worker：

```bash
docker run -d \
  --name blogn2-app \
  --restart unless-stopped \
  --network host \
  -e BLOGN_CONFIG_FILE=/app/config.env \
  -v $(pwd)/.env:/app/config.env:ro \
  -v /home/wy/pic/blogn_img/upload:/app/uploads \
  -v /home/wy/pic/blogn_img/userlogo:/app/avatars \
  -v /home/wy/.cache/huggingface:/app/.cache/huggingface:ro \
  -v /home/wy/.cache/modelscope:/app/.cache/modelscope:ro \
  blogn2-app \
  uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 2. 资源限制

```yaml
services:
  blogn2:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

### 3. 健康检查

容器已配置健康检查，可以通过以下命令查看：

```bash
docker inspect blogn2-app | grep -A 10 Health
```

## 🔒 安全建议

1. **使用强密码**
   - 修改 `SECRET_KEY` 为强随机字符串
   - 使用强数据库密码

2. **限制网络访问**
   - 只暴露必要的端口
   - 使用防火墙限制访问

3. **定期更新**
   - 定期更新基础镜像
   - 及时应用安全补丁

4. **日志管理**
   - 配置日志轮转
   - 监控异常日志

5. **备份数据**
   - 定期备份数据库
   - 备份上传的文件

## 📚 相关文档

- [INSTALL.md](../INSTALL.md) - 详细安装指南
- [README.md](../README.md) - 项目说明
- [env.docker.example](env.docker.example) - 环境变量配置示例

## 🆘 获取帮助

如果遇到问题，请：

1. 查看日志：`docker logs blogn2-app`
2. 检查容器状态：`docker ps -a | grep blogn2-app`
3. 检查环境变量：`docker exec blogn2-app env | grep -E 'DATABASE_URL|CACHE_REDIS|MODEL_|APP_'`
4. 查看文档：参考项目文档
5. 提交 Issue：在 GitHub 上提交问题

---

**BlogN2** - 容器化部署，简单高效！ 🚀

