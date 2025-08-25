# BlogN2 - 现代化博客平台

一个基于FastAPI和现代Web技术构建的高性能博客平台，支持用户管理、博客发布、评论系统等功能。

## 🚀 主要特性

- **高性能后端**: 基于FastAPI框架，支持异步操作
- **智能缓存系统**: Redis后端缓存，显著提升性能
- **现代化前端**: Web Components架构，响应式设计
- **用户管理系统**: 完整的用户注册、登录、资料管理
- **博客发布系统**: 支持富文本编辑、分类管理
- **评论互动**: 实时评论系统，支持回复功能
- **文件管理**: 安全的文件上传和头像管理
- **RESTful API**: 完整的API文档和测试支持

## 📋 开发规则

### Git操作规则
- **绝对禁止自动提交**: 任何AI助手都不得在没有用户明确要求的情况下进行git commit或push操作
- **必须等待明确指示**: 即使代码修改完成，也必须等待用户明确指示才能进行git操作
- **保守原则**: 如果不确定是否需要git操作，选择不执行

### 代码修改规则
- 优先使用装饰器替代内联权限检查
- 保持代码简洁和一致性
- 每次修改后都要进行测试验证

## 🏗️ 技术架构

### 后端技术栈
- **FastAPI**: 现代、快速的Web框架
- **SQLModel**: 基于Pydantic的ORM
- **PostgreSQL**: 主数据库
- **Redis**: 缓存和会话存储
- **Uvicorn**: ASGI服务器

### 前端技术栈
- **Web Components**: 原生组件系统
- **现代CSS**: CSS变量、Grid、Flexbox
- **原生JavaScript**: ES6+特性
- **响应式设计**: 移动优先的设计理念

### 缓存系统
- **Redis后端**: 高性能缓存存储
- **智能装饰器**: 自动缓存管理
- **缓存统计**: 实时性能监控
- **失效策略**: 智能缓存更新

## 📁 项目结构

```
blogn2/
├── src/                          # 源代码目录
│   ├── config/                   # 配置模块
│   │   └── cache.py             # 缓存配置
│   ├── controllers/              # API控制器
│   │   ├── blog.py              # 博客控制器
│   │   ├── user.py              # 用户控制器
│   │   ├── metadata.py          # 元数据控制器
│   │   ├── project.py           # 项目控制器
│   │   └── urllink.py           # 链接控制器
│   ├── models/                   # 数据模型
│   ├── repositories/             # 数据访问层
│   ├── services/                 # 业务逻辑层
│   ├── utils/                    # 工具模块
│   │   └── cache.py             # 缓存工具
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
│   ├── test_redis.py            # Redis测试脚本
│   └── test_config.py           # 配置测试脚本
├── docs/                         # 文档目录
├── requirements.txt              # Python依赖
├── env.example                   # 环境变量模板
└── README.md                     # 项目说明
```

## 🚀 快速开始

### 1. 环境要求

- Python 3.8+
- PostgreSQL 12+
- Redis 6+
- Node.js 16+ (可选，用于前端构建)

### 2. 安装依赖

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

### 3. 环境配置

```bash
# 复制环境变量模板
cp env.example .env

# 编辑 .env 文件，配置数据库和Redis连接信息
```

### 4. 数据库设置

```bash
# 创建数据库
createdb blogn2

# 运行数据库迁移（如果有）
# python -m alembic upgrade head
```

### 5. 启动应用

```bash
# 启动Redis服务
redis-server

# 启动应用
python src/main.py

# 或使用uvicorn
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. 访问应用

- 首页: http://localhost:8000/
- API文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

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

# 清理测试文件
python tests/run_tests.py clean
```

### 测试Redis连接

```bash
python scripts/test_redis.py
```

### 测试配置

```bash
python scripts/test_config.py
```

## 📊 缓存系统

BlogN2实现了完整的缓存系统，支持：

- **自动缓存**: 使用装饰器自动缓存API响应
- **智能失效**: 基于数据变更的缓存失效
- **性能监控**: 实时缓存命中率统计
- **配置管理**: 环境变量配置缓存策略

### 缓存装饰器示例

```python
from src.utils.cache import cache_blog_list

@cache_blog_list(ttl=1800)  # 缓存30分钟
async def get_blog_list(page: int = 1, limit: int = 10):
    return await blog_service.get_blog_list(page, limit)
```

## 🔧 配置说明

### 环境变量

主要配置项包括：

- `DATABASE_URL`: PostgreSQL数据库连接URL
- `CACHE_REDIS_HOST`: Redis服务器地址
- `CACHE_ENABLE_CACHE`: 是否启用缓存
- `CACHE_DEFAULT_TTL`: 默认缓存时间
- `APP_ENV`: 应用环境

详细配置请参考 `env.example` 文件。

## 📚 API文档

启动应用后，访问以下地址查看API文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 🚨 注意事项

1. **安全配置**: 生产环境请修改默认密钥和配置
2. **数据库备份**: 定期备份数据库数据
3. **Redis监控**: 监控Redis内存使用情况
4. **日志管理**: 配置适当的日志级别和轮转策略

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 联系方式

- 项目主页: [GitHub Repository]
- 问题反馈: [Issues]
- 功能建议: [Discussions]

## 🎉 致谢

感谢所有为这个项目做出贡献的开发者和用户！

---

**BlogN2** - 让博客创作更简单、更高效！ 🚀 