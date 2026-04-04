# BlogN - 现代化博客平台

一个基于FastAPI和现代Web技术构建的高性能博客平台，支持用户管理、博客发布、评论系统、智能搜索等功能。

> **安装与配置**：环境要求、依赖安装、数据库初始化、BERT 模型等完整步骤请参阅 **[INSTALL.md](INSTALL.md)**。

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
- **前端工具**：`openConfirmDialog`、注册码格式化等说明见 [`src/static/js/utils/README.md`](src/static/js/utils/README.md)

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
│   │   ├── model.py             # 模型/BERT 配置（路径、设备等）
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

详细的**安装与配置步骤**（环境要求、克隆与依赖、数据库与 pgvector、BERT 模型、启动与验证等）请参考 **[INSTALL.md](INSTALL.md)**。

完成安装后执行 `python run.py` 启动应用。默认管理员账户：**用户名** `admin`，**密码** `testpasswd`。

## 🧪 测试

### 运行测试
```bash
# 激活虚拟环境（推荐）
source venv/bin/activate   # Linux/macOS；Windows: venv\Scripts\activate

# 运行所有测试
python -m pytest

# 仅运行单元测试（不包含需 BERT 的集成/性能测试）
python -m pytest tests/unit/

# 若未下载 BERT 模型，可跳过相关测试以避免失败
python -m pytest --ignore=tests/integration/test_bert_vectorization_with_real_db.py --ignore=tests/performance/test_bert_vectorization_performance.py
```

也可使用 `tests/run_tests.py`：`python tests/run_tests.py all`、`unit`、`integration`、`coverage`。

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
- `UPLOAD_DIR`: 文件上传目录（本地与 Docker 共用同一 .env：本地填宿主机路径；Docker 由 compose 覆盖为容器路径并挂载此处目录）
- `AVATAR_DIR`: 用户头像目录（同上，本地与 Docker 共用）
- `MODEL_MODEL_NAME`: Hugging Face 模型 ID（默认 `paraphrase-multilingual-MiniLM-L12-v2`）；无本地路径时按此名称下载，有本地路径时主要用于日志与回退。
- `MODEL_MODEL_PATH`: 容器内/本地模型路径（可选；Docker 下由 entrypoint 解析到挂载的 snapshot）
- `MODEL_DEVICE`: 运行设备，`auto`（默认）时仅当当前 GPU 在 PyTorch 编译支持列表内才用 CUDA，否则用 CPU；可显式设为 `cpu` 或 `cuda`。
- `MODEL_PREFER_LOCAL`: 是否优先使用本地模型

详细配置请参考 `.env.example` 文件；模型设备与 BERT 配置见 [doc/MODEL_CONFIGURATION.md](doc/MODEL_CONFIGURATION.md)。

## 📚 API文档

启动应用后，访问以下地址查看API文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 🔍 智能搜索功能

BlogN集成了基于BERT的智能搜索系统：

- **语义搜索**: 理解查询意图，返回相关结果
- **向量化存储**: 使用pgvector存储文本向量
- **混合搜索**: 结合语义搜索和关键词搜索
- **多语言支持**: 支持中文和英文搜索

### BERT 模型安装

智能搜索依赖 **sentence-transformers** 的多语言 BERT 模型（默认：`paraphrase-multilingual-MiniLM-L12-v2`）。首次使用前需下载模型，详见 [INSTALL.md](INSTALL.md) 中的「下载 BERT 模型」步骤。相关环境变量见 `.env.example` 中的 `MODEL_*` 配置。**Docker 部署**时宿主机模型目录在 `docker run` 的 `-v` 参数中指定（见上方「Docker run 参数说明」），挂载到容器内后 entrypoint 与应用会自动解析到含 `config.json` 的 snapshot 路径，详见 [docker/README-DOCKER.md](docker/README-DOCKER.md)。

## 🛡️ 权限管理

系统提供细粒度的权限控制：

- **用户角色**: 管理员、普通用户、冻结用户
- **权限矩阵**: 基于角色的权限分配
- **数据过滤**: 根据权限过滤敏感信息
- **装饰器支持**: 便捷的权限检查装饰器

## 📊 缓存系统

BlogN实现了完整的缓存系统：

- **自动缓存**: 使用装饰器自动缓存API响应
- **智能失效**: 基于数据变更的缓存失效
- **性能监控**: 实时缓存命中率统计
- **配置管理**: 环境变量配置缓存策略

## 📋 部署时需手动完成的事项

以下功能或配置需在部署环境中由管理员手动完成，代码与镜像中未自动完成：

### 邮件重置密码（sendmail）

| 步骤 | 说明 |
|------|------|
| **1. 安装 sendmail** | 宿主机安装：`sudo apt install sendmail`（Ubuntu/Debian） |
| **2. 配置 sendmail** | 编辑 `/etc/mail/sendmail.mc`，设置 `MASQUERADE_AS(bloggern.com)` 等使发件人域名与站点一致；执行 `sudo make -C /etc/mail` 后 `sudo systemctl restart sendmail` |
| **3. 环境变量** | 在 `.env` 中配置：`MAIL_FROM`、`RESET_LINK_EXPIRE_MINUTES`、`BASE_URL`；Docker 部署时另设 `SMTP_HOST=localhost`、`SMTP_PORT=25`（使用宿主机 sendmail） |
| **4. 创建重置令牌表** | 首次部署或升级后执行：`python scripts/init_db.py`，以创建 `password_reset_tokens` 表 |
| **5. DNS/SPF（可选）** | 在域名 DNS 中配置 SPF 记录（如 `v=spf1 ip4:发信服务器公网IP ~all`）以提高送达率、减少被判为垃圾邮件 |

