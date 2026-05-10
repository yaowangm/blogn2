-- 创建 user_auth_security_state 表（认证安全状态，按用户 + 操作类型）
-- 设计说明: doc/AUTH_SECURITY_USER_STATE_DB_DESIGN.md
--
-- user_id 使用 BIGINT，与 public.users.id（bigint）外键类型一致。
--
-- 用法:
--   psql -U <user> -d <database> -f scripts/create_user_auth_security_state.sql
-- 或在 psql 内: \i scripts/create_user_auth_security_state.sql

CREATE TABLE IF NOT EXISTS user_auth_security_state (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    opt_type VARCHAR(32) NOT NULL,
    fail_count INTEGER NOT NULL DEFAULT 0 CHECK (fail_count >= 0),
    window_start TIMESTAMPTZ NOT NULL DEFAULT now(),
    next_allowed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_user_auth_security_state_user_opt UNIQUE (user_id, opt_type)
);

COMMENT ON TABLE user_auth_security_state IS '认证安全状态：每用户每操作类型一行，失败计数窗口与最早可再试时间';
COMMENT ON COLUMN user_auth_security_state.id IS '代理主键';
COMMENT ON COLUMN user_auth_security_state.user_id IS '用户 ID，关联 users';
COMMENT ON COLUMN user_auth_security_state.opt_type IS '操作类型：login / forgot_password / validate_reset_token / reset_password / register 等';
COMMENT ON COLUMN user_auth_security_state.fail_count IS '当前窗口内累计失败（或广义计数）';
COMMENT ON COLUMN user_auth_security_state.window_start IS '当前失败计数窗口起点';
COMMENT ON COLUMN user_auth_security_state.next_allowed_at IS '该操作类型下最早允许再发起请求的 UTC 时间';

-- ---------------------------------------------------------------------------
-- 补充索引说明（与 src/repositories/user_auth_security_state_repository.py 一致）
--
-- 热路径仅为等值条件：WHERE user_id = ? AND opt_type = ?（FOR UPDATE、
-- INSERT … ON CONFLICT … uq_user_auth_security_state_user_opt）。
-- 表上的 UNIQUE (user_id, opt_type) 已由 PostgreSQL 建立唯一 btree，勿再建
-- 等效复合索引以免重复占用空间。
--
-- 以下为 doc/AUTH_SECURITY_USER_STATE_DB_DESIGN.md 所述运维清理预留，例如：
--   DELETE FROM user_auth_security_state
--   WHERE fail_count = 0 AND next_allowed_at < now() - interval '90 days';
-- 部分索引缩小体积，并贴合 WHERE fail_count = 0 的过滤条件。
-- ---------------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS ix_user_auth_security_state_idle_next_allowed
    ON user_auth_security_state (next_allowed_at)
    WHERE fail_count = 0;
