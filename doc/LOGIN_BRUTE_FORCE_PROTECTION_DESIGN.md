# 登录防暴力破解与安全加固设计文档

**文档定位（2026）**：本文描述 BlogN2 认证链路的威胁模型、目标与**当前生产实现**（PostgreSQL 表 `user_auth_security_state` + `AuthSecurityService`）。历史上曾草案化「Redis + Lua 双维度（IP + 账号）」方案，**已不再使用**；业务缓存仍可单独使用 Redis，与认证安全状态存储无关。

表结构、字段语义与 `opt_type` 约定详见：`doc/AUTH_SECURITY_USER_STATE_DB_DESIGN.md`。环境变量见 `src/config/auth_security.py` 与 `.env.example`（前缀 `AUTH_*`）。

---

## 一、问题背景

`POST /api/auth/login` 在凭据错误时若无限流，攻击者可高频穷举密码。关联接口（忘记密码、校验 token、注册）也存在滥用与枚举风险。

---

## 二、目标与范围

### 2.1 目标

在保持登录成功返回 JWT、失败返回认证错误等**业务语义不变**的前提下，对敏感操作做可配置、可审计的节流与锁定。

### 2.2 范围

- 登录、忘记密码、重置密码、校验重置 token、注册成功后的用户维度状态；
- 不包含验证码、人机校验、设备指纹（可作为后续扩展）；
- **不包含**应用层业务缓存（仍可使用 Redis，见 `doc/README_CACHE.md`）。

---

## 三、当前核心策略（生产实现）

### 3.1 维度与前提

- **仅用户维度**：只有在能解析出 `user_id`（已存在用户）时，才读写 `user_auth_security_state`。
- **未知用户名/邮箱、无效 token**：不在该表上记录限流（与「防枚举」策略一致；若需 IP 维防护，应在网关/WAF 层单独考虑）。

### 3.2 登录（`opt_type=login`）

- **冷却**：通过 `next_allowed_at` 实现两次尝试最小间隔（配置 `AUTH_LOGIN_MIN_INTERVAL_SECONDS`）。
- **失败计数与窗口**：`fail_count` + `window_start`，窗口长度与长锁使用 `AUTH_LOGIN_LOCK_SECONDS`（与现实现一致）。
- **阈值**：`AUTH_LOGIN_MAX_FAIL_PER_ACCOUNT`；达到阈值后延长 `next_allowed_at` 并返回 `429`（或失败路径上同时返回业务错误码，见代码）。
- **成功**：清零该用户登录相关计数并允许立即继续合法操作。

### 3.3 密码重置与注册

- **忘记密码**：邮箱能解析到用户时，按 `AUTH_PWDRESET_REQ_*` 对该 `user_id` / `forgot_password` 行做窗口计数。
- **校验 token / 执行重置**：在能解析 token 对应 `user_id` 时，分别使用 `validate_reset_token`、`reset_password` 的 `opt_type` 与 `AUTH_PWDRESET_VALIDATE_*`。
- **注册**：成功创建用户后，对 `register` 的 `opt_type` 记录一次（`AUTH_REGISTER_*`）；`validate_regkey` **不做**该表限流（无 `user_id`）。

---

## 四、技术选型（状态存储）

- **存储**：PostgreSQL 表 `user_auth_security_state`（每 `(user_id, opt_type)` 至多一行）。
- **一致性**：`SELECT … FOR UPDATE` 与/或 `INSERT … ON CONFLICT DO NOTHING` 后再锁定读取，避免并发竞态。
- **不可用策略**：`AUTH_FAIL_CLOSED_WHEN_DB_ERROR`（未设置时可读已废弃的 `AUTH_FAIL_CLOSED_WHEN_REDIS_DOWN`，迁移期兼容）。为 `true` 时写库失败返回 `503`。

---

## 五、数据模型（概要）

不在本文重复列字段；请参阅 `AUTH_SECURITY_USER_STATE_DB_DESIGN.md` 与 `doc/DATABASE_SCHEMA.md` 中「用户认证安全状态表」一节。

---

## 六、接口行为约定（与实现对齐）

### 6.1 登录

1. 用 `UserRepository.get_by_login_identifier` 解析用户；若存在则 `pre_login_check(user_id)`。
2. 校验密码；失败则 `on_login_failed(user_id)`（若步骤 1 未解析到用户则跳过写表）。
3. 成功则 `on_login_success(user_id)`。

### 6.2 HTTP 建议

- 凭据错误且未触发锁定：`401`；
- 冷却/锁定：`429` + `Retry-After`；
- 安全状态写库失败且 Fail-Closed：`503`。

---

## 七、实现落点（代码结构）

| 职责 | 路径 |
|------|------|
| 配置 | `src/config/auth_security.py` |
| 安全服务 | `src/services/auth_security_service.py` |
| 状态仓储 | `src/repositories/user_auth_security_state_repository.py` |
| 模型 | `src/models/user_auth_security_state.py` |
| 依赖注入 | `src/utils/dependencies.py` → `get_auth_security_service` |
| 登录/重置等路由 | `src/controllers/auth.py`、`src/routes/user_register.py` |

