"""article_hit_cookie 单元测试：签名校验与截断逻辑。"""

import os

import pytest

from src.utils import article_hit_cookie as m


@pytest.fixture
def secret(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "unit-test-secret-key")
    yield
    monkeypatch.delenv("SECRET_KEY", raising=False)


def test_roundtrip_and_tamper(secret):
    v = m.build_cookie_value({1, 42, 99})
    parsed = m.parse_seen_article_ids(v)
    assert parsed == {1, 42, 99}

    bad = "aaaa." + v.split(".", 1)[1]
    assert m.parse_seen_article_ids(bad) is None


def test_empty_cookie(secret):
    assert m.parse_seen_article_ids(None) == set()
    assert m.parse_seen_article_ids("") == set()


def test_max_ids_truncates_oldest(secret):
    ids = set(range(200))
    v = m.build_cookie_value(ids)
    parsed = m.parse_seen_article_ids(v)
    assert len(parsed) == m._MAX_IDS
    assert min(parsed) == 200 - m._MAX_IDS


def test_max_age_env(secret, monkeypatch):
    monkeypatch.setenv("ARTICLE_HIT_COOKIE_MAX_AGE", "7200")
    assert m.cookie_max_age() == 7200
    monkeypatch.setenv("ARTICLE_HIT_COOKIE_MAX_AGE", "30")
    assert m.cookie_max_age() == 60
