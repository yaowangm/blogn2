# 缓存配置说明

## Redis 为可选加速器

BlogN2 **不依赖 Redis**。以下任一情况均与「无缓存」行为一致：直连数据库/API，端点正常响应，不报错。

- `CACHE_ENABLE_CACHE=false`（开发默认）
- Redis 未启动或连接失败
- 缓存读写异常（装饰器会记录日志并回退执行原函数）

启用缓存（`CACHE_ENABLE_CACHE=true`）且 Redis 可用时，热路径 API 由 Redis 加速。健康检查 `/health` 与 `/api/cache/status` 会报告 `cache_available`，**不会**因 Redis 不可用而导致健康检查失败。

## 环境变量配置

缓存系统通过环境变量 `CACHE_DEFAULT_TTL` 等配置 TTL 与开关，而不是在代码里硬编码。

### 配置方式

在 `.env` 文件中添加以下配置：

```bash
# 默认缓存 TTL（秒）
CACHE_DEFAULT_TTL=900

# 是否启用 Redis 缓存（生产环境建议 true）
CACHE_ENABLE_CACHE=true
```

### TTL 处理机制

1. **默认 TTL**：装饰器未传 `ttl` 时使用 `cache_settings.default_ttl`
2. **自定义 TTL**：装饰器可传入 `ttl=` 覆盖默认值
3. **环境变量**：`CACHE_DEFAULT_TTL` 控制默认 TTL

### 当前 API 缓存配置

#### 项目相关 API
- `/projects/{project_id}` — 项目详情
- `/projects/{project_id}/posts` — 文章列表（键含 `page`、`page_size`、`type`、`folder_id`、`include_deleted`）
- `/projects/{project_id}/comments/recent` — 最近评论
- `/projects/{project_id}/categories` — 分类列表
- `/projects/{project_id}/external-links` — 外部链接
- `/projects/{project_id}/rss` — 项目 RSS
- `/projects/{project_id}/stats` — 统计信息
- `/projects/user/{user_id}` — 用户项目列表

#### 博客目录 API
- `/blogs/recent` — 最新加入博客（`cache_blogs_joined_recent`，键含 `limit`）
- `/blogs/posts/latest` — 最新博文分页（`cache_blog_recent_list`，键含 `page`、`page_size`、`exclude`、`blogid`）
- `/blogs/popular` — 热门博客
- `/comments/recent` — 全站最近评论（`@cache_blog_comments()`，键含 `limit`）
- `/metadata/` — 站点元数据

#### 文章相关 API
- `/articles/{article_id}` — 文章详情（键含评论分页 `page`、`per_page`）
- `/articles/{article_id}/comments` — 评论列表（键含 `page`、`limit`）
- `/articles/{article_id}/attachments` — 附件列表

#### 搜索 API
- `/search` — 搜索结果（`@cache_search_results()`，键含 `q`、`page`、`type`、`sort`、`limit`）

#### 统计 API
- `/global-stats` — 全局统计（`@cache_global_stats()`，TTL 60 秒，键 `stats:global`）

#### RSS 相关 API
- `/rss/site`、`/rss/blog/{project_id}` 及对应 `/full` 端点

RSS 在 service 层缓存 **XML 字符串**（`build_*_rss_xml` 返回 `str`），再包装为 `Response`；避免对 `StarletteResponse` 直接缓存导致缓存永不命中。

### 缓存键生成

系统使用 `CacheKeyGenerator`（`src/config/cache.py`）生成键，经 `_ensure_cache_prefix` 加上 `CACHE_CACHE_PREFIX`（默认 `blogn2`）。

#### 项目相关
- `project:detail:{project_id}`
- `project:posts:{project_id}:{page}:{page_size}:{post_type}:{folder_id|all}:{active|deleted}`
- `project:comments:{project_id}:recent:{limit}`
- `blog:comments:recent:{limit}` — 全站最近评论
- `project:categories:{project_id}`
- `project:rss:{project_id}:{limit}`
- `project:stats:{project_id}`

#### 博客 / 文章
- `blog:recent:joined:{limit}` — `/blogs/recent`
- `blog:recent:list:{page}:{page_size}:{exclude}:{blogid}` — `/blogs/posts/latest`
- `article:detail:{article_id}:{page}:{per_page}`
- `article:comments:{article_id}:{page}:{limit}`

#### RSS
- `rss:site:{limit}` / `rss:site:full:{limit}`
- `rss:blog:{project_id}:{limit}` / `rss:blog:{project_id}:full:{limit}`

#### 搜索 / 统计 / 元数据
- `search:{query}:{page}:{type}:{sort}:{limit}`
- `stats:global`
- `metadata:site`

### 自定义 TTL 示例

```python
@cache_project_detail(ttl=1800)
async def get_project(project_id: int):
    ...
```

### 配置建议

| 环境 | `CACHE_DEFAULT_TTL` | `CACHE_ENABLE_CACHE` |
|------|---------------------|----------------------|
| 开发 | 300（5 分钟） | 按需 |
| 生产 | 900（15 分钟） | **true** |
| 高并发 | 1800（30 分钟） | **true** |

### 注意事项

- 修改缓存相关环境变量后需重启应用
- `CACHE_ENABLE_CACHE=false` 或 Redis 不可用时，所有 `@cache_*` 装饰器跳过读写并直接执行原函数
- 缓存键必须包含所有影响响应的查询参数，避免不同请求互相覆盖
