# 认证安全状态（数据库）设计方案

> **说明（临时文档）**：本文档为草案，用于评审「以 PostgreSQL 单表替代 Redis 认证限流」的表结构与行为约定；与 `LOGIN_BRUTE_FORCE_PROTECTION_DESIGN.md`（Redis 实现）并存，待落地后可视情况合并或替换。**不要求随仓库提交**，可自行删除或改名。

---

## 一、文档目的

在以下前提下，给出可实现的详细设计：

1. **仅用户维度**：只有在能解析出 `user_id` 时才读取/写入本表；不存 IP、不明文存邮箱。
2. **单表承载状态**：用 `window_start` 表达失败计数窗口；用 `fail_count` 累计窗口内失败；用 `next_allowed_at` 表达「最早允许再试」（合并短冷却与长锁的对外语义，便于返回 `Retry-After`）。
3. **阈值与窗口长度**：统一来自现有/扩展的环境配置（`AUTH_*`），表中不存「每次操作单独阈值」。

---

## 二、与现有 Redis 方案的差异（必读）

| 项目 | 现有 Redis 方案 | 本方案 |
|------|-----------------|--------|
| 维度 | IP + 账号（账号侧为哈希，非 user_id） | 仅 `user_id` |
| 用户名不存在、邮箱无用户、非法 token | 仍可能通过 IP 或其它键限流 | **本表不参与**；需接受弱于双维度的防刷，或另行引入其它手段（本文不展开） |
| 注册前 | 可按 IP 限流 | **无 `user_id` 前本表不可用**；注册前限流需其它设计或放弃 |
| 存储 | Redis + Lua | PostgreSQL 单行 upsert / `SELECT FOR UPDATE` |

---

## 三、表结构

### 3.1 表名

建议：`user_auth_security_state`（与业务域一致、避免与通用 `security` 混淆）。

### 3.2 列定义

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | `BIGSERIAL` | `PRIMARY KEY` | 代理主键，便于 ORM 与日志引用；业务定位仍靠 `(user_id, opt_type)`。 |
| `user_id` | `BIGINT` | `NOT NULL`，`REFERENCES users(id)` | 绑定用户；删除用户时是否 `ON DELETE CASCADE` 由产品决定（推荐 `CASCADE` 清理孤儿状态）。 |
| `opt_type` | `VARCHAR(32)` | `NOT NULL` | 操作类型，见 §4。 |
| `fail_count` | `INTEGER` | `NOT NULL`，`DEFAULT 0`，`CHECK (fail_count >= 0)` | 当前失败计数窗口内的累计失败次数。 |
| `window_start` | `TIMESTAMPTZ` | `NOT NULL` | 当前失败计数窗口的起点；与配置中的「窗口秒数」配合决定是否归零 `fail_count`。 |
| `next_allowed_at` | `TIMESTAMPTZ` | `NOT NULL` | 该用户该操作类型下，**下一次允许发起相关请求的最早时刻**；未到则返回 429，并据此计算 `Retry-After`。 |

### 3.3 唯一约束与索引

- **业务唯一**：`UNIQUE (user_id, opt_type)`  
  所有更新必须针对至多一行；插入时使用 `ON CONFLICT (user_id, opt_type) DO UPDATE` 或等价逻辑，禁止依赖仅 `id` 定位业务状态。

- **可选索引**：若计划按时间清理冷数据，可增加 `INDEX (next_allowed_at)` 或 `INDEX (updated_at)`（若增加 `updated_at` 审计列，见 §8）。

### 3.4 与 `window_start`、`next_allowed_at` 的分工

- **`window_start`**：回答「当前 `fail_count` 从何时开始累计、何时视为进入新窗口并应清零计数」。
- **`next_allowed_at`**：回答「客户端最早何时可以再试」，同时覆盖：
  - **短冷却**（两次尝试最小间隔，与现网「5 秒」类似）；
  - **长锁**（达到失败阈值后的禁止时段，与现网「24 小时」类似）。

二者不重复：`window_start` 不负责「何时可再试」；`next_allowed_at` 不负责「计数窗口起点」。

---

## 四、`opt_type` 枚举约定

与接口一一对应，便于扩展与日志。建议取值（字符串常量，大小写敏感在代码中统一小写）：

