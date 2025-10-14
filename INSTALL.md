# BlogN2 安装指南

本文档详细描述如何在干净的Linux环境中安装和配置BlogN2博客系统。

## 系统要求

### 操作系统
- Linux发行版（推荐Ubuntu 24.04 LTS或类似版本）
- 64位架构

### 软件版本要求
- **Python**: 3.12.3
- **PostgreSQL**: 16.9
- **Redis**: 7.0.15
- **Git**: 用于代码下载

> **注意**: 本文档基于上述版本测试，不保证在其他版本下可以正常运行。

## 安装步骤

### 1. 更新系统包

```bash
sudo apt update
sudo apt upgrade -y
```

### 2. 安装系统依赖

```bash
# 安装基础开发工具
sudo apt install -y build-essential git curl wget

# 安装Python 3.12和相关工具
sudo apt install -y python3.12 python3.12-venv python3.12-dev python3-pip

# 安装PostgreSQL
sudo apt install -y postgresql postgresql-contrib postgresql-server-dev-16

# 安装Redis
sudo apt install -y redis-server

# 安装图片处理依赖
sudo apt install -y libjpeg-dev libpng-dev libfreetype6-dev

# 安装其他系统依赖
sudo apt install -y pkg-config libffi-dev libssl-dev
```

### 3. 配置PostgreSQL

```bash
# 启动PostgreSQL服务
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 切换到postgres用户
sudo -u postgres psql

# 在PostgreSQL中执行以下命令
CREATE USER blogn_user WITH PASSWORD 'blogn_password';
CREATE DATABASE blogn_example OWNER blogn_user;
GRANT ALL PRIVILEGES ON DATABASE blogn_example TO blogn_user;
\q
```

### 4. 配置Redis

```bash
# 启动Redis服务
sudo systemctl start redis-server
sudo systemctl enable redis-server

# 验证Redis运行状态
redis-cli ping
# 应该返回 PONG
```

### 5. 下载项目代码

```bash
# 克隆项目仓库
git clone https://github.com/yaowangm/blogn2.git
cd blogn2

# 查看项目结构
ls -la
```

### 6. 创建Python虚拟环境

```bash
# 创建虚拟环境
python3.12 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 升级pip
pip install --upgrade pip
```

### 7. 安装Python依赖

```bash
# 安装项目依赖
pip install -r requirements.txt
```

### 8. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置文件
nano .env
```

在`.env`文件中配置以下关键项：

```env
# 数据库配置
DATABASE_URL=postgresql+asyncpg://blogn_user:blogn_password@localhost:5432/blogn_example

# Redis配置
CACHE_REDIS_HOST=localhost
CACHE_REDIS_PORT=6379
CACHE_REDIS_PASSWORD=

# 应用配置
APP_ENV=development
DEBUG=true
SECRET_KEY=your-super-secret-jwt-key-change-in-production

# 文件上传配置
UPLOAD_DIR=../pic/blogn_img/upload
AVATAR_DIR=../pic/blogn_img/userlogo
```

### 9. 创建必要的目录

```bash
# 创建图片存储目录
mkdir -p ../pic/blogn_img/upload
mkdir -p ../pic/blogn_img/userlogo

# 设置目录权限
chmod 755 ../pic/blogn_img/upload
chmod 755 ../pic/blogn_img/userlogo
```

### 10. 初始化数据库

```bash
# 使用提供的SQL文件初始化数据库
psql -U blogn_user -d blogn_example -f data/blogn_example.sql

# 验证数据库初始化
psql -U blogn_user -d blogn_example -c "SELECT name, state FROM users WHERE name = 'admin';"
```

应该看到类似输出：
```
 name  | state 
-------+-------
 admin |    10
```

### 11. 安装pgvector扩展（用于向量搜索）

```bash
# 安装pgvector扩展
sudo apt install -y postgresql-16-pgvector

# 在数据库中启用扩展
psql -U blogn_user -d blogn_example -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### 12. 验证安装

```bash
# 测试数据库连接
python -c "
from src.database import create_engine
from sqlmodel import text
engine = create_engine('postgresql+psycopg2://blogn_user:blogn_password@localhost:5432/blogn_example')
with engine.connect() as conn:
    result = conn.execute(text('SELECT version()'))
    print('PostgreSQL连接成功:', result.fetchone()[0])
"

# 测试Redis连接
python -c "
import redis
r = redis.Redis(host='localhost', port=6379, db=0)
print('Redis连接成功:', r.ping())
"
```

### 13. 启动应用

```bash
# 确保在项目根目录
cd /path/to/blogn2

# 激活虚拟环境
source venv/bin/activate

# 启动应用
python run.py
```

如果一切正常，您应该看到类似输出：
```
🚀 启动 BlogN2 FastAPI 应用...
📍 访问地址:
   - 首页: http://localhost:8000
   - API文档: http://localhost:8000/docs
   - 健康检查: http://localhost:8000/health
   - 网站元数据: http://localhost:8000/api/metadata/
   - 用户统计: http://localhost:8000/api/users/summary
   - 最新用户: http://localhost:8000/api/users/listnew
   - 最新博客: http://localhost:8000/api/blogs/recent
   - 热门博客: http://localhost:8000/api/blogs/popular

INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

## 访问系统

### 默认管理员账户
- **用户名**: `admin`
- **密码**: `testpasswd`
- **权限**: 管理员

### 主要访问地址
- **首页**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

## 故障排除

### 常见问题

1. **数据库连接失败**
   ```bash
   # 检查PostgreSQL服务状态
   sudo systemctl status postgresql
   
   # 检查数据库用户权限
   sudo -u postgres psql -c "\du"
   ```

2. **Redis连接失败**
   ```bash
   # 检查Redis服务状态
   sudo systemctl status redis-server
   
   # 测试Redis连接
   redis-cli ping
   ```

3. **Python依赖安装失败**
   ```bash
   # 更新pip
   pip install --upgrade pip
   
   # 清理缓存重新安装
   pip cache purge
   pip install -r requirements.txt
   ```

4. **权限问题**
   ```bash
   # 检查图片目录权限
   ls -la ../pic/blogn_img/
   
   # 修复权限
   chmod -R 755 ../pic/blogn_img/
   ```

### 日志查看

```bash
# 查看应用日志
tail -f app.log

# 查看系统服务日志
sudo journalctl -u postgresql
sudo journalctl -u redis-server
```

## 开发环境配置

### 代码热重载
应用默认启用热重载，修改代码后会自动重启。

### 调试模式
在`.env`文件中设置`DEBUG=true`启用调试模式。

### 数据库管理
```bash
# 连接数据库
psql -U blogn_user -d blogn_example

# 查看表结构
\dt

# 查看用户表
SELECT * FROM users;
```

## 下一步

1. 访问 http://localhost:8000 查看系统首页
2. 使用管理员账户登录
3. 创建您的第一篇博客文章
4. 探索系统的各种功能

## 技术支持

如果遇到问题，请检查：
1. 所有服务是否正常运行
2. 环境变量配置是否正确
3. 数据库和Redis连接是否正常
4. 文件权限是否正确

---

**注意**: 这是一个开发环境配置，生产环境部署需要额外的安全配置和优化。
