# 本地 Docker 部署指南

本文档说明如何在本地使用 Docker 部署 BlogN2 应用，连接到本地已安装的 PostgreSQL、Redis 和 BERT 模型缓存。

## 📋 前置要求

1. **Docker 已安装并运行**
2. **PostgreSQL 已安装并运行**（默认端口 5432）
3. **Redis 已安装并运行**（默认端口 6379）
4. **BERT 模型缓存已存在**（通常在 `~/.cache/huggingface` 或 `~/.cache/modelscope`）

## 🚀 部署步骤

### 1. 启动 Docker 服务

在 WSL 环境中（不支持 systemd），使用以下方法：

#### 方法 1: 使用 service 命令（推荐）

```bash
sudo service docker start
```

#### 方法 2: 使用辅助脚本

```bash
cd docker
./start-docker.sh
```

#### 方法 3: 手动启动 dockerd

```bash
sudo dockerd > /dev/null 2>&1 &
```

#### 方法 4: 使用 Docker Desktop for Windows

如果安装了 Docker Desktop for Windows，确保它在 Windows 端运行，WSL 会自动连接。

#### 检查 Docker 是否运行

```bash
docker ps
```

如果提示权限问题，可以：

```bash
# 添加用户到 docker 组
sudo usermod -aG docker $USER
newgrp docker

# 或修改 socket 权限（临时）
sudo chmod 666 /var/run/docker.sock
```

### 2. 配置环境变量

确保项目根目录有 `.env` 文件，配置如下：

```bash
# 在项目根目录
cp docker/env.docker.example .env
nano .env
```

**关键配置项**：

```env
# 数据库配置（连接到本地 PostgreSQL）
DATABASE_URL=postgresql+asyncpg://用户名:密码@localhost:5432/数据库名

# Redis配置（连接到本地 Redis）
CACHE_REDIS_HOST=localhost
CACHE_REDIS_PORT=6379
CACHE_REDIS_PASSWORD=

# BERT模型配置
MODEL_CACHE_DIR=/app/.cache/huggingface
MODEL_PREFER_LOCAL=true

# 应用配置
APP_ENV=production
BASE_URL=http://localhost:8000
SECRET_KEY=your-super-secret-jwt-key-change-in-production
```

### 3. 创建必要目录

```bash
# 在项目根目录
mkdir -p uploads avatars
chmod 755 uploads avatars
```

### 4. 使用部署脚本（推荐）

```bash
cd docker
./deploy.sh
```

### 5. 手动部署

如果不想使用脚本，可以手动执行：

#### 4.1 构建镜像

```bash
cd docker
docker build -f Dockerfile -t blogn2:latest ..
```

#### 4.2 启动容器

```bash
# 在 docker 目录中执行
docker run -d \
    --name blogn2-app \
    --restart unless-stopped \
    --network host \
    --env-file ../.env \
    -e CACHE_REDIS_HOST=localhost \
    -e MODEL_CACHE_DIR=/app/.cache/huggingface \
    -e MODEL_PREFER_LOCAL=true \
    -v "$(pwd)/../uploads:/app/uploads" \
    -v "$(pwd)/../avatars:/app/avatars" \
    -v "$HOME/.cache/huggingface:/app/.cache/huggingface:ro" \
    -v "$HOME/.cache/modelscope:/app/.cache/modelscope:ro" \
    blogn2:latest
```

### 5. 验证部署

```bash
# 查看容器状态
docker ps | grep blogn2-app

# 查看日志
docker logs -f blogn2-app

# 测试健康检查
curl http://localhost:8000/health
```

## 🔧 配置说明

### 网络模式

使用 `--network host` 模式，容器可以直接访问主机的 localhost 服务（PostgreSQL、Redis）。

### 模型缓存挂载

- `~/.cache/huggingface` → `/app/.cache/huggingface` (只读)
- `~/.cache/modelscope` → `/app/.cache/modelscope` (只读)

这样可以复用本地已下载的模型，避免容器内重新下载。

### 数据持久化

- `uploads/` → `/app/uploads` (上传文件)
- `avatars/` → `/app/avatars` (用户头像)

## 🛠️ 常用操作

### 查看日志

```bash
docker logs -f blogn2-app
```

### 停止容器

```bash
docker stop blogn2-app
```

### 启动容器

```bash
docker start blogn2-app
```

### 重启容器

```bash
docker restart blogn2-app
```

### 进入容器

```bash
docker exec -it blogn2-app bash
```

### 删除容器

```bash
docker stop blogn2-app
docker rm blogn2-app
```

### 重新构建并部署

```bash
cd docker
docker build -f Dockerfile -t blogn2:latest ..
docker stop blogn2-app && docker rm blogn2-app
./deploy.sh
```

## 🔍 故障排查

### Docker daemon 未运行

```bash
sudo systemctl start docker
sudo systemctl enable docker  # 设置开机自启
```

### 无法连接到 PostgreSQL

1. 检查 PostgreSQL 是否运行：
   ```bash
   sudo systemctl status postgresql
   ```

2. 检查端口是否监听：
   ```bash
   sudo netstat -tlnp | grep 5432
   ```

3. 检查 DATABASE_URL 配置是否正确

### 无法连接到 Redis

1. 检查 Redis 是否运行：
   ```bash
   sudo systemctl status redis
   ```

2. 检查端口是否监听：
   ```bash
   sudo netstat -tlnp | grep 6379
   ```

3. 测试连接：
   ```bash
   redis-cli ping
   ```

### 模型加载失败

1. 检查模型缓存目录是否存在：
   ```bash
   ls -la ~/.cache/huggingface
   ls -la ~/.cache/modelscope
   ```

2. 检查挂载是否正确：
   ```bash
   docker exec blogn2-app ls -la /app/.cache/huggingface
   ```

3. 查看容器日志：
   ```bash
   docker logs blogn2-app | grep -i model
   ```

## 📚 相关文档

- [README-DOCKER.md](README-DOCKER.md) - 完整 Docker 部署文档
- [env.docker.example](env.docker.example) - 环境变量配置示例

---

**提示**：如果遇到权限问题，确保当前用户在 docker 组中，或使用 sudo 运行 docker 命令。

