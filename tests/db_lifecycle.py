"""
Pytest 专用：基于 DATABASE_URL 中的连接信息创建/销毁临时 PostgreSQL 库。

DATABASE_URL 仅用于解析主机/账号；CREATE/DROP 连 catalog 库（默认 postgres），
不依赖其中的业务库名（如 blogn）是否存在。
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

logger = logging.getLogger(__name__)

_TEST_DB_CREATED_ENV = "BLOGN_PYTEST_DATABASE_CREATED"
_TEST_DB_NAME_ENV = "BLOGN_PYTEST_DATABASE_NAME"
_ADMIN_DATABASE_URL_ENV = "BLOGN_PYTEST_ADMIN_DATABASE_URL"
_TEST_DB_PREFIX = "blogn_pytest_"


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _test_database_name() -> str:
    return f"{_TEST_DB_PREFIX}{os.getpid()}"


def _is_managed_test_database(name: str | None) -> bool:
    return bool(name and name.startswith(_TEST_DB_PREFIX))


def _is_local_host(host: str | None) -> bool:
    return host in (None, "", "localhost", "127.0.0.1")


def _sync_url(database_url: str) -> str:
    return database_url.replace("+asyncpg", "+psycopg2")


def _url_username(parsed) -> str:
    if parsed.username:
        return parsed.username
    query = getattr(parsed, "query", None) or {}
    if isinstance(query, str):
        from urllib.parse import parse_qs

        query = {k: v[0] for k, v in parse_qs(query).items()}
    return query.get("user") or os.getenv("PGUSER") or os.getenv("USER") or "postgres"


def _normalize_local_database_url(database_url: str, database_name: str | None = None) -> str:
    """本机开发时改用 Unix socket（与 `psql blogn` 一致），避免 .env 里 TCP 密码与 peer 认证不一致。"""
    parsed = make_url(database_url)
    db = database_name if database_name is not None else parsed.database
    if not db or not _is_local_host(parsed.host):
        if database_name is not None:
            return str(parsed.set(database=database_name))
        return database_url

    driver = parsed.drivername
    if "asyncpg" in driver:
        driver = "postgresql+asyncpg"
    elif "psycopg2" in driver or driver == "postgresql":
        driver = "postgresql+psycopg2"
    else:
        driver = parsed.drivername

    user = _url_username(parsed)
    return f"{driver}://{user}@/{db}"


_ADMIN_CATALOG_DATABASE = "postgres"


def _admin_sync_url(database_url: str) -> str:
    """CREATE/DROP DATABASE 时连接 catalog 库，勿依赖 .env 业务库是否存在。"""
    override = os.getenv("BLOGN_PYTEST_ADMIN_DATABASE_URL", "").strip()
    if override:
        return _normalize_local_database_url(_sync_url(override))

    return _normalize_local_database_url(_sync_url(database_url), _ADMIN_CATALOG_DATABASE)


def _database_url_with_name(database_url: str, database_name: str) -> str:
    return _normalize_local_database_url(database_url, database_name)


def _import_all_models() -> None:
    """注册 SQLModel 与独立 declarative 模型，供 create_all 使用。"""
    from src.models import (  # noqa: F401
        attachment,
        folder,
        glovar,
        password_reset_token,
        point_log,
        post,
        project,
        project_item,
        regkey,
        relation,
        subscription,
        urllink,
        user,
        user_auth_security_state,
    )


def _hash_test_password(plain: str) -> str:
    """与 create_admin_user 一致：MD5 → bcrypt。"""
    from src.utils.password_hash import hash_user_password

    return hash_user_password(plain)


def _align_schema_with_legacy(conn) -> None:
    """SQLModel create_all 与历史 blogn 库部分列可空性不一致，测试库对齐为可空。"""
    legacy_nullable_columns = [
        ("users", "regtime"),
    ]
    for table, column in legacy_nullable_columns:
        conn.execute(text(f"ALTER TABLE {table} ALTER COLUMN {column} DROP NOT NULL"))


def _seed_baseline_data(database_url: str) -> None:
    """写入集成测试假定存在的基础数据（admin 用户等）。"""
    from datetime import datetime

    from sqlmodel import Session

    from src.models.user import User

    sync_url = _sync_url(database_url)
    engine = create_engine(sync_url, echo=False, future=True)
    try:
        with Session(engine) as session:
            if session.execute(text("SELECT COUNT(*) FROM users")).scalar():
                return

            admin = User(
                name="admin",
                password=_hash_test_password("testpasswd"),
                state=10,
                email="admin@example.com",
                regtime=datetime.now(),
                iplog="127.0.0.1",
                point=0,
                lastupdate=datetime.now(),
                intropiid=0,
            )
            session.add(admin)
            session.commit()
            logger.info("已写入 pytest 基础种子数据（admin 用户）")
    finally:
        engine.dispose()


def _run_sql_file_with_psql(database_url: str, sql_path: Path) -> bool:
    import shutil
    import subprocess

    if not shutil.which("psql"):
        return False

    parsed = make_url(_sync_url(database_url))
    username = _url_username(parsed)
    env = os.environ.copy()
    if parsed.password and not _is_local_host(parsed.host):
        env["PGPASSWORD"] = parsed.password

    cmd = [
        "psql",
        "-U",
        username,
        "-d",
        parsed.database or "",
        "-v",
        "ON_ERROR_STOP=0",
        "-f",
        str(sql_path),
    ]
    if not _is_local_host(parsed.host):
        cmd[1:1] = ["-h", parsed.host or "localhost", "-p", str(parsed.port or 5432)]
    result = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if result.returncode != 0:
        logger.warning(
            "psql 执行 %s 失败 (exit %s): %s",
            sql_path.name,
            result.returncode,
            (result.stderr or result.stdout or "").strip()[:500],
        )
        return False
    return True


def _init_schema(database_url: str) -> None:
    from sqlmodel import SQLModel

    from src.models.attachment import Base as AttachmentBase

    sync_url = _sync_url(database_url)
    engine = create_engine(sync_url, echo=False, future=True)

    _import_all_models()
    SQLModel.metadata.create_all(engine)
    AttachmentBase.metadata.create_all(engine)

    with engine.connect() as conn:
        try:
            _align_schema_with_legacy(conn)
            conn.commit()
        except Exception as exc:
            conn.rollback()
            logger.warning("测试库 schema 对齐失败，部分集成测试可能失败: %s", exc)

        try:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
        except Exception as exc:
            conn.rollback()
            logger.warning("测试库未安装 pgvector 扩展，向量相关测试可能失败: %s", exc)
        else:
            vector_sql = _project_root() / "scripts" / "create_vector_tables.sql"
            if vector_sql.is_file():
                if not _run_sql_file_with_psql(database_url, vector_sql):
                    logger.warning("向量表 SQL 未完整应用，部分 BERT 测试可能失败")

    engine.dispose()
    _seed_baseline_data(database_url)


def _reload_database_module() -> None:
    import importlib

    import src.database

    importlib.reload(src.database)


def provision_test_database() -> str:
    """创建临时测试库、初始化表结构，并改写 DATABASE_URL。"""
    if os.getenv(_TEST_DB_CREATED_ENV) == "1":
        url = os.getenv("DATABASE_URL")
        if not url:
            raise ValueError("DATABASE_URL 未设置")
        return url

    source_url = os.getenv("DATABASE_URL")
    if not source_url:
        raise ValueError(
            "DATABASE_URL 环境变量未设置。请在 .env 中配置 PostgreSQL 连接（仅用于解析主机/账号）。"
        )

    parsed = make_url(source_url)
    if not parsed.drivername.startswith("postgresql"):
        raise ValueError(
            f"pytest 集成测试需要 PostgreSQL，当前 DATABASE_URL 驱动为 {parsed.drivername!r}"
        )

    db_name = _test_database_name()
    admin_url = _admin_sync_url(source_url)
    admin_engine = create_engine(admin_url, echo=False, isolation_level="AUTOCOMMIT")

    try:
        with admin_engine.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": db_name},
            ).scalar()
            if not exists:
                conn.execute(text(f'CREATE DATABASE "{db_name}"'))
                logger.info("已创建 pytest 临时数据库: %s", db_name)
    finally:
        admin_engine.dispose()

    test_url = _database_url_with_name(source_url, db_name)
    os.environ["DATABASE_URL"] = test_url
    os.environ[_TEST_DB_NAME_ENV] = db_name
    os.environ[_ADMIN_DATABASE_URL_ENV] = admin_url
    os.environ[_TEST_DB_CREATED_ENV] = "1"

    _init_schema(test_url)
    _reload_database_module()

    logger.info("pytest 使用临时数据库: %s", db_name)
    return test_url


def destroy_test_database() -> None:
    """删除 pytest 创建的临时数据库。"""
    if os.getenv(_TEST_DB_CREATED_ENV) != "1":
        return

    db_name = os.getenv(_TEST_DB_NAME_ENV)
    if not _is_managed_test_database(db_name):
        logger.warning("跳过删除：非 pytest 托管库名 %r", db_name)
        return

    admin_url = os.getenv(_ADMIN_DATABASE_URL_ENV)
    if not admin_url:
        logger.warning("缺少管理连接 URL，无法删除临时测试库 %s", db_name)
        return

    admin_engine = create_engine(admin_url, echo=False, isolation_level="AUTOCOMMIT")

    try:
        with admin_engine.connect() as conn:
            conn.execute(
                text(
                    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                    "WHERE datname = :name AND pid <> pg_backend_pid()"
                ),
                {"name": db_name},
            )
            conn.execute(text(f'DROP DATABASE IF EXISTS "{db_name}" WITH (FORCE)'))
            logger.info("已删除 pytest 临时数据库: %s", db_name)
    except Exception as exc:
        logger.error("删除 pytest 临时数据库失败 %s: %s", db_name, exc)
    finally:
        admin_engine.dispose()
        os.environ.pop(_TEST_DB_CREATED_ENV, None)
        os.environ.pop(_TEST_DB_NAME_ENV, None)
        os.environ.pop(_ADMIN_DATABASE_URL_ENV, None)
