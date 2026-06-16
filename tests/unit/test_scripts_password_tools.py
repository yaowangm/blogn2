"""scripts/ 下密码相关运维脚本的单元与集成测试。"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path

import pytest
from sqlalchemy.engine import make_url
from sqlmodel import Session, create_engine, select

from src.models.user import User
from tests.conftest import get_database_url, get_sync_database_url

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _load_script_module(module_name: str):
    path = PROJECT_ROOT / "scripts" / f"{module_name}.py"
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _unique_name(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _pytest_database_name() -> str:
    return make_url(get_sync_database_url()).database or ""


@pytest.fixture
def script_sync_session():
    engine = create_engine(get_sync_database_url(), echo=False)
    with Session(engine) as session:
        yield session
    engine.dispose()


class TestCreateAdminUserScript:
    @pytest.fixture
    def mod(self):
        return _load_script_module("create_admin_user")

    def test_validate_password_rejects_weak_and_short(self, mod):
        ok, _ = mod.validate_password("ValidPass1")
        assert ok is True

        ok, msg = mod.validate_password("123")
        assert ok is False
        assert "6" in msg

        ok, msg = mod.validate_password("password")
        assert ok is False
        assert "简单" in msg

    def test_hash_and_verify_password(self, mod):
        plain = "ScriptTest_Pw1!"
        stored = mod.hash_password(plain)
        assert stored.startswith("$2b$")
        assert mod.verify_password(plain, stored) is True
        assert mod.verify_password("wrong", stored) is False

    @pytest.mark.integration
    def test_create_and_update_admin_user(self, mod, script_sync_session):
        username = _unique_name("script_admin")
        password = "ScriptAdmin1!"

        assert mod.create_admin_user(
            script_sync_session, username, password, "script-admin@example.invalid"
        )

        user = mod.find_user_by_name(script_sync_session, username)
        assert user is not None
        assert user.state == 10
        assert mod.verify_password(password, user.password)

        new_password = "ScriptAdmin2!"
        assert mod.update_admin_user(
            script_sync_session, user, new_password, "updated@example.invalid"
        )
        script_sync_session.refresh(user)
        assert user.email == "updated@example.invalid"
        assert mod.verify_password(new_password, user.password)

    @pytest.mark.integration
    def test_cli_dry_run(self, mod):
        username = _unique_name("dryrun_admin")
        db_name = _pytest_database_name()
        result = subprocess.run(
            [
                sys.executable,
                str(PROJECT_ROOT / "scripts/create_admin_user.py"),
                "--dry-run",
                "-u",
                username,
                "-p",
                "DryRunPass1!",
                "-d",
                db_name,
            ],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr or result.stdout
        assert "预览操作" in result.stdout

        engine = create_engine(get_sync_database_url(), echo=False)
        try:
            with Session(engine) as session:
                assert mod.find_user_by_name(session, username) is None
        finally:
            engine.dispose()


class TestResetUserPasswordScript:
    @pytest.fixture
    def mod(self):
        return _load_script_module("reset_user_password")

    @pytest.mark.integration
    def test_reset_user_password(self, mod, script_sync_session):
        user = User(
            name=_unique_name("reset_target"),
            email="reset-target@example.invalid",
            password=mod.hash_password("OldPass1!"),
            state=1,
            regtime=datetime(2024, 1, 1, 12, 0, 0),
        )
        script_sync_session.add(user)
        script_sync_session.commit()
        script_sync_session.refresh(user)

        new_password = "NewPass2!"
        assert mod.reset_user_password(script_sync_session, user, new_password)
        script_sync_session.refresh(user)
        assert mod.verify_password(new_password, user.password)
        assert mod.verify_password("OldPass1!", user.password) is False

    @pytest.mark.integration
    def test_cli_reset_password(self, mod, script_sync_session):
        user = User(
            name=_unique_name("cli_reset"),
            email="cli-reset@example.invalid",
            password=mod.hash_password("OldCliPass1!"),
            state=1,
            regtime=datetime(2024, 1, 1, 12, 0, 0),
        )
        script_sync_session.add(user)
        script_sync_session.commit()
        script_sync_session.refresh(user)

        new_password = "CliNewPass1!"
        result = subprocess.run(
            [
                sys.executable,
                str(PROJECT_ROOT / "scripts/reset_user_password.py"),
                str(user.id),
                "-f",
                "-p",
                new_password,
            ],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            env={**__import__("os").environ, "DATABASE_URL": get_database_url()},
        )
        assert result.returncode == 0, result.stderr or result.stdout

        script_sync_session.expire_all()
        refreshed = mod.find_user_by_id(script_sync_session, user.id)
        assert refreshed is not None
        assert mod.verify_password(new_password, refreshed.password)


class TestUpdateUserPassScript:
    @pytest.fixture
    def mod(self):
        return _load_script_module("update_user_pass")

    def test_hash_format_detection(self, mod):
        md5 = "cc03e747a6afbbcbf8be7668acfebee5"
        assert mod.is_md5_hash(md5) is True
        assert mod.is_md5_hash("not-a-hash") is False

        bcrypt_sample = mod.convert_md5_to_bcrypt(md5)
        assert mod.is_bcrypt_hash(bcrypt_sample) is True

    def test_verify_double_hash(self, mod):
        plain = "migrate_me1"
        md5 = __import__("hashlib").md5(plain.encode()).hexdigest()
        stored = mod.convert_md5_to_bcrypt(md5)
        assert mod.verify_double_hash(plain, stored) is True


class TestScriptPasswordResetSelfCheck:
    """scripts/test_password_reset.py 中的自检函数。"""

    @pytest.fixture
    def mod(self):
        return _load_script_module("test_password_reset")

    def test_password_hashing(self, mod):
        assert mod.test_password_hashing() is True

    def test_password_verification(self, mod):
        assert mod.test_password_verification() is True

    def test_compatibility(self, mod):
        assert mod.test_compatibility() is True
