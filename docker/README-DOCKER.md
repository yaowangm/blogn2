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

1. **Docker** 和 **Docker Compose** 已安装
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
```

### 3. 创建必要的目录

```bash
# 创建上传目录（用于持久化存储）
mkdir -p uploads avatars
chmod -R 755 uploads avatars
```

### 4. 构建和启动容器

```bash
# 进入 docker 目录
cd docker

# 构建镜像
docker-compose build

# 或者直接使用 docker build
docker build -f docker/Dockerfile -t blogn2-app ..

# 启动容器
docker-compose up -d

# 查看日志
docker-compose logs -f
```

> **说明**：Dockerfile 使用 CPU-only PyTorch，镜像更小，构建更快。构建时 PyTorch 安装层独立缓存，提高后续构建速度。

### 5. 验证部署

```bash
# 在 docker 目录中检查容器状态
cd docker
docker-compose ps

# 测试健康检查
curl http://localhost:8000/health

# 查看应用日志
docker-compose logs blogn2
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

#### 应用配置
- `APP_ENV`: 应用环境（`development`/`production`/`testing`）
- `BASE_URL`: 应用基础 URL（用于生成链接）
- `SECRET_KEY`: JWT 密钥（生产环境必须修改）

详细配置请参考 `docker/env.docker.example` 文件。

### 网络配置

#### 连接到外部 PostgreSQL 和 Redis

如果 PostgreSQL 和 Redis 在不同的 Docker 网络中，需要配置网络连接：

**方法 1：使用外部网络**

```yaml
# 在 docker-compose.yml 中
networks:
  blogn2-network:
    external: true
    name: external-network
```

**方法 2：使用主机网络**

```yaml
# 在 docker-compose.yml 中
services:
  blogn2:
    network_mode: "host"
    # 然后使用 localhost 或 127.0.0.1 连接
```

**方法 3：使用服务名称（如果在同一 compose 文件中）**

如果 PostgreSQL 和 Redis 也在同一个 `docker-compose.yml` 中，可以直接使用服务名称：

```yaml
environment:
  - DATABASE_URL=postgresql+asyncpg://user:pass@postgres-service:5432/db
  - CACHE_REDIS_HOST=redis-service
```

### 数据持久化

#### 上传文件持久化

上传的文件和用户头像通过 volume 挂载持久化：

```yaml
volumes:
  - ./uploads:/app/uploads
  - ./avatars:/app/avatars
```

#### 模型缓存

BERT 模型缓存存储在容器内的 `MODEL_CACHE_DIR` 目录中。如果需要持久化：

1. **方法 1：挂载 volume**（推荐）

```yaml
volumes:
  - ./model_cache:/app/.cache/models
```

2. **方法 2：使用命名 volume**

```yaml
volumes:
  - model_cache:/app/.cache/models

volumes:
  model_cache:
```

## 🛠️ 常用操作

### 查看日志

```bash
# 在 docker 目录中执行
cd docker

# 查看所有服务日志
docker-compose logs

# 查看应用日志
docker-compose logs blogn2

# 实时跟踪日志
docker-compose logs -f blogn2

# 查看最近 100 行日志
docker-compose logs --tail=100 blogn2
```

### 重启服务

```bash
# 在 docker 目录中执行
cd docker

# 重启应用容器
docker-compose restart blogn2

# 停止并启动
docker-compose stop blogn2
docker-compose start blogn2
```

### 进入容器

```bash
# 在 docker 目录中执行
cd docker

# 进入运行中的容器
docker-compose exec blogn2 bash

# 以 root 用户进入
docker-compose exec --user root blogn2 bash
```

### 执行管理命令

```bash
# 在 docker 目录中执行
cd docker

# 创建管理员用户
docker-compose exec blogn2 python scripts/create_admin_user.py

# 运行数据库迁移（如果有）
docker-compose exec blogn2 python scripts/init_db.py
```

### 更新应用

```bash
# 拉取最新代码
git pull

# 进入 docker 目录并重新构建镜像
cd docker
docker-compose build

# 重启容器
docker-compose up -d
```

## 🔍 故障排查

### 容器无法启动

1. **检查日志**
   ```bash
   docker-compose logs blogn2
   ```

2. **检查环境变量**
   ```bash
   docker-compose config
   ```

3. **检查数据库连接**
   ```bash
   docker-compose exec blogn2 python -c "
   import os
   from urllib.parse import urlparse
   url = os.getenv('DATABASE_URL')
   parsed = urlparse(url.replace('postgresql+asyncpg://', 'http://'))
   print(f'数据库主机: {parsed.hostname}:{parsed.port or 5432}')
   "
   ```

### 无法连接数据库

1. **检查网络连接**
   ```bash
   docker-compose exec blogn2 ping <数据库主机>
   ```

2. **检查端口**
   ```bash
   docker-compose exec blogn2 nc -zv <数据库主机> 5432
   ```

3. **检查 DATABASE_URL 格式**
   - 确保 URL 格式正确
   - 检查用户名、密码、主机、端口、数据库名

### 无法连接 Redis

1. **检查 Redis 连接**
   ```bash
   docker-compose exec blogn2 python -c "
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

### 模型下载失败

1. **检查网络连接**
   ```bash
   docker-compose exec blogn2 ping huggingface.co
   ```

2. **检查 MODEL_CACHE_DIR 权限**
   ```bash
   docker-compose exec blogn2 ls -la /app/.cache/models
   ```

3. **手动下载模型**（如果需要）
   - 在宿主机下载模型
   - 挂载到容器的 `MODEL_CACHE_DIR`

## 📊 性能优化

### 1. 使用多 worker

修改 `docker-compose.yml` 中的启动命令：

```yaml
command: ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
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

1. 查看日志：`cd docker && docker-compose logs blogn2`
2. 检查配置：`cd docker && docker-compose config`
3. 运行检查脚本：`cd docker && ./docker-check.sh`
4. 查看文档：参考项目文档
5. 提交 Issue：在 GitHub 上提交问题

---

**BlogN2** - 容器化部署，简单高效！ 🚀

