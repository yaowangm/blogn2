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

def cleanup_test_data(engine):
    """清理测试数据"""
    from sqlmodel import Session
    from sqlalchemy import text
    session = Session(engine)
    try:
        print("🧹 开始清理测试数据...")
        
        # 获取当前最大的ID作为基准
        max_id_result = session.execute(text("SELECT MAX(id) as max_id FROM post"))
        max_id = max_id_result.fetchone()[0] or 0
        test_id_threshold = max_id - 1000  # 假设测试数据的ID比当前最大ID小1000以内
        
        # 删除测试用户
        result1 = session.execute(text("DELETE FROM users WHERE name LIKE '%test%' OR email LIKE '%test%' OR name LIKE '%Test%' OR email LIKE '%Test%'"))
        print(f"🗑️ 删除了 {result1.rowcount} 个测试用户")
        
        # 删除测试项目
        result2 = session.execute(text("DELETE FROM project WHERE name LIKE '%Test%' OR name LIKE '%test%'"))
        print(f"🗑️ 删除了 {result2.rowcount} 个测试项目")
        
        # 删除测试文章
        result3 = session.execute(text("DELETE FROM projectitem WHERE name LIKE '%Test%' OR name LIKE '%test%'"))
        print(f"🗑️ 删除了 {result3.rowcount} 个测试文章")
        
        # 删除测试评论和留言（更全面的清理）
        result4 = session.execute(text("""
            DELETE FROM post WHERE 
                content LIKE '%测试%' OR content LIKE '%test%' OR 
                subject LIKE '%测试%' OR subject LIKE '%test%' OR
                content LIKE '%这是%' OR subject LIKE '%这是%' OR
                content LIKE '%跟贴%' OR content LIKE '%主贴%' OR
                content LIKE '%留言本%' OR subject LIKE '%留言本%' OR
                content LIKE '%文章评论%' OR subject LIKE '%文章评论%' OR
                id > :threshold
        """), {"threshold": test_id_threshold})
        print(f"🗑️ 删除了 {result4.rowcount} 个测试评论和留言")
        
        # 删除测试附件
        result5 = session.execute(text("DELETE FROM attachment WHERE comment LIKE '%test%' OR comment LIKE '%Test%' OR linkstr LIKE '%test%' OR linkstr LIKE '%Test%'"))
        print(f"🗑️ 删除了 {result5.rowcount} 个测试附件")
        
        # 删除测试分类
        result6 = session.execute(text("DELETE FROM folders WHERE name LIKE '%test%' OR name LIKE '%Test%'"))
        print(f"🗑️ 删除了 {result6.rowcount} 个测试分类")
        
        # 删除测试友情链接
        result7 = session.execute(text("DELETE FROM urllink WHERE subject LIKE '%test%' OR subject LIKE '%Test%' OR linkstr LIKE '%test%' OR linkstr LIKE '%Test%'"))
        print(f"🗑️ 删除了 {result7.rowcount} 个测试友情链接")
        
        # 删除测试订阅（基于项目ID）
        result8 = session.execute(text("DELETE FROM subsc WHERE projectid IN (SELECT id FROM project WHERE name LIKE '%test%' OR name LIKE '%Test%')"))
        print(f"🗑️ 删除了 {result8.rowcount} 个测试订阅")
        
        session.commit()
        print("✅ 测试数据清理完成")
    except Exception as e:
        print(f"❌ 清理测试数据时出错: {e}")
        session.rollback()
    finally:
        session.close()

class UnifiedDatabaseManager:
    """统一的数据库连接和事务管理器"""
    
    def __init__(self, sync_engine, async_engine):
        self.sync_engine = sync_engine
        self.async_engine = async_engine
        self._transaction = None
        self._async_transaction = None
    
    def begin_transaction(self):
        """开始事务"""
        # 创建同步会话并开始事务
        self.sync_session = Session(self.sync_engine)
        self._transaction = self.sync_session.begin()
        
        # 创建异步会话并开始事务
        from sqlmodel.ext.asyncio.session import AsyncSession
        from sqlalchemy.orm import sessionmaker
        async_session_factory = sessionmaker(
            self.async_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        self.async_session = async_session_factory()
        # 使用同步方式开始异步事务
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果事件循环正在运行，创建任务
                task = asyncio.create_task(self.async_session.begin())
                self._async_transaction = task
            else:
                # 如果事件循环没有运行，直接运行
                self._async_transaction = loop.run_until_complete(self.async_session.begin())
        except RuntimeError:
            # 如果没有事件循环，创建新的
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                self._async_transaction = loop.run_until_complete(self.async_session.begin())
            finally:
                loop.close()
    
    def commit(self):
        """提交事务"""
        if self._transaction:
            self._transaction.commit()
        if self._async_transaction:
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self._async_transaction.commit())
                else:
                    loop.run_until_complete(self._async_transaction.commit())
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(self._async_transaction.commit())
                finally:
                    loop.close()
    
    def rollback(self):
        """回滚事务"""
        if self._transaction:
            try:
                self._transaction.rollback()
            except Exception:
                pass
        if self._async_transaction:
            try:
                import asyncio
                # 如果是任务，等待完成
                if asyncio.iscoroutine(self._async_transaction):
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.create_task(self._async_transaction.rollback())
                    else:
                        loop.run_until_complete(self._async_transaction.rollback())
                else:
                    # 如果是事务对象，直接回滚
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.create_task(self._async_transaction.rollback())
                    else:
                        loop.run_until_complete(self._async_transaction.rollback())
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    if asyncio.iscoroutine(self._async_transaction):
                        loop.run_until_complete(self._async_transaction.rollback())
                    else:
                        loop.run_until_complete(self._async_transaction.rollback())
                finally:
                    loop.close()
            except Exception:
                pass
    
    def close(self):
        """关闭连接"""
        if hasattr(self, 'sync_session'):
            try:
                self.sync_session.close()
            except Exception:
                pass
        if hasattr(self, 'async_session'):
            try:
                import asyncio
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self.async_session.close())
                else:
                    loop.run_until_complete(self.async_session.close())
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(self.async_session.close())
                finally:
                    loop.close()
            except Exception:
                pass

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
    """创建真实PostgreSQL同步会话 - 每个测试后自动回滚"""
    session = Session(real_sync_engine)
    try:
        # 开始事务
        session.begin()
        yield session
    finally:
        # 回滚事务，不提交更改
        try:
            session.rollback()
        except Exception:
            # 忽略回滚时的异常
            pass
        finally:
            # 确保会话被正确关闭
            try:
                session.close()
            except Exception:
                # 忽略关闭时的异常
                pass

@pytest.fixture
def unified_db_manager(real_sync_engine, real_async_engine):
    """创建统一的数据库管理器"""
    manager = UnifiedDatabaseManager(real_sync_engine, real_async_engine)
    try:
        # 开始事务
        manager.begin_transaction()
        yield manager
    finally:
        # 回滚事务并关闭连接
        try:
            manager.rollback()
        except Exception:
            pass
        try:
            manager.close()
        except Exception:
            pass
        # 手动清理测试数据作为备用方案
        try:
            cleanup_test_data(real_sync_engine)
        except Exception:
            pass

@pytest.fixture(autouse=True)
def cleanup_after_test(real_sync_engine):
    """自动清理测试数据 - 在每个测试后运行"""
    yield
    # 测试结束后清理数据
    try:
        cleanup_test_data(real_sync_engine)
    except Exception:
        pass

@pytest.fixture
def real_sync_session_with_commit(unified_db_manager):
    """创建真实PostgreSQL同步会话 - 使用统一事务管理"""
    yield unified_db_manager.sync_session

@pytest.fixture
def real_async_session_with_commit(unified_db_manager):
    """创建真实PostgreSQL异步会话 - 使用统一事务管理"""
    yield unified_db_manager.async_session

@pytest.fixture
def mock_async_session():
    """创建模拟异步会话 - 用于单元测试"""
    from unittest.mock import AsyncMock
    mock_session = AsyncMock()
    return mock_session

@pytest.fixture
async def real_async_session(real_async_engine):
    """创建真实PostgreSQL异步会话 - 每个测试后自动回滚"""
    from sqlmodel.ext.asyncio.session import AsyncSession
    from sqlalchemy.orm import sessionmaker
    
    # 创建会话工厂
    async_session_factory = sessionmaker(
        real_async_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session_factory() as session:
        # 开始事务
        await session.begin()
        # 创建保存点
        savepoint = await session.begin_nested()
        try:
            yield session
        finally:
            # 回滚到保存点
            await savepoint.rollback()

@pytest.fixture
async def real_async_session_with_commit(real_async_engine):
    """创建真实PostgreSQL异步会话 - 使用事务回滚"""
    from sqlmodel.ext.asyncio.session import AsyncSession
    from sqlalchemy.orm import sessionmaker
    
    # 创建会话工厂
    async_session_factory = sessionmaker(
        real_async_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session_factory() as session:
        # 开始事务
        await session.begin()
        try:
            yield session
        finally:
            # 回滚整个事务
            try:
                await session.rollback()
            except Exception:
                pass



@pytest.fixture
def test_client(unified_db_manager):
    """创建测试客户端 - 使用统一数据库管理器"""
    # 临时替换应用的数据库引擎和会话工厂
    from src.database import async_engine, async_session
    from src.main import app
    from sqlalchemy.orm import sessionmaker
    from sqlmodel.ext.asyncio.session import AsyncSession
    
    # 保存原始引擎和会话工厂
    original_engine = async_engine
    original_session = async_session
    
    # 替换为统一管理器的异步引擎和会话
    import src.database
    src.database.async_engine = unified_db_manager.async_engine
    src.database.async_session = sessionmaker(
        unified_db_manager.async_engine,
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
def test_client_with_rollback(real_async_engine):
    """创建测试客户端 - 使用事务回滚"""
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
            # 检查事件循环是否还在运行
            try:
                loop = asyncio.get_running_loop()
                if loop.is_closed():
                    # 事件循环已关闭，跳过缓存清理
                    return
            except RuntimeError:
                # 没有运行的事件循环，跳过缓存清理
                return
            
            # 清理所有缓存
            await cache_manager.clear_pattern("*")
    except Exception as e:
        # 如果缓存清理失败，继续测试
        pass 