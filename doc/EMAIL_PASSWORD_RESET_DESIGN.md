# 邮件重置密码功能设计文档

本文档描述通过邮件（Ubuntu sendmail）实现自动重置密码的完整设计与实现要点。

---

## 一、功能概述

用户忘记密码时，可通过注册邮箱申请重置链接；系统发送带一次性令牌的邮件，用户点击链接后设置新密码，无需旧密码即可完成重置。

---

## 二、整体流程

```
┌─────────────┐    填写邮箱      ┌─────────────┐    生成 token 并保存    ┌─────────────┐
│   用户      │ ──────────────► │  申请重置   │ ──────────────────────► │   sendmail   │
└─────────────┘                 └─────────────┘                        └──────┬──────┘
                                                                               │
                                                                               │ 发送邮件
                                                                               ▼
┌─────────────┐    点击邮件链接   ┌─────────────┐    校验 token          ┌─────────────┐
│   用户      │ ◄──────────────  │  邮件中的   │ ◄────────────────────  │  设置新密码  │
└─────────────┘                  │  重置链接   │                         └──────┬──────┘
                                 └─────────────┘                                │
                                                                                │ 更新密码、删除 token
                                                                                ▼
                                                                         ┌─────────────┐
                                                                         │   完成      │
                                                                         └─────────────┘
```

- **申请重置**：用户输入邮箱 → 若该邮箱已注册则生成 token、入库、发邮件；若未注册也返回成功（防枚举）。
- **重置密码**：用户点击链接（带 token）→ 打开重置页 → 输入新密码 → 校验 token → 更新密码并删除 token。

---

## 三、现有基础（项目内）

| 模块 | 说明 |
|------|------|
| `User` 模型 | 含 `email`、`password`（bcrypt 哈希，支持 MD5+bcrypt 双格式） |
| `AuthService` | `hash_password()`、`verify_password()` |
| `UserRepository` | `get_by_email()`、`update_password(user_id, new_password)`（需传入已哈希密码） |
| `get_base_url()` | 用于生成重置链接根地址（如 `https://bloggern.com`） |

---

## 四、数据层设计

### 4.1 密码重置令牌表 `password_reset_tokens`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int, PK | 主键 |
| user_id | int, FK(users.id) | 用户 ID |
| token | varchar(64), unique, index | 一次性令牌（如 UUID 或 secrets.token_urlsafe） |
| expires_at | datetime | 过期时间 |
| created_at | datetime | 创建时间 |

- 同一用户可存在多条未过期 token（可选：实现时限制同一邮箱 N 分钟内仅允许一条，需业务层控制）。
- token 使用后立即删除，过期 token 可定时清理。

### 4.2 仓库接口 `PasswordResetTokenRepository`

- `create(user_id, token, expires_at)`：插入一条记录。
- `get_valid_token(token)`：根据 token 查询且 `expires_at > now()`，返回记录或 None。
- `delete_by_token(token)`：使用后删除。
- `delete_expired()`（可选）：定时任务清理过期记录。

---

## 五、邮件发送（sendmail）

### 5.1 实现方式

- 使用 Python 标准库 `subprocess` 调用系统 `sendmail` 命令。
- 邮件内容使用 `email.mime.text` / `email.mime.multipart` 构建 MIME，设置 From、To、Subject、正文。
- 对外接口示例：`send_password_reset_email(to_email, reset_link, username)`。

### 5.2 邮件内容要点

- **主题**：如「Bloggern 密码重置」。
- **正文**：含重置链接（`BASE_URL + /reset-password?token=xxx`）、有效期说明、未申请则忽略等提示。
- **发件人**：从配置 `MAIL_FROM` 读取（如 `noreply@bloggern.com`）。

### 5.3 Ubuntu sendmail 配置要点

- 安装：`sudo apt install sendmail`。
- 宏配置 `/etc/mail/sendmail.mc`：可设置 `MASQUERADE_AS(bloggern.com)` 等，使发件人域名与站点一致。
- 修改后需执行：`sudo make -C /etc/mail`，再 `sudo systemctl restart sendmail`。

---

## 六、DNS 与 SPF（提高送达率）

- 在域名 `bloggern.com` 的 DNS 中配置 **SPF 记录**（TXT 或新网等面板中的「SPF 记录」类型）。
- 若本机直接发信，记录示例：`v=spf1 ip4:发信服务器公网IP ~all`。
- 作用：声明允许该 IP 以 `@bloggern.com` 发信，减少被判为垃圾邮件；配合 DKIM/DMARC 可进一步优化。

---

## 七、业务逻辑层

### 7.1 PasswordResetService

- **request_reset(email)**  
  - 用 `UserRepository.get_by_email(email)` 查用户。  
  - 若不存在：直接返回成功，不发送邮件（防邮箱枚举）。  
  - 若存在：生成 token（如 `secrets.token_urlsafe(32)`），计算 `expires_at`（如当前时间 + 60 分钟），写入 `PasswordResetToken`，调用 `send_password_reset_email(...)`。