| `opt_type` | 典型触发接口 | 解析 `user_id` 的时机（实现约束） |
|------------|--------------|-------------------------------------|
| `login` | `POST /api/auth/login` | 在能用用户名/邮箱**解析到已有用户**之后，再对本表做 pre-check / on-fail / on-success；解析不到则**跳过本表**（见 §七）。 |
| `forgot_password` | `POST /api/auth/forgot-password` | 仅在确认邮箱对应用户存在、且业务决定发送邮件/返回成功路径前，对**该用户**限流；邮箱无用户则跳过（与「不枚举用户」策略一致）。 |
| `validate_reset_token` | 校验重置 token 的接口 | Token 校验成功并解析出 `user_id` 后再计数/检查；token 无效则无 `user_id`，跳过。 |
| `reset_password` | 带 token 重置密码 | 与上类似，在已绑定 `user_id` 后更新。 |
| `register` | 注册相关 | 仅在**用户行已创建**并拿到 `user_id` 后，若仍需「每用户注册后冷却」可写；**注册请求到达前**无法用本表限流。 |

新增能力时追加新 `opt_type`，避免复用导致语义混乱。

---

## 五、配置项（环境变量）

前缀 `AUTH_*`，见 `src/config/auth_security.py` 与 `.env.example`。当前实现用到的键：

| 环境变量 | 含义 |
|----------|------|
| `AUTH_FAIL_CLOSED_WHEN_DB_ERROR` | 认证安全状态写库失败时是否返回 503（未设置时可回退读取已废弃的 `AUTH_FAIL_CLOSED_WHEN_REDIS_DOWN`） |
| `AUTH_LOGIN_MAX_FAIL_PER_ACCOUNT` | 登录失败阈值（与 `fail_count` 比较触发长锁） |
| `AUTH_LOGIN_LOCK_SECONDS` | 失败计数窗口长度与长锁秒数（实现中与现网一致用同一值） |
| `AUTH_LOGIN_MIN_INTERVAL_SECONDS` | 两次登录尝试最小间隔 |
| `AUTH_PWDRESET_REQ_MAX_PER_EMAIL` | 忘记密码每用户每窗口最大次数 |
| `AUTH_PWDRESET_REQ_WINDOW_SECONDS` | 忘记密码窗口秒数 |
| `AUTH_PWDRESET_VALIDATE_MAX_PER_USER` | 校验/重置 token 每用户每窗口最大次数 |
| `AUTH_PWDRESET_VALIDATE_WINDOW_SECONDS` | 上述窗口秒数 |
| `AUTH_REGISTER_MAX_PER_USER` | 注册成功记录每用户每窗口最大次数 |
| `AUTH_REGISTER_WINDOW_SECONDS` | 注册窗口秒数 |

**原则**：表中**不存**阈值与窗口秒数；读取配置在应用层完成，写入表时只写状态列。

---

## 六、状态机与算法（逻辑说明）

以下用伪代码描述；实现语言为 Python + SQLAlchemy/SQLModel 异步会话，且必须在**短事务**内完成读改写。

### 6.1 通用：进入新失败计数窗口

对某 `(user_id, opt_type)`：

```text
若 now >= window_start + FAIL_WINDOW_SECONDS:
    fail_count := 0
    window_start := now
```

在每次「记录失败」或「记录一次受保护尝试」前执行（或与递增同一事务内执行），保证窗口与现网「自窗口起点起计满再重置」语义一致。

### 6.2 通用：是否允许当前请求（pre-check）

```text
加载或插入 (user_id, opt_type) 行（见 §九 并发）
若 now < next_allowed_at:
    返回 429，Retry-After = ceil(next_allowed_at - now)
否则:
    允许进入业务逻辑；并根据策略更新 next_allowed_at（见下）
```

**短冷却（最小间隔）**：在「允许通过 pre-check、即将执行敏感操作」时：

```text
next_allowed_at := max(next_allowed_at, now + MIN_INTERVAL_SECONDS)
```

（若希望「仅失败后才冷却、成功不推迟」，可改为仅在失败分支更新；需与产品一致，并在实现注释中固定一种。）

### 6.3 登录失败（已知 user）

