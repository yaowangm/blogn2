# 密码重置脚本快速开始指南

## 🚀 快速使用

### 1. 基本用法

```bash
# 激活虚拟环境
source venv/bin/activate

# 重置用户ID为1的密码
python scripts/reset_user_password.py 1
```

### 2. 高级用法

```bash
# 跳过确认，直接重置密码
python scripts/reset_user_password.py 1 --force

# 指定新密码（不推荐，会显示在命令行历史中）
python scripts/reset_user_password.py 1 --password "newpassword123"

# 组合使用
python scripts/reset_user_password.py 1 --force --password "newpassword123"
```

## 📋 使用步骤

1. **激活虚拟环境**
   ```bash
   source venv/bin/activate
   ```

2. **运行脚本**
   ```bash
   python scripts/reset_user_password.py <用户ID>
   ```

3. **确认操作**
   - 脚本会显示用户信息
   - 输入 `y` 确认重置

4. **输入新密码**
   - 使用 `getpass` 输入，密码不会显示
   - 需要输入两次确认

5. **完成重置**
   - 脚本会自动验证新密码
   - 显示成功或失败信息

## ⚠️ 注意事项

- 确保 `.env` 文件中配置了正确的 `DATABASE_URL`
- 用户ID必须是数据库中存在的有效ID
- 新密码长度建议不少于6位
- 使用 `--force` 参数会跳过所有确认提示

## 🔧 故障排除

### 常见错误

1. **ModuleNotFoundError: No module named 'dotenv'**
   ```bash
   # 激活虚拟环境
   source venv/bin/activate
   ```

2. **数据库连接失败**
   - 检查 `.env` 文件中的 `DATABASE_URL`
   - 确认数据库服务正在运行

3. **用户不存在**
   - 确认用户ID是否正确
   - 检查数据库中是否存在该用户

### 测试功能

运行测试脚本验证功能是否正常：

```bash
python scripts/test_password_reset.py
```

## 📚 更多信息

- 详细使用说明：`README_PASSWORD_RESET.md`
- 测试脚本：`test_password_reset.py`
- 相关代码：`src/services/auth_service.py`
