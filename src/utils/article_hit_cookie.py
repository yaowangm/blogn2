"""
文章详情访问量去重：浏览器端签名 Cookie，短 Max-Age，不落库、不占用 Redis 会话。

SECRET_KEY 用于 HMAC；可选 ARTICLE_HIT_COOKIE_MAX_AGE（秒，默认 3600，范围 60–86400）。
可选 ARTICLE_HIT_COOKIE_SECURE=true 时设置 Secure 属性。
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import os
from typing import Optional, Set

COOKIE_NAME = "blogn_ac"
_MAX_IDS = 120
_DEFAULT_MAX_AGE = 3600


def _secret_bytes() -> bytes:
    key = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    return key.encode("utf-8")


def cookie_max_age() -> int:
    raw = os.getenv("ARTICLE_HIT_COOKIE_MAX_AGE", str(_DEFAULT_MAX_AGE))
    try:
        v = int(raw)
    except ValueError:
        return _DEFAULT_MAX_AGE
    return max(60, min(v, 86400))


def cookie_secure() -> bool:
    return os.getenv("ARTICLE_HIT_COOKIE_SECURE", "").lower() in ("1", "true", "yes")


def _sign(payload: str) -> str:
    mac = hmac.new(_secret_bytes(), payload.encode("utf-8"), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(mac).decode("ascii").rstrip("=")


def _urlsafe_b64decode(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)


def parse_seen_article_ids(cookie_value: Optional[str]) -> Optional[Set[int]]:
    """
    解析 Cookie。返回 None 表示签名校验失败（伪造或损坏）；缺失或空字符串视为已见集合为空。
    """
    if not cookie_value:
        return set()
    try:
        sig_part, payload_b64 = cookie_value.split(".", 1)
        payload = _urlsafe_b64decode(payload_b64).decode("utf-8")
        if not hmac.compare_digest(sig_part, _sign(payload)):
            return None
        data = json.loads(payload)
        ids = data.get("i")
        if not isinstance(ids, list):
            return None
        return {int(x) for x in ids}
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError, binascii.Error):
        return None


def build_cookie_value(seen_ids: Set[int]) -> str:
    id_list = sorted(seen_ids)
    if len(id_list) > _MAX_IDS:
        id_list = id_list[-_MAX_IDS:]
    payload = json.dumps({"i": id_list}, separators=(",", ":"))
    bile = base64.urlsafe_b64encode(payload.encode("utf-8")).decode("ascii").rstrip("=")
    return f"{_sign(payload)}.{bile}"