---

## 八、配置项

以 `.env.example` 为准；常用项包括 `AUTH_FAIL_CLOSED_WHEN_DB_ERROR`、`AUTH_LOGIN_MAX_FAIL_PER_ACCOUNT`、`AUTH_LOGIN_LOCK_SECONDS`、`AUTH_LOGIN_MIN_INTERVAL_SECONDS`、`AUTH_PWDRESET_*`、`AUTH_REGISTER_*`（具体含义见 `AUTH_SECURITY_USER_STATE_DB_DESIGN.md` §五）。

---

## 九、并发与一致性

以下逻辑必须在**同一数据库事务/行锁**语义下完成，禁止仅靠前端延时：

- 登录前置检查与冷却写入；
- 失败计数递增与锁定判定；
- 窗口型 `opt_type` 的递增与超限判定。

---

## 十、日志与审计

建议记录：时间、脱敏账号标识、IP、User-Agent、事件类型（冷却/锁定/失败/成功）、相关 `opt_type` 与 `Retry-After` 依据。避免明文密码与完整邮箱进入日志。

---

## 十一、测试方案

### 11.1 单元测试

- 冷却与锁定分支、`Retry-After`、成功清零、Fail-Closed 503；
- 配置迁移：`AUTH_FAIL_CLOSED_WHEN_DB_ERROR` 与旧变量兼容（见 `tests/unit/test_auth_security_service.py`）。

### 11.2 接口/集成

- `/api/auth/login` 错误密码场景下计数与 429 行为；
- 重置与注册相关路由在可解析 `user_id` 时的限流。

---

## 十二、上线与运维建议

1. 执行建表 SQL：`scripts/create_user_auth_security_state.sql`（或依赖 `SQLModel.metadata.create_all` 的新环境）。
2. 配置 `AUTH_*` 与数据库连接；观察 429/503 比例。
3. 告警：短时登录失败激增、单用户 `fail_count` 异常、数据库错误率。
4. 反向代理继续正确透传 `X-Forwarded-For`（用于业务日志等；**认证安全表不存 IP**）。
5. 与运营同步锁定策略；必要时通过 SQL 或后续管理工具清理/调整 `user_auth_security_state` 行。

---

## 十三、后续可扩展项

- 验证码、风控评分、WAF 联动；
- 管理端查看/解锁某用户的 `user_auth_security_state`；
- 在网关对匿名接口补充 IP 维全局限流（与本表互补）。

---

## 十四、关联安全修复（历史草案与实现状态）

以下条目来自安全巡检时的分条设计；**实现状态**已标注，便于与代码对照。

### 14.1 重置密码请求限流

- **实现**：已用 `user_auth_security_state`（`forgot_password` / `validate_reset_token` / `reset_password`）按**用户**窗口计数；阈值见 `AUTH_PWDRESET_*`。不再使用 Redis 键。
- **说明**：未解析到用户时（未知邮箱、无效 token）不在该表限流。

### 14.2 重置 token 原子消费

- **实现**：`PasswordResetTokenRepository` 中使用 `DELETE … RETURNING` 等与密码更新同事务消费 token，避免并发重放。

### 14.3 重置 token 传输与泄露面

- **部分实现**：重置页等路径的 `Referrer-Policy` 等中间件策略见 `src/utils/middleware_handlers.py`；邮件内 URL 形态见 `EMAIL_PASSWORD_RESET_DESIGN.md`。

### 14.4 注册防枚举与限流

- **实现**：注册失败对外统一文案；注册成功后在 DB 记录 `register` 用量；`validate_regkey` 不做用户表限流（设计取舍）。

### 14.5 CORS 与会话存储

- **部分实现**：CORS 从环境变量读取；长期 Cookie 会话仍为规划项。

---

## 十五、配置补充

与 `AUTH_SECURITY_USER_STATE_DB_DESIGN.md` §五一致；默认值见 `.env.example`。

---

## 十六、分阶段计划（回顾）

P0/P1/P2 的优先级仍可参考，其中 **P0 中与认证限流相关项已在 DB 方案中落地**；其余（审计看板、验证码、Cookie 会话等）可按资源排期。

---

## 十七、验收标准（与实现对齐）

- **登录（已知用户）**：可配置次数阈值、约 24h 量级的锁定、`AUTH_LOGIN_MIN_INTERVAL_SECONDS` 冷却、成功后清理状态行中的登录计数语义。
- **重置链路**：超阈值 `429`；不枚举邮箱；token 原子消费。
- **注册**：对外统一失败提示；成功后有用户维度注册计数（若需 IP 维注册前限流须另案）。
- **观测**：日志可区分 401/429/503 与原因类别。
- **兼容**：正常登录/重置/注册主流程保持可用。

---

## 总结

认证相关限流与锁定已由 **PostgreSQL `user_auth_security_state` + `AuthSecurityService`** 实现，配置统一为 `AUTH_*`；Redis 仅保留给**非认证**的缓存等能力。详细表结构与算法见 `doc/AUTH_SECURITY_USER_STATE_DB_DESIGN.md`。
