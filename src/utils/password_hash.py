"""Bcrypt 密码哈希（MD5 预哈希，与历史 blogn / passlib 输出兼容）。"""

from __future__ import annotations

import bcrypt


def bcrypt_hash(value: str) -> str:
    return bcrypt.hashpw(value.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def bcrypt_verify(value: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(value.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False
