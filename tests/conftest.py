"""
Pytest 配置文件
包含测试夹具和全局设置
"""

import pytest
import asyncio
import os
import sys
from pathlib import Path
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.pool import StaticPool

# 测试数据库配置
TEST_DATABASE_URL = "sqlite:///./test.db"

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """创建事件循环夹具"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def test_engine():
    """创建测试数据库引擎"""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    yield engine
    # 清理测试数据库
    if os.path.exists("./test.db"):
        os.remove("./test.db")

@pytest.fixture
def test_session(test_engine):
    """创建测试数据库会话"""
    SQLModel.metadata.create_all(test_engine)
    with Session(test_engine) as session:
        yield session
    SQLModel.metadata.drop_all(test_engine)

@pytest.fixture
def mock_db_session():
    """模拟数据库会话"""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session

@pytest.fixture
def mock_async_session():
    """模拟异步数据库会话"""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session

@pytest.fixture
def test_client():
    """创建测试客户端"""
    from src.main import app
    with TestClient(app) as client:
        yield client

@pytest.fixture
def sample_user_data():
    """示例用户数据"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "full_name": "Test User",
        "bio": "Test bio"
    }

@pytest.fixture
def sample_blog_data():
    """示例博客数据"""
    return {
        "title": "Test Blog Post",
        "content": "This is a test blog post content.",
        "author_id": 1,
        "tags": ["test", "blog"],
        "status": "published"
    }

@pytest.fixture
def sample_metadata():
    """示例元数据"""
    return {
        "site_name": "Test Blog",
        "description": "A test blog site",
        "version": "1.0.0",
        "author": "Test Author"
    }

# 环境变量设置
@pytest.fixture(autouse=True)
def setup_test_env():
    """设置测试环境变量"""
    os.environ["ENVIRONMENT"] = "test"
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    yield
    # 清理环境变量
    if "ENVIRONMENT" in os.environ:
        del os.environ["ENVIRONMENT"]
    if "DATABASE_URL" in os.environ:
        del os.environ["DATABASE_URL"] 