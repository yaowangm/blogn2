# BlogN 安装指南

本文档详细描述如何在干净的Linux环境中安装和配置BlogN博客系统。

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
DEBUG=true
SECRET_KEY=your-super-secret-jwt-key-change-in-production

# 文件上传配置（本地与 Docker 共用：填宿主机路径；Docker 由 compose 覆盖并挂载）
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

### 12. 下载 BERT 模型（智能搜索，可选）

使用语义搜索或运行 BERT 相关测试前，需先下载模型（约 400MB，仅首次需要）：

```bash
# 确保已激活虚拟环境
source venv/bin/activate

# 下载默认模型到缓存目录（默认 ~/.cache/huggingface/hub）
python -c "
from sentence_transformers import SentenceTransformer
SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
print('BERT 模型下载完成')
"
```

- **MODEL_MODEL_NAME**（`.env` 中可选）：Hugging Face 上的模型 ID（默认 `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`）。当未配置本地模型路径或本地路径不可用时，应用会按此名称从 Hugging Face 下载模型；若已通过挂载使用本地模型，则主要用于日志与回退名称。
- **MODEL_MODEL_PATH**（可选）：本地/容器内模型目录（需含 `config.json`）。设置且 `MODEL_PREFER_LOCAL=true` 时优先使用本地模型。Docker 下宿主机模型目录**不通过 .env 配置**，由 `docker run -v` 或 compose 的 volume 指定。
- **MODEL_DEVICE**（可选，默认 `auto`）：`auto` 时根据 `torch.cuda.get_arch_list()` 与当前 GPU 的 compute capability 判断，仅当当前 GPU 架构在 PyTorch 编译支持列表内才使用 CUDA，否则自动使用 CPU，避免 "no kernel image" 等错误；可显式设置 `cpu` 或 `cuda`。
- **缓存目录**：默认 `~/.cache/huggingface/hub`，需对该目录有写权限；可在 `.env` 中设置 `MODEL_CACHE_DIR` 指定其他目录。
- **网络**：若无法直连 Hugging Face，可配置 `HF_ENDPOINT` 使用镜像，或将他人已下载的 `MODEL_CACHE_DIR` 目录拷贝到本机。
- **Docker 部署**：宿主机模型目录在 `docker run` 的 `-v` 参数中指定（见本文档「Docker 部署」一节），挂载到容器内后由 entrypoint 与应用自动解析到 snapshot，详见 [docker/README-DOCKER.md](docker/README-DOCKER.md)。
- 不使用智能搜索或暂不跑 BERT 相关测试时可跳过本步。

### 13. 验证安装

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

### 14. 启动应用

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
🚀 启动 BlogN FastAPI 应用...
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

## 使用初始管理员账户

### 1. 登录系统

1. 打开浏览器，访问 http://localhost:8000
2. 在页面右上角找到"登录"按钮，点击进入登录页面
3. 输入以下信息：
   - **用户名**: `admin`
   - **密码**: `testpasswd`
4. 点击"登录"按钮

### 2. 验证管理员权限

登录成功后，您应该能看到：
- 页面右上角显示"admin"用户名
- 导航菜单中包含管理员专用功能
- 可以访问用户管理、系统设置等高级功能

### 3. 首次使用建议

1. **修改密码**：
   - 登录后立即修改默认密码
   - 进入个人资料页面更新密码

2. **创建博客**：
   - 使用"创建文章"功能发布第一篇博客
   - 测试图片上传和附件功能

3. **用户管理**：
   - 查看用户列表
   - 创建新用户账户
   - 管理用户权限

4. **系统配置**：
   - 检查系统设置
   - 配置网站基本信息
   - 管理友情链接等

### 4. 常见登录问题

如果无法登录，请检查：

1. **数据库连接**：
   ```bash
   # 验证admin用户是否存在
   psql -U blogn_user -d blogn_example -c "SELECT name, state FROM users WHERE name = 'admin';"
   ```

2. **密码验证**：
   ```bash
   # 使用提供的脚本验证密码
   python scripts/create_admin_user.py --dry-run
   ```

3. **应用日志**：
   ```bash
   # 查看应用日志
   tail -f app.log
   ```

### Docker 部署（可选）

若使用 Docker 运行应用，以下参数在 `docker run` 命令行中配置（**不要**把 `BLOGN_CONFIG_FILE` 等写入 `.env`）。**.env 中的 `UPLOAD_DIR`、`AVATAR_DIR` 为宿主机路径**：使用 **docker-compose** 时 compose 会据此挂载并覆盖为容器路径；使用 **docker run** 时需用下表中的 `-e`、`-v` 覆盖并挂载。

| 参数 | 说明 |
|------|------|
| `--name blogn2-app` | 容器名称 |
| `--restart unless-stopped` | 退出时自动重启（除非手动 stop） |
| `--network host` | 使用宿主机网络，访问本机 PostgreSQL、Redis、sendmail |
| `-e BLOGN_CONFIG_FILE=/app/config.env` | 应用从该路径读取配置（即下方挂载的 .env） |
| `-v 宿主机/.env:/app/config.env:ro` | 将项目根目录 `.env` 挂载为容器内配置文件，只读 |
| `-v 宿主机上传目录:/app/uploads` | 上传文件持久化（可与 .env 中 UPLOAD_DIR 一致） |
| `-v 宿主机头像目录:/app/avatars` | 用户头像持久化（可与 .env 中 AVATAR_DIR 一致） |
| `-v 宿主机HF缓存:/app/.cache/huggingface:ro` | Hugging Face 缓存（可选） |
| `-v 宿主机ModelScope缓存:/app/.cache/modelscope:ro` | ModelScope 缓存（可选） |
| `-v 宿主机BERT模型目录:/app/.cache/models/bert-model-hub:ro` | BERT 模型 hub 目录（含 `snapshots/`），不挂载则无法使用智能搜索 |
| `blogn2-app` | 镜像名（需先执行 `docker build -f docker/Dockerfile -t blogn2-app .`） |

示例（宿主机路径请按本机修改）：

```bash
docker run -d \
  --name blogn2-app \
  --restart unless-stopped \
  --network host \
  -e BLOGN_CONFIG_FILE=/app/config.env \
  -v /path/to/blogn2/.env:/app/config.env:ro \
  -v /path/to/upload:/app/uploads \
  -v /path/to/avatars:/app/avatars \
  -v /path/to/.cache/huggingface:/app/.cache/huggingface:ro \
  -v /path/to/.cache/modelscope:/app/.cache/modelscope:ro \
  -v /path/to/models--sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2:/app/.cache/models/bert-model-hub:ro \
  blogn2-app
```

更多细节见 [docker/README-DOCKER.md](docker/README-DOCKER.md)。

### 5. 重置管理员密码（如需要）

如果忘记密码或需要重置，可以使用提供的脚本：

```bash
# 激活虚拟环境
source venv/bin/activate

# 重置admin用户密码
python scripts/create_admin_user.py -u admin -p newpassword -f
```

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
