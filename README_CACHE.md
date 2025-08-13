# FastAPI-Cache2 + Redis 缓存系统

本项目实现了基于FastAPI-Cache2和Redis的缓存机制，提供高性能的数据缓存功能。经过重构优化，代码质量、可读性和可维护性得到显著提升。

## 🚀 功能特性

- **自动缓存**: 使用装饰器自动缓存API响应
- **灵活配置**: 支持环境变量配置Redis连接和缓存策略
- **缓存统计**: 提供缓存命中率和使用统计
- **缓存管理**: 支持手动清除缓存和查看缓存状态
- **调试模式**: 支持缓存调试日志
- **重构优化**: 代码重构后提升性能和可维护性

## 📦 依赖安装

```bash
pip install fastapi-cache2==0.2.1 redis==5.0.1 aioredis==2.0.1
```

## ⚙️ 配置说明

### 环境变量配置

1. **复制环境变量模板**：
   ```bash
   cp .env.example .env
   ```

2. **编辑 `.env` 文件**，配置以下参数：

```env
# Redis缓存配置
CACHE_REDIS_HOST=localhost      # Redis服务器地址
CACHE_REDIS_PORT=6379          # Redis服务器端口
CACHE_REDIS_DB=0               # Redis数据库编号
CACHE_REDIS_PASSWORD=          # Redis密码（可选，留空表示无密码）
CACHE_REDIS_SSL=false          # 是否使用SSL连接Redis

# 缓存设置
CACHE_ENABLE_CACHE=true        # 是否启用缓存功能
CACHE_CACHE_DEBUG=false        # 是否启用缓存调试模式
CACHE_DEFAULT_TTL=600          # 默认缓存时间（秒，10分钟）
CACHE_MAX_TTL=86400            # 最大缓存时间（秒，24小时）
CACHE_CACHE_PREFIX=blogn2      # 缓存键前缀
```

### 配置验证

启动应用时，系统会自动从 `.env` 文件加载配置。如果配置有问题，可以：

1. **检查配置加载**：
   ```python
   from src.config.cache import validate_cache_config
   config_info = validate_cache_config()
   print(config_info)
   ```

2. **启用调试模式**：
   在 `.env` 文件中设置 `CACHE_CACHE_DEBUG=true`，启动时会打印配置信息

3. **使用配置测试脚本**：
   ```bash
   python scripts/test_config.py
   ```

### 配置参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `CACHE_REDIS_HOST` | localhost | Redis服务器地址 |
| `CACHE_REDIS_PORT` | 6379 | Redis服务器端口 |
| `CACHE_REDIS_DB` | 0 | Redis数据库编号 |
| `CACHE_REDIS_PASSWORD` | - | Redis密码（可选） |
| `CACHE_REDIS_SSL` | false | 是否使用SSL连接 |
| `CACHE_ENABLE_CACHE` | true | 是否启用缓存 |
| `CACHE_CACHE_DEBUG` | false | 是否启用调试模式 |
| `CACHE_DEFAULT_TTL` | 600 | 默认缓存时间（秒，10分钟） |
| `CACHE_MAX_TTL` | 86400 | 最大缓存时间（秒，24小时） |
| `CACHE_CACHE_PREFIX` | blogn2 | 缓存键前缀 |

## 🔧 使用方法

### 1. 基本缓存装饰器

```python
from src.utils.cache import cache_decorator

@cache_decorator()  # 使用默认缓存时间（10分钟）
async def get_user_data(user_id: int):
    # 你的业务逻辑
    return user_data

# 或者指定自定义缓存时间
@cache_decorator(ttl=1800)  # 缓存30分钟
async def get_user_data_custom_ttl(user_id: int):
    return user_data
```

### 2. 预定义缓存装饰器

```python
from src.utils.cache import cache_user_profile, cache_blog_list

# 用户资料缓存（使用默认缓存时间10分钟）
@cache_user_profile()
async def get_user_profile(user_id: int):
    return user_profile

# 博客列表缓存（使用默认缓存时间10分钟）
@cache_blog_list()
async def get_blog_list(page: int = 1, limit: int = 10):
    return blog_list

# 或者指定自定义缓存时间
@cache_user_profile(ttl=1800)  # 缓存30分钟
async def get_user_profile_custom_ttl(user_id: int):
    return user_profile
```

### 3. 缓存失效装饰器

```python
from src.utils.cache import invalidate_user_cache

@invalidate_user_cache()
async def update_user_profile(user_id: int):
    # 更新用户资料后自动清除相关缓存
    return updated_profile
```

## 📊 缓存统计