- **reset_password(token, new_password)**  
  - 调用 `get_valid_token(token)`，无效或过期则返回错误。  
  - 使用 `AuthService.hash_password(new_password)` 得到哈希，再调用 `UserRepository.update_password(user_id, hashed_password)`。  
  - 调用 `delete_by_token(token)` 使 token 一次性生效。

### 7.2 安全与限流（建议）

- token 长度与随机性：使用 `secrets.token_urlsafe(32)` 或等价方式。
- 有效期：30–60 分钟（可配置）。
- 同一邮箱请求频率限制：如 5 分钟内仅允许 1 次申请（可在 service 或 API 层用缓存/DB 实现）。

---

## 八、API 设计

### 8.1 申请重置

- **POST** `/api/auth/forgot-password`
- 请求体：`{"email": "user@example.com"}`
- 响应：`{"message": "若该邮箱已注册，将收到重置邮件"}`（不区分是否存在，防止枚举）

### 8.2 执行重置

- **POST** `/api/auth/reset-password`
- 请求体：`{"token": "xxx", "new_password": "xxx"}`
- 成功：`{"message": "密码重置成功"}`
- 失败：400/401（token 无效或过期）

### 8.3 可选：校验 token

- **GET** `/api/auth/validate-reset-token?token=xxx`
- 用于前端在展示重置表单前确认 token 是否有效，返回 `{"valid": true/false}`。

---

## 九、配置项

| 环境变量 | 说明 | 示例 |
|----------|------|------|
| MAIL_FROM | 发件人地址 | noreply@bloggern.com |
| RESET_LINK_EXPIRE_MINUTES | 重置链接有效期（分钟） | 60 |
| BASE_URL | 站点根 URL，用于生成重置链接 | https://bloggern.com |

---

## 十、前端页面

### 10.1 忘记密码页

- 路径：如 `/forgot-password`。
- 内容：邮箱输入框、提交按钮；提交到 `POST /api/auth/forgot-password`，展示统一提示“若该邮箱已注册，将收到重置邮件”。

### 10.2 重置密码页

- 路径：如 `/reset-password?token=xxx`（token 从 query 读取）。
- 内容：新密码、确认密码；提交到 `POST /api/auth/reset-password`；成功后跳转登录页。

### 10.3 入口

- 在登录框或登录页增加「忘记密码」链接，指向 `/forgot-password`。

---

## 十一、文件清单（实现时涉及）

| 类型 | 路径 |
|------|------|
| 模型 | src/models/password_reset_token.py |
| 仓库 | src/repositories/password_reset_token_repository.py |
| 服务 | src/services/password_reset_service.py |
| 邮件 | src/utils/email_sender.py |
| 控制器 | src/controllers/auth.py（新增 forgot-password、reset-password 接口） |
| Pydantic | src/models/auth.py（ForgotPasswordRequest/Response、ResetPasswordRequest/Response） |
| 配置 | src/config/app.py（MAIL_FROM、RESET_LINK_EXPIRE_MINUTES） |
| 环境变量模板 | .env.example（新增 MAIL_FROM、RESET_LINK_EXPIRE_MINUTES 说明与示例） |
| 页面 | src/static/forgot-password.html、reset-password.html |
| 路由 | src/utils/page_handlers.py（注册上述页面） |
| 前端入口 | 如 src/static/js/components/login-modal.js（“忘记密码”链接） |

---

## 十二、实施顺序建议

1. 配置 sendmail 并测试发信。
2. 在 `.env.example` 中新增邮件重置密码相关环境变量：`MAIL_FROM`、`RESET_LINK_EXPIRE_MINUTES`（含注释与示例值），便于部署时配置。
3. 实现 `PasswordResetToken` 模型与仓库，并在 `create_db_and_tables` 中注册。
4. 实现 `email_sender` 与 `PasswordResetService`。
5. 在 auth 控制器中实现 `POST /api/auth/forgot-password`、`POST /api/auth/reset-password`（及可选的 validate-reset-token）。
6. 实现忘记密码页、重置密码页及登录入口链接。
7. 配置 SPF（及可选 DKIM/DMARC），并做端到端测试与限流/安全加固。

---

## 十三、Docker 部署说明

- 若应用运行在 Docker 中，容器内需能调用 sendmail（安装 sendmail 或将 25 端口转发到宿主机 sendmail）；也可改为通过 SMTP 中继发信（需在配置中增加 SMTP 相关项并在 `email_sender` 中实现）。
- 环境变量 `MAIL_FROM`、`RESET_LINK_EXPIRE_MINUTES`、`BASE_URL` 需在容器环境中正确注入。

---

*文档版本：1.0，与 sendmail 分支邮件重置密码功能设计一致。*
