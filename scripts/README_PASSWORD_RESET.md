# 用户密码重置脚本使用说明

## 概述

`reset_user_password.py` 是一个命令行工具，用于重置数据库中用户的密码。该脚本使用与登录系统完全相同的双重加密方式（MD5 + bcrypt），确保密码格式的一致性。

## 功能特性

- ✅ 通过用户ID查找用户
- ✅ 使用双重加密（MD5 + bcrypt）重置密码
- ✅ 支持交互式密码输入（隐藏显示）
- ✅ 密码强度检查
- ✅ 操作确认提示
- ✅ 密码验证测试
- ✅ 详细的用户信息显示

## 使用方法

### 基本用法

```bash
# 重置用户ID为1的密码
python scripts/reset_user_password.py 1
```

### 高级用法

```bash
# 跳过确认提示，直接重置密码
python scripts/reset_user_password.py 1 --force

# 直接指定新密码（不推荐，密码会显示在命令行历史中）
python scripts/reset_user_password.py 1 --password "newpassword123"

# 组合使用
python scripts/reset_user_password.py 1 --force --password "newpassword123"
```

## 命令行参数

| 参数 | 短选项 | 说明 | 必需 |
|------|--------|------|------|
| `user_id` | - | 要重置密码的用户ID | ✅ |
| `--force` | `-f` | 跳过确认提示，直接重置密码 | ❌ |
| `--password` | `-p` | 直接指定新密码 | ❌ |

## 使用示例

### 示例1：交互式重置密码

```bash
$ python scripts/reset_user_password.py 1

🔐 用户密码重置工具
==================================================
目标用户ID: 1

🔍 正在查找用户ID: 1

📋 用户信息:
  ID: 1
  用户名: admin
  邮箱: admin@example.com
  状态: 正常
  注册时间: 2024-01-01 00:00:00
  最后更新: 2024-01-15 10:30:00
  最后登录IP: 192.168.1.100
  积分: 100

⚠️  即将重置用户 'admin' 的密码
是否继续？(y/N): y

请输入新密码:
> ********

请再次输入新密码:
> ********

🔄 正在重置用户 'admin' 的密码...
✅ 密码重置成功！

🧪 验证新密码...
✅ 新密码验证成功！
```

### 示例2：批量重置密码（使用脚本）

```bash
#!/bin/bash
# 批量重置多个用户的密码

for user_id in 1 2 3 4 5; do
    echo "重置用户 $user_id 的密码..."
    echo "newpassword123" | python scripts/reset_user_password.py $user_id --force --password "newpassword123"
    echo "完成用户 $user_id"
    echo "---"
done
```

## 安全注意事项

1. **密码输入**: 推荐使用交互式输入（`getpass`），密码不会显示在屏幕上
2. **命令行历史**: 使用 `--password` 参数时，密码会记录在命令行历史中，存在安全风险
3. **权限控制**: 确保只有授权用户才能运行此脚本
4. **日志记录**: 密码重置操作会更新用户的 `lastupdate` 字段

## 加密方式说明

该脚本使用与登录系统完全相同的双重加密方式：

1. **第一步**: 对明文密码进行MD5哈希
   ```
   plain_password → MD5 → md5_hash
   ```

2. **第二步**: 对MD5哈希进行bcrypt加密
   ```
   md5_hash → bcrypt → final_hash
   ```

这种双重加密方式确保了：
- 与现有登录系统的兼容性
- 密码存储的安全性
- 支持旧格式密码的平滑迁移

## 错误处理

脚本包含完善的错误处理机制：

- 数据库连接失败
- 用户不存在
- 密码验证失败
- 数据库操作异常
- 用户中断操作

## 环境要求

- Python 3.7+
- 已安装项目依赖（`pip install -r requirements.txt`）
- 正确配置 `.env` 文件中的 `DATABASE_URL`
- 数据库连接权限

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查 `.env` 文件中的 `DATABASE_URL` 配置
   - 确认数据库服务正在运行
   - 验证数据库连接权限

2. **用户不存在**
   - 确认用户ID是否正确
   - 检查数据库中是否存在该用户

3. **密码验证失败**
   - 确认新密码格式正确
   - 检查数据库更新是否成功

### 调试模式

如需调试，可以修改脚本中的数据库连接配置：

```python
# 在 get_database_connection() 函数中
sync_engine = create_engine(
    database_url.replace("+asyncpg", "+psycopg2"),
    echo=True  # 显示SQL语句
)
```

## 相关文件

- `src/services/auth_service.py` - 认证服务，包含密码验证逻辑
- `src/models/user.py` - 用户模型定义
- `scripts/update_user_pass.py` - 密码格式迁移脚本

## 更新日志

- **v1.0.0** - 初始版本，支持基本的密码重置功能
- **v1.1.0** - 添加命令行参数支持，改进用户体验