### 查看缓存状态

```bash
curl http://localhost:8000/api/cache/status
```

响应示例：
```json
{
  "cache_enabled": true,
  "cache_available": true,
  "cache_debug": false,
  "stats": {
    "hits": 150,
    "misses": 25,
    "sets": 175,
    "deletes": 10,
    "total_requests": 175,
    "hit_rate": 85.71
  }
}
```

### 查看缓存统计

```bash
curl http://localhost:8000/api/cache/stats
```

### 清除缓存

```bash
curl -X POST http://localhost:8000/api/cache/clear
```

## 🧪 测试缓存系统

### 1. 测试配置加载

```bash
python scripts/test_config.py
```

### 2. 测试Redis连接

```bash
python scripts/test_redis.py
```

### 3. 完整性能测试

```bash
python scripts/final_cache_performance_test.py
```

### 4. 测试API缓存

```bash
# 第一次请求（缓存未命中）
curl http://localhost:8000/api/blogs/recent

# 第二次请求（缓存命中）
curl http://localhost:8000/api/blogs/recent
```

## 📁 项目结构

```
src/
├── config/
│   └── cache.py          # 缓存配置（重构优化）
├── utils/
│   └── cache.py          # 缓存工具和装饰器（重构优化）
├── controllers/
│   ├── blog.py           # 博客控制器（已添加缓存）
│   ├── user.py           # 用户控制器（已添加缓存）
│   └── metadata.py       # 元数据控制器（已添加缓存）
└── main.py               # 主应用（已集成缓存）

scripts/
├── final_cache_performance_test.py  # 完整性能测试脚本
├── test_config.py                   # 配置验证测试
└── test_redis.py                    # Redis连接测试

docs/
├── CACHE_REFACTORING_SUMMARY.md     # 重构总结文档
├── CACHE_TESTING_SUMMARY.md         # 测试工具说明
└── README_CACHE.md                  # 本文档
```

## 🔍 缓存键策略

系统使用以下缓存键策略：

- **用户相关**: `user:profile:{user_id}`, `user:blogs:{user_id}:{page}`
- **博客相关**: `blog:list:{page}:{limit}`, `blog:detail:{blog_id}`, `blog:comments:{blog_id}`
- **搜索相关**: `search:{query}:{page}`
- **元数据**: `metadata:site`

## 🚨 注意事项

1. **Redis服务**: 确保Redis服务正在运行
2. **内存使用**: 监控Redis内存使用情况
3. **缓存失效**: 重要数据更新后及时清除相关缓存
4. **调试模式**: 生产环境建议关闭调试模式

## 🔧 故障排除

### Redis连接失败

1. 检查Redis服务是否运行：
   ```bash
   redis-cli ping
   ```

2. 检查Redis配置：
   ```bash
   redis-cli config get bind
   redis-cli config get port
   ```

3. 测试连接：
   ```bash
   python scripts/test_redis.py
   ```

### 缓存不生效

1. 检查缓存是否启用：
   ```bash
   curl http://localhost:8000/api/cache/status
   ```

2. 检查环境变量配置
3. 查看应用日志

## 📈 性能优化建议

1. **合理设置TTL**: 根据数据更新频率设置合适的缓存时间
2. **使用缓存前缀**: 避免键冲突
3. **监控缓存命中率**: 定期检查缓存效果
4. **设置最大TTL**: 防止缓存过期时间过长

## 🔄 版本更新

- **v1.0.0**: 初始版本，支持基本缓存功能
- 支持FastAPI-Cache2和Redis
- 提供缓存装饰器和统计功能
- 集成到现有API控制器

- **v2.0.0**: 重构优化版本（当前版本）
- 代码重构，提升可读性和可维护性
- 减少约8-10%的代码量
- 减少约25%的重复逻辑
- 新增完整的性能测试工具
- 优化缓存键生成和错误处理逻辑

## 🎯 重构成果

### 代码质量提升
- **可读性**: 函数职责更加单一，逻辑更清晰
- **可维护性**: 减少重复代码，便于统一修改
- **可扩展性**: 公共函数便于复用，易于添加新功能
- **健壮性**: 统一的错误处理，更好的异常管理

### 性能优化
- **内存使用**: 减少重复的字符串操作
- **执行效率**: 优化缓存键生成逻辑
- **资源管理**: 更好的连接和资源管理

### 新增功能
- **性能测试工具**: 完整的缓存性能测试脚本
- **配置验证**: 自动配置检查和验证
- **Redis测试**: 连接和功能测试工具
- **详细文档**: 重构总结和测试说明 