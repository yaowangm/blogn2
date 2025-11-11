# 缓存配置说明

## 环境变量配置

缓存系统现在支持通过环境变量 `CACHE_DEFAULT_TTL` 来配置默认缓存时间，而不是硬编码。

### 配置方式

在 `.env` 文件中添加以下配置：

```bash
# 默认缓存TTL（秒）
CACHE_DEFAULT_TTL=900
```

### TTL处理机制

系统使用现有的缓存机制来处理TTL：

1. **默认TTL**: 如果装饰器调用时不传入 `ttl` 参数，系统会自动使用 `cache_settings.default_ttl`
2. **自定义TTL**: 可以在装饰器调用时传入具体的 `ttl` 值来覆盖默认设置
3. **环境变量配置**: `cache_settings.default_ttl` 可以通过环境变量 `CACHE_DEFAULT_TTL` 进行配置

### 实际TTL示例

假设 `CACHE_DEFAULT_TTL=900`（15分钟）：

- **使用默认TTL**: `@cache_project_detail()` → 使用900秒
- **自定义TTL**: `@cache_project_detail(ttl=1800)` → 使用1800秒（30分钟）

### 当前API缓存配置

#### 项目相关API
- `/projects/{project_id}` - 长缓存（项目详情）
- `/projects/{project_id}/posts` - 中等缓存（文章列表）
- `/projects/{project_id}/comments/recent` - 短缓存（最近评论）
- `/projects/{project_id}/categories` - 长缓存（分类列表）
- `/projects/{project_id}/external-links` - 长缓存（外部链接）
- `/projects/{project_id}/rss` - 中等缓存（RSS订阅）
- `/projects/{project_id}/stats` - 短缓存（统计信息）
- `/projects/user/{user_id}` - 长缓存（用户项目）

#### RSS相关API
- `/rss/site` - 中等缓存（全站RSS）
- `/rss/blog/{project_id}` - 中等缓存（博客RSS）
- `/rss/site/full` - 中等缓存（完整全站RSS）
- `/rss/blog/{project_id}/full` - 中等缓存（完整博客RSS）

#### 友情链接API
- `/projects/{project_id}/friend-links` - 长缓存（项目友情链接）
- `/friend-links` - 长缓存（所有友情链接）

### 缓存键生成

系统使用统一的 `CacheKeyGenerator` 类来生成缓存键，确保键的一致性和唯一性：

#### 项目相关缓存键
- `project:detail:{project_id}` - 项目详情
- `project:posts:{project_id}:{page}:{page_size}:{post_type}` - 项目文章列表
- `project:comments:{project_id}:recent` - 项目评论
- `project:categories:{project_id}` - 项目分类
- `project:external_links:{project_id}` - 项目外部链接
- `project:rss:{project_id}` - 项目RSS
- `project:stats:{project_id}` - 项目统计
- `user:projects:{user_id}` - 用户项目

#### RSS相关缓存键
- `rss:site` - 站点RSS
- `rss:blog:{project_id}` - 博客RSS
- `rss:site:full` - 完整站点RSS
- `rss:blog:{project_id}:full` - 完整博客RSS

#### 友情链接相关缓存键
- `friend_links:project:{project_id}` - 项目友情链接
- `friend_links:all` - 所有友情链接

### 自定义TTL

如果需要为特定API设置自定义TTL，可以在装饰器中传入参数：

```python
@cache_project_detail(ttl=1800)  # 自定义30分钟缓存
async def get_project(project_id: int):
    # ...
```

### 配置建议

#### 开发环境
```bash
CACHE_DEFAULT_TTL=300  # 5分钟，便于调试
```

#### 生产环境
```bash
CACHE_DEFAULT_TTL=900  # 15分钟，平衡性能和实时性
```

#### 高并发环境
```bash
CACHE_DEFAULT_TTL=1800  # 30分钟，减少数据库压力
```

### 监控和调优

1. **监控缓存命中率**: 通过Redis监控工具查看缓存使用情况
2. **调整TTL**: 根据实际访问模式调整 `CACHE_DEFAULT_TTL`
3. **分析性能**: 观察数据库查询减少和响应时间改善

### 注意事项

- 修改 `CACHE_DEFAULT_TTL` 后需要重启应用才能生效
- 缓存时间过短可能导致频繁的数据库查询
- 缓存时间过长可能导致数据更新不及时
- 建议在生产环境中根据实际负载进行调优
