# BlogN2 - 现代化博客平台

一个基于FastAPI和现代Web技术构建的高性能博客平台，支持用户管理、博客发布、评论系统、智能搜索等功能。

## 🚀 主要特性

- **高性能后端**: 基于FastAPI框架，支持异步操作
- **智能缓存系统**: Redis后端缓存，显著提升性能
- **现代化前端**: Web Components架构，响应式设计
- **用户管理系统**: 完整的用户注册、登录、资料管理
- **博客发布系统**: 支持富文本编辑、分类管理
- **评论互动**: 实时评论系统，支持回复功能
- **文件管理**: 安全的文件上传和头像管理
- **智能搜索**: 基于BERT的语义搜索和向量化
- **权限管理**: 细粒度的权限控制系统
- **RESTful API**: 完整的API文档和测试支持

## 🏗️ 技术架构

### 后端技术栈
- **FastAPI**: 现代、快速的Web框架
- **SQLModel**: 基于Pydantic的ORM
- **PostgreSQL**: 主数据库，支持pgvector扩展
- **Redis**: 缓存和会话存储
- **Uvicorn**: ASGI服务器
- **BERT**: 语义搜索和文本向量化

### 前端技术栈
- **Web Components**: 原生组件系统
- **现代CSS**: CSS变量、Grid、Flexbox
- **原生JavaScript**: ES6+特性
- **响应式设计**: 移动优先的设计理念
- **Material 3**: 现代化UI设计风格

### 智能搜索系统
- **pgvector**: PostgreSQL向量扩展
- **sentence-transformers**: 多语言BERT模型
- **语义搜索**: 基于向量相似度的智能搜索
- **全文搜索**: 传统关键词搜索
- **混合搜索**: 结合语义和关键词的搜索策略

## 📁 项目结构

```
blogn2/
├── src/                          # 源代码目录
│   ├── config/                   # 配置模块
│   │   ├── app.py               # 应用配置
│   │   ├── cache.py             # 缓存配置
│   │   └── permissions.py       # 权限配置
│   ├── controllers/              # API控制器
│   │   ├── auth.py              # 认证控制器
│   │   ├── blog.py              # 博客控制器
│   │   ├── user.py              # 用户控制器
│   │   ├── metadata.py          # 元数据控制器
│   │   ├── project.py           # 项目控制器
│   │   └── urllink.py           # 链接控制器
│   ├── models/                   # 数据模型
│   │   ├── user.py              # 用户模型
│   │   ├── project_item.py      # 项目条目模型
│   │   ├── post.py              # 文章模型
│   │   └── auth.py              # 认证模型
│   ├── repositories/             # 数据访问层
│   │   ├── user_repository.py   # 用户数据访问
│   │   ├── project_repository.py # 项目数据访问
│   │   ├── post_repository.py   # 文章数据访问
│   │   └── subscription_repository.py # 订阅数据访问
│   ├── services/                 # 业务逻辑层
│   │   ├── blog_service.py      # 博客业务逻辑
│   │   ├── auth_service.py      # 认证业务逻辑
│   │   └── vectorization_service.py # 向量化服务
│   ├── utils/                    # 工具模块
│   │   ├── cache.py             # 缓存工具
│   │   ├── permission_manager.py # 权限管理
│   │   ├── file_handlers.py     # 文件处理
│   │   └── api_handlers.py      # API处理
│   ├── static/                   # 静态资源
│   │   ├── index.html           # 首页
│   │   ├── blog.html            # 博客页面
│   │   ├── css/                 # 样式文件
│   │   └── js/                  # JavaScript文件
│   ├── database.py              # 数据库配置
│   └── main.py                  # 主应用入口
├── tests/                        # 测试目录
│   ├── unit/                    # 单元测试
│   ├── integration/             # 集成测试
│   └── run_tests.py             # 测试运行脚本
├── scripts/                      # 脚本目录
│   ├── create_admin_user.py     # 管理员用户创建脚本
│   ├── batch_vectorization.py   # 批量向量化脚本
│   └── test_*.py                # 各种测试脚本
├── data/                         # 数据文件
│   └── blogn_example.sql        # 示例数据库结构
├── doc/                          # 文档目录
│   ├── DATABASE_SCHEMA.md       # 数据库架构文档
│   ├── PERMISSION_SYSTEM_README.md # 权限系统文档
│   └── README_*.md              # 各种功能文档
├── requirements.txt              # Python依赖
├── .env.example                  # 环境变量模板
├── INSTALL.md                    # 详细安装指南
├── run.py                        # 应用启动脚本
└── README.md                     # 项目说明
```

