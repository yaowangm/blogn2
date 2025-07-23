import pytest
import asyncio
from typing import AsyncGenerator
from fastapi.testclient import TestClient
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import StaticPool

from src.main import app
from src.database import get_async_session
from src.database import User, ProjectItem

# 测试数据库URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# 创建测试数据库引擎
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_db_setup():
    """设置测试数据库"""
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

@pytest.fixture
async def test_session(test_db_setup):
    """创建测试数据库会话，直接返回AsyncSession对象"""
    session = AsyncSession(test_engine)
    try:
        yield session
    finally:
        await session.close()

@pytest.fixture
def client(test_session) -> TestClient:
    """创建测试客户端"""
    def override_get_session():
        return test_session
    
    app.dependency_overrides[get_async_session] = override_get_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
async def sample_user(test_session) -> User:
    """创建示例用户"""
    user = User(
        name="testuser",
        email="test@example.com",
        password="hashed_password",
        state=1
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    return user

@pytest.fixture
async def sample_project_item(test_session) -> ProjectItem:
    """创建示例项目条目"""
    item = ProjectItem(
        title="测试项目",
        description="这是一个测试项目",
        url="https://example.com",
        state=1
    )
    test_session.add(item)
    await test_session.commit()
    await test_session.refresh(item)
    return item 