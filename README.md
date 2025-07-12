# BlogN2 - FastAPI 博客系统

一个基于 FastAPI 的现代化博客系统。

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制环境变量模板文件：

```bash
cp .env.example .env
```

编辑 `.env` 文件，设置数据库连接信息：

```bash
# 数据库配置
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/database_name
```

**重要**: 请确保将实际的数据库连接信息填入 `.env` 文件中，不要使用示例中的占位符。

### 3. 启动应用

```bash
python run.py
```

或者直接运行：

```bash
cd src
python main.py
```

### 3. 访问应用

启动后，你可以访问以下地址：

- **首页**: http://localhost:8000
- **测试页面**: http://localhost:8000/api/test
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

## 项目结构

```
blogn2/
├── src/
│   ├── main.py              # FastAPI 主应用
│   └── routes/
│       ├── __init__.py
│       └── test.py          # 测试路由
├── requirements.txt         # 项目依赖
├── run.py                  # 启动脚本
└── README.md              # 项目说明
```

## API 端点

### 基础端点

- `GET /` - 首页
- `GET /health` - 健康检查

### 测试端点

- `GET /api/test` - 测试页面（HTML）
- `GET /api/test/json` - 测试数据（JSON）
- `GET /api/test/error` - 测试错误处理

## 技术栈

- **FastAPI** - 现代、快速的 Web 框架
- **Uvicorn** - 轻量级 ASGI 服务器
- **SQLModel** - 结合 SQLAlchemy 和 Pydantic 的 ORM
- **AsyncPG** - 高性能异步 PostgreSQL 驱动

## 开发

应用支持热重载，修改代码后会自动重启服务器。

## 下一步

- [ ] 添加数据库连接
- [ ] 实现用户认证
- [ ] 添加博客文章管理
- [ ] 实现评论系统 