## 🚀 快速开始

### 环境要求

- **Python**: 3.12.3
- **PostgreSQL**: 16.9 (支持pgvector扩展)
- **Redis**: 7.0.15
- **Git**: 用于代码下载

> **注意**: 本文档基于上述版本测试，不保证在其他版本下可以正常运行。

### 安装步骤

详细的安装指南请参考 [INSTALL.md](INSTALL.md) 文件。

#### 1. 克隆项目
```bash
git clone https://github.com/yaowangm/blogn2.git
cd blogn2
```

#### 2. 创建虚拟环境
```bash
python3.12 -m venv venv
source venv/bin/activate
```

#### 3. 安装依赖
```bash
pip install -r requirements.txt
```

#### 4. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库和Redis连接信息
```

#### 5. 初始化数据库
```bash
# 创建数据库和用户
psql -U postgres -c "CREATE USER blogn_user WITH PASSWORD 'blogn_password';"
psql -U postgres -c "CREATE DATABASE blogn_example OWNER blogn_user;"

# 导入示例数据
psql -U blogn_user -d blogn_example -f data/blogn_example.sql
```

#### 6. 启动应用
```bash
python run.py
```

### 默认管理员账户

- **用户名**: `admin`
- **密码**: `testpasswd`
- **权限**: 管理员

## 🧪 测试

### 运行测试
```bash
# 运行所有测试
python tests/run_tests.py all

# 运行单元测试
python tests/run_tests.py unit

# 运行集成测试
python tests/run_tests.py integration

# 生成覆盖率报告
python tests/run_tests.py coverage
```

### 测试特定功能
```bash
# 测试Redis连接
python scripts/test_redis.py

# 测试配置
python scripts/test_config.py

# 测试数据库连接
python test_db.py
```

## 🔧 配置说明

### 环境变量

主要配置项包括：

- `DATABASE_URL`: PostgreSQL数据库连接URL
- `CACHE_REDIS_HOST`: Redis服务器地址
- `CACHE_ENABLE_CACHE`: 是否启用缓存
- `CACHE_DEFAULT_TTL`: 默认缓存时间
- `UPLOAD_DIR`: 文件上传目录
- `AVATAR_DIR`: 用户头像目录
- `MODEL_MODEL_NAME`: BERT模型名称
- `APP_ENV`: 应用环境

详细配置请参考 `.env.example` 文件。

## 📚 API文档

启动应用后，访问以下地址查看API文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 🔍 智能搜索功能

BlogN2集成了基于BERT的智能搜索系统：

- **语义搜索**: 理解查询意图，返回相关结果
- **向量化存储**: 使用pgvector存储文本向量
- **混合搜索**: 结合语义搜索和关键词搜索
- **多语言支持**: 支持中文和英文搜索

## 🛡️ 权限管理

系统提供细粒度的权限控制：

- **用户角色**: 管理员、普通用户、冻结用户
- **权限矩阵**: 基于角色的权限分配
- **数据过滤**: 根据权限过滤敏感信息
- **装饰器支持**: 便捷的权限检查装饰器

## 📊 缓存系统

BlogN2实现了完整的缓存系统：

- **自动缓存**: 使用装饰器自动缓存API响应
- **智能失效**: 基于数据变更的缓存失效
- **性能监控**: 实时缓存命中率统计
- **配置管理**: 环境变量配置缓存策略

## 🚨 注意事项

1. **安全配置**: 生产环境请修改默认密钥和配置
2. **数据库备份**: 定期备份数据库数据
3. **Redis监控**: 监控Redis内存使用情况
4. **日志管理**: 配置适当的日志级别和轮转策略
5. **文件权限**: 确保上传目录有正确的读写权限

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 联系方式

- 项目主页: [GitHub Repository](https://github.com/yaowangm/blogn2)
- 问题反馈: [Issues](https://github.com/yaowangm/blogn2/issues)
- 功能建议: [Discussions](https://github.com/yaowangm/blogn2/discussions)

## 🎉 致谢

感谢所有为这个项目做出贡献的开发者和用户！

---

**BlogN2** - 让博客创作更简单、更高效！ 🚀