```text
BEGIN
对行 FOR UPDATE 或等价原子 upsert
应用 §6.1 窗口滚动
fail_count += 1
若 fail_count >= MAX_FAIL:
    next_allowed_at := max(next_allowed_at, now + LOCK_SECONDS)
否则:
    可选：next_allowed_at := max(next_allowed_at, now + MIN_INTERVAL_SECONDS)  # 若失败也强制短冷却
COMMIT
返回业务层 401 等
```

### 6.4 登录成功（已知 user）

```text
fail_count := 0
window_start := now   # 或保持原值，团队自定；建议重置窗口起点避免歧义
next_allowed_at := now  # 或 now + 0，表示立即允许后续合法操作；若仍有最小间隔策略则取 max
```

与现网「成功后清理失败计数」对齐。

### 6.5 忘记密码 / 校验 token / 注册后等

对非「失败递增」类限流（原 Redis 为 INCR + 小时窗口），可简化为：

- **仅计数 + 窗口**：用同一表的 `fail_count` 表示「周期内已使用次数」或单独语义 `usage_count`（若坚持用 `fail_count` 命名，建议在文档与代码注释中标明「广义计数」）；  
- 或使用 `window_start` + 配置窗口，在窗口内 `fail_count`（或计数列）超限则 `next_allowed_at = window_start + WINDOW_SECONDS`。

具体映射应在实现前为每个 `opt_type` 写清一行规则表（与现 `AUTH_PWDRESET_*`、`AUTH_REGISTER_*` 对齐）。

---

## 七、无法解析 `user_id` 时的行为（固定约定）

1. **不创建**匿名占位行（表中不出现「假 user_id」）。
2. **不调用**本表的 pre-check / increment（该请求在「用户状态限流」维度上为空白）。
3. 文档与发布说明中明确：**不削弱** TLS、密码强度、token 一次性等业务安全；削弱的是「针对未知身份的 DB 侧节流」。

若未来需要补 IP 维，应单独设计（不在本表内硬塞）。

---

## 八、可选列与运维

| 可选列 | 用途 |
|--------|------|
| `updated_at` | 自动 `on update`，便于清理与排障 |
| `created_at` | 首行插入时间 |

**清理**：可定期删除 `next_allowed_at < now() - 若干天` 且 `fail_count = 0` 且无长锁需求的行；或保留作审计（注意体积）。

---

## 九、并发与一致性

1. **同一 `(user_id, opt_type)`** 的所有变更必须在**单事务**内完成，并对该行加锁：
   - `SELECT … FROM user_auth_security_state WHERE user_id=? AND opt_type=? FOR UPDATE`；或
   - `INSERT … ON CONFLICT (user_id, opt_type) DO UPDATE … RETURNING *`（PostgreSQL 推荐，减少竞态）。
2. **死锁**：多 `opt_type` 同一请求若需锁多行，按 `opt_type` 字典序固定加锁顺序。
3. **数据库不可用**：与现 Fail-Closed 策略一致时可返回 503；由 `AUTH_FAIL_CLOSED_WHEN_DB_ERROR` 控制。

---

## 十、与代码仓库的衔接（实现清单，非本文执行）

1. **模型**：新增 SQLModel 表定义；在 `src/database.py` 中 `import` 模型以便 `create_all` 注册。
2. **迁移**：项目若无 Alembic，生产环境需提供等价 `CREATE TABLE` + `UNIQUE (user_id, opt_type)` 的 SQL 脚本。
3. **服务层**：以 `AuthSecurityService`（或新名）替换 Redis/Lua，注入 `AsyncSession`；控制器在能拿到 `user_id` 的分支调用。
4. **测试**：单测用事务回滚或测试库；覆盖窗口滚动、锁定、`Retry-After`、并发双请求只计一次等。
5. **文档**：落地后更新 `LOGIN_BRUTE_FORCE_PROTECTION_DESIGN.md` 或声明废弃 Redis 路径。

---

## 十一、小结

- **表**：`user_auth_security_state`  
- **列**：`id`（BIGSERIAL PK）、`user_id`、`opt_type`、`fail_count`、`window_start`、`next_allowed_at`  
- **约束**：`UNIQUE (user_id, opt_type)`  
- **语义**：`window_start` 管计数窗口；`next_allowed_at` 管最早可再试；配置管所有阈值与秒数；无 `user_id` 则不写不查本表。

---

*文档状态：临时草案；未与具体 PR/提交绑定。*
