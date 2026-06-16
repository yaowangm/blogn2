"""Bcrypt 密码哈希（MD5 预哈希，与历史 blogn 存储格式兼容）。"""

from __future__ import annotations

import hashlib

import bcrypt


def _md5_hex(value: str) -> str:
    return hashlib.md5(value.encode("utf-8")).hexdigest()


def bcrypt_hash(value: str) -> str:
    return bcrypt.hashpw(value.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def bcrypt_verify(value: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(value.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def hash_user_password(plain_password: str) -> str:
    """明文密码 → MD5 → bcrypt（注册/重置密码的标准流程）。"""
    return bcrypt_hash(_md5_hex(plain_password))


def verify_user_password(plain_password: str, stored_hash: str) -> bool:
    """验证密码，支持直接 bcrypt（旧格式）与 MD5+bcrypt（新格式）。"""
    try:
        if stored_hash.startswith("$2b$") and len(stored_hash) == 60:
            if bcrypt_verify(plain_password, stored_hash):
                return True
            return bcrypt_verify(_md5_hex(plain_password), stored_hash)
        return bcrypt_verify(_md5_hex(plain_password), stored_hash)
    except Exception:
        return False