### Docker 部署（宿主机 sendmail）

| 步骤 | 说明 |
|------|------|
| **宿主机运行 sendmail** | 宿主机安装并启动 sendmail，监听 25 端口（见上表） |
| **容器连宿主机 25 端口** | 使用 **host 网络**时，在配置中设置 `SMTP_HOST=localhost`、`SMTP_PORT=25`，容器内应用通过 SMTP 连接宿主机 25 端口发信，无需在容器内安装 sendmail |

详细设计见 [doc/EMAIL_PASSWORD_RESET_DESIGN.md](doc/EMAIL_PASSWORD_RESET_DESIGN.md)，Docker 部署见 [docker/README-DOCKER.md](docker/README-DOCKER.md)。

### Docker run 参数说明

以下参数均在 `docker run` 命令行中配置（`.env` 中的 `UPLOAD_DIR`、`AVATAR_DIR` 为宿主机路径，本地与 docker-compose 共用；`docker run` 时用下方 `-v` 挂载同一路径即可）。

| 参数 | 说明 |
|------|------|
| `--name blogn2-app` | 容器名称，便于 `docker logs` / `docker restart` 等操作 |
| `--restart unless-stopped` | 容器退出时自动重启（除非手动 stop），保证服务常驻 |
| `--network host` | 使用宿主机网络，容器内可直接访问本机 PostgreSQL、Redis、sendmail 等 |
| `-e BLOGN_CONFIG_FILE=/app/config.env` | 告知应用从挂载的配置文件读取环境变量（数据库、Redis、日志等） |
| `-v 宿主机路径/.env:/app/config.env:ro` | 将项目根目录的 `.env` 挂载为容器内配置文件，只读 |
| `-v 宿主机上传目录:/app/uploads` | 上传文件持久化，可与 .env 中 `UPLOAD_DIR` 一致 |
| `-v 宿主机头像目录:/app/avatars` | 用户头像持久化，可与 .env 中 `AVATAR_DIR` 一致 |
| `-v 宿主机HF缓存:/app/.cache/huggingface:ro` | Hugging Face 缓存（可选，若模型从宿主机挂载可省略） |
| `-v 宿主机ModelScope缓存:/app/.cache/modelscope:ro` | ModelScope 缓存（可选） |
| `-v 宿主机BERT模型目录:/app/.cache/models/bert-model-hub:ro` | BERT 模型 hub 目录（含 `snapshots/`），宿主机路径按本机实际修改；不挂载则无法使用智能搜索 |
| `blogn2-app` | 镜像名（需先 `docker build -f docker/Dockerfile -t blogn2-app .`） |

示例（宿主机路径请按本机修改）：

```bash
docker run -d \
  --name blogn2-app \
  --restart unless-stopped \
  --network host \
  -e BLOGN_CONFIG_FILE=/app/config.env \
  -v /home/wy/blogn2/.env:/app/config.env:ro \
  -v /home/wy/pic/blogn_img/upload:/app/uploads \
  -v /home/wy/pic/blogn_img/userlogo:/app/avatars \
  -v /home/wy/.cache/huggingface:/app/.cache/huggingface:ro \
  -v /home/wy/.cache/modelscope:/app/.cache/modelscope:ro \
  -v /home/wy/snap/models--sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2:/app/.cache/models/bert-model-hub:ro \
  blogn2-app
```

更多细节见 [docker/README-DOCKER.md](docker/README-DOCKER.md)。

---

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

本项目采用 BSD 3-Clause 许可证 - 查看 [BSD 3-Clause License](https://opensource.org/licenses/BSD-3-Clause) 了解详情。

### 第三方组件与致谢

- `.cursor/rules/analyze-pr-changes.mdc` 文件基于开源项目 [AI-PR-Reviewer-Tasks](https://github.com/holasoymalva/AI-PR-Reviewer-Tasks) 中的同名规则改编而来。原始项目由 `holasoymalva` 等贡献者维护，并在 **Apache License 2.0** 许可下发布。根据该许可条款，我们在此明确标注来源与许可证信息；完整许可证文本可参阅其仓库中的 `LICENSE` 文件或 [Apache License 2.0 官方页面](http://www.apache.org/licenses/LICENSE-2.0)。

## 📞 联系方式

- 项目主页: [GitHub Repository](https://github.com/yaowangm/blogn2)
- 问题反馈: [Issues](https://github.com/yaowangm/blogn2/issues)
- 功能建议: [Discussions](https://github.com/yaowangm/blogn2/discussions)

## 🎉 致谢

感谢所有为这个项目做出贡献的开发者和用户！

---

**BlogN** - 让博客创作更简单、更高效！ 🚀