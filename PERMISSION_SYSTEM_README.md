# BlogN2 权限管理系统

## 概述

BlogN2权限管理系统是一个统一的权限控制解决方案，将所有权限相关代码集中管理，提供清晰的权限矩阵和灵活的权限检查机制。

## 系统架构

### 1. 权限管理器 (`src/utils/permission_manager.py`)

**核心功能**：
- 统一的权限检查逻辑
- 用户角色判断（管理员、普通用户、冻结用户）
- 个人资料查看权限控制
- 敏感字段访问权限控制
- 数据过滤功能

**主要方法**：
```python
# 角色判断
permission_manager.get_user_role(user_state)
permission_manager.is_admin(user_state)
permission_manager.is_frozen(user_state)

# 权限检查
permission_manager.can_view_profile(current_user, target_user_id, target_user_state)
permission_manager.can_view_sensitive_fields(current_user, target_user_id)
permission_manager.can_manage_users(current_user)
permission_manager.can_manage_system(current_user)

# 数据过滤
permission_manager.get_profile_data_permissions(current_user, target_user_id)
permission_manager.filter_profile_data(user_data, permissions)
```

### 2. 权限装饰器 (`src/utils/permission_decorators.py`)

**提供便捷的权限检查装饰器**：
- `@require_auth()` - 基本认证要求
- `@require_profile_access()` - 个人资料访问权限
- `@require_sensitive_fields_access()` - 敏感字段访问权限
- `@require_admin()` - 管理员权限
- `@require_user_management()` - 用户管理权限

### 3. 权限配置 (`src/config/permissions.py`)

**定义权限规则和配置**：
- 用户角色枚举（管理员、普通用户、冻结用户）
- 权限级别枚举（无权限、读取、写入、管理）
- 资源类型枚举（用户资料、敏感信息、博客内容、系统配置、用户管理）
- 权限矩阵配置
- 敏感字段和公开字段配置
- 权限检查规则配置
- 权限错误消息配置

### 4. 权限中间件 (`src/middleware/permission_middleware.py`)

**全局权限控制**：
- 自动识别受保护的路径
- 请求日志记录
- 权限审计功能
- 全局权限拦截

## 权限矩阵

| 用户类型 | 查看自己资料 | 查看他人资料 | 查看敏感字段 | 管理用户 | 管理系统 |
|---------|-------------|-------------|-------------|----------|----------|
| **未登录** | ❌ | ❌ | ❌ | ❌ | ❌ |
| **普通用户** | ✅ | ❌ | ✅ (仅自己) | ❌ | ❌ |
| **管理员** | ✅ | ✅ | ✅ (所有人) | ✅ | ✅ |
| **冻结用户** | ❌ | ❌ | ❌ | ❌ | ❌ |

## 使用方法

### 1. 在API控制器中使用

```python
from src.utils.permission_manager import permission_manager

@router.get("/users/{user_id}")
async def get_user_by_id(
    user_id: int,
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user)
):
    # 使用权限管理器检查权限
    if not permission_manager.can_view_profile(current_user, user_id, user.state):
        raise HTTPException(status_code=403, detail="无权限查看该用户资料")
    
    # 获取权限配置
    permissions = permission_manager.get_profile_data_permissions(current_user, user_id)
    
    # 过滤数据
    filtered_data = permission_manager.filter_profile_data(user_data, permissions)
    
    return filtered_data
```

### 2. 使用权限装饰器

```python
from src.utils.permission_decorators import require_admin

@router.get("/admin/system-config")
@require_admin()
async def get_system_config(current_user: Dict[str, Any] = Depends(get_current_user_required)):
    # 只有管理员可以访问
    return system_config
```

### 3. 在中间件中集成

```python
from src.middleware.permission_middleware import create_permission_middleware

# 在FastAPI应用中添加中间件
app.add_middleware(create_permission_middleware())
```

## 权限检查流程

1. **请求到达** → 中间件拦截
2. **路径识别** → 判断是否需要权限检查
3. **用户认证** → 获取当前用户信息
4. **权限验证** → 使用权限管理器检查权限
5. **数据过滤** → 根据权限过滤返回数据
6. **日志记录** → 记录权限检查和访问日志

## 安全特性

- **集中管理**：所有权限逻辑集中在一个地方
- **数据过滤**：敏感数据在后端就被过滤，不会传输到前端
- **角色分离**：清晰的用户角色和权限分离
- **审计日志**：完整的权限检查和访问日志
- **缓存控制**：防止敏感信息被浏览器缓存

## 扩展性

- **新增权限**：在权限配置中添加新的权限规则
- **新增角色**：在权限管理器中添加新的角色判断逻辑
- **新增资源**：在权限矩阵中添加新的资源类型
- **自定义装饰器**：创建特定业务场景的权限装饰器

## 最佳实践

1. **始终使用权限管理器**：不要在其他地方重复实现权限检查逻辑
2. **明确权限边界**：清晰定义每个API端点的权限要求
3. **数据最小化**：只返回用户有权限查看的数据
4. **日志完整性**：记录所有权限相关的操作
5. **错误处理**：提供清晰的权限错误消息

## 总结

BlogN2权限管理系统通过集中管理、统一接口、清晰配置的方式，实现了：

- **代码集中**：所有权限相关代码都在权限管理器中
- **逻辑清晰**：权限矩阵和检查规则一目了然
- **易于维护**：修改权限规则只需要修改配置文件
- **安全可靠**：多层权限检查和数据过滤
- **扩展性强**：支持新增权限、角色和资源类型

这个系统为BlogN2提供了企业级的权限管理能力，确保用户数据的安全性和系统的可维护性。
