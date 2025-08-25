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
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# 使用真实的PostgreSQL数据库进行集成测试
# 必须从环境变量获取数据库URL，不允许硬编码密码
REAL_DATABASE_URL = os.getenv("DATABASE_URL")
if not REAL_DATABASE_URL:
    raise ValueError("DATABASE_URL 环境变量未设置，请在 .env 文件中配置数据库连接信息")

REAL_SYNC_DATABASE_URL = REAL_DATABASE_URL.replace("+asyncpg", "+psycopg2")

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """创建共享的事件循环"""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()

@pytest.fixture
def real_async_engine():
    """创建真实PostgreSQL异步引擎 - 每个测试独立"""
    engine = create_async_engine(
        REAL_DATABASE_URL,
        echo=False,  # 测试时不显示SQL
        future=True,
        pool_pre_ping=True,  # 连接前检查
        pool_recycle=300,    # 5分钟后回收连接
        pool_size=1,         # 每个测试使用单个连接
        max_overflow=0,      # 不允许溢出连接
        pool_timeout=30,     # 连接超时时间
    )
    yield engine
    # 清理：关闭引擎
    import asyncio
    try:
        loop = asyncio.get_running_loop()
        if loop.is_running():
            # 如果事件循环正在运行，同步等待引擎释放完成
            # 使用asyncio.run_coroutine_threadsafe确保在正确的线程中执行
            import concurrent.futures
            import threading
            
            # 创建Future来等待任务完成
            future = asyncio.run_coroutine_threadsafe(engine.dispose(), loop)
            try:
                # 等待最多30秒完成，避免无限等待
                future.result(timeout=30)
            except concurrent.futures.TimeoutError:
                # 如果超时，记录警告但不阻塞测试
                import warnings
                warnings.warn("Engine disposal timed out after 30 seconds")
        else:
            loop.run_until_complete(engine.dispose())
    except RuntimeError:
        # 如果没有运行中的事件循环，创建新的
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(engine.dispose())
        finally:
            loop.close()

@pytest.fixture
def real_sync_engine():
    """创建真实PostgreSQL同步引擎 - 每个测试独立"""
    engine = create_engine(
        REAL_SYNC_DATABASE_URL,
        echo=False,  # 测试时不显示SQL
        future=True,
        pool_pre_ping=True,  # 连接前检查
        pool_recycle=300,    # 5分钟后回收连接
        pool_size=1,         # 每个测试使用单个连接
        max_overflow=0,      # 不允许溢出连接
    )
    yield engine
    # 清理：关闭引擎和所有连接
    try:
        engine.dispose()
    except Exception:
        # 忽略清理时的异常
        pass

@pytest.fixture
def real_sync_session(real_sync_engine):
    """创建真实PostgreSQL同步会话"""
    session = Session(real_sync_engine)
    try:
        # 开始事务
        session.begin()
        yield session
        # 回滚事务，不提交更改
        session.rollback()
    finally:
        # 确保会话被正确关闭
        try:
            session.close()
        except Exception:
            # 忽略关闭时的异常
            pass

@pytest.fixture
def mock_async_session():
    """创建模拟异步会话 - 用于单元测试"""
    from unittest.mock import AsyncMock
    mock_session = AsyncMock()
    return mock_session



@pytest.fixture
def test_client(real_async_engine):
    """创建测试客户端 - 使用相同的数据库引擎"""
    # 临时替换应用的数据库引擎和会话工厂
    from src.database import async_engine, async_session
    from src.main import app
    from sqlalchemy.orm import sessionmaker
    from sqlmodel.ext.asyncio.session import AsyncSession
    
    # 保存原始引擎和会话工厂
    original_engine = async_engine
    original_session = async_session
    
    # 替换为测试引擎和会话工厂
    import src.database
    src.database.async_engine = real_async_engine
    src.database.async_session = sessionmaker(
        real_async_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    client = None
    try:
        client = TestClient(app)
        yield client
    finally:
        # 确保客户端被正确关闭
        if client:
            try:
                client.close()
            except Exception:
                # 忽略关闭时的异常
                pass
        # 确保恢复原始引擎和会话工厂
        src.database.async_engine = original_engine
        src.database.async_session = original_session

@pytest.fixture
def sample_user_data():
    """示例用户数据"""
    return {
        "name": "testuser",
        "email": "test@example.com",
        "password": "testpassword",
        "state": 1
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
        "version": "1.0.0"
    }

@pytest.fixture
def setup_test_env():
    """设置测试环境 - 仅在需要时手动调用"""
    # 保存原始环境变量
    original_database_url = os.environ.get("DATABASE_URL")
    
    # 设置测试数据库URL
    os.environ["DATABASE_URL"] = REAL_DATABASE_URL
    
    yield
    
    # 恢复原始环境变量
    if original_database_url:
        os.environ["DATABASE_URL"] = original_database_url
    else:
        os.environ.pop("DATABASE_URL", None)


@pytest.fixture(autouse=True)
async def clear_cache_after_each_test():
    """在每个测试后清理所有缓存"""
    yield
    try:
        from src.utils.cache import cache_manager
        if cache_manager.is_available():
            # 清理所有缓存
            await cache_manager.clear_pattern("*")
    except Exception as e:
        # 如果缓存清理失败，继续测试
        pass 