"""
Pytest 配置文件
包含测试夹具和全局设置
"""

import pytest
import asyncio
import os
import sys
import logging
from pathlib import Path
from typing import Generator, Set, Dict, Any
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock
from dotenv import load_dotenv
from sqlalchemy.exc import InvalidRequestError, StatementError

# 加载环境变量
load_dotenv()

# 配置日志记录器
logger = logging.getLogger(__name__)

class TestDataTracker:
    """测试数据跟踪器 - 记录测试过程中创建的数据ID"""
    
    def __init__(self):
        self.user_ids: Set[int] = set()
        self.project_ids: Set[int] = set()
        self.article_ids: Set[int] = set()
        self.comment_ids: Set[int] = set()
        self.message_ids: Set[int] = set()
        self.attachment_ids: Set[int] = set()
        self.folder_ids: Set[int] = set()
        self.urllink_ids: Set[int] = set()
        self.subscription_ids: Set[int] = set()
    
    def add_user(self, user_id: int):
        """记录用户ID"""
        self.user_ids.add(user_id)
    
    def add_project(self, project_id: int):
        """记录项目ID"""
        self.project_ids.add(project_id)
    
    def add_article(self, article_id: int):
        """记录文章ID"""
        self.article_ids.add(article_id)
    
    def add_comment(self, comment_id: int):
        """记录评论ID"""
        self.comment_ids.add(comment_id)
    
    def add_message(self, message_id: int):
        """记录留言ID"""
        self.message_ids.add(message_id)
    
    def add_attachment(self, attachment_id: int):
        """记录附件ID"""
        self.attachment_ids.add(attachment_id)
    
    def add_folder(self, folder_id: int):
        """记录分类ID"""
        self.folder_ids.add(folder_id)
    
    def add_urllink(self, urllink_id: int):
        """记录友情链接ID"""
        self.urllink_ids.add(urllink_id)
    
    def add_subscription(self, subscription_id: int):
        """记录订阅ID"""
        self.subscription_ids.add(subscription_id)
    
    def clear(self):
        """清空所有记录的ID"""
        self.user_ids.clear()
        self.project_ids.clear()
        self.article_ids.clear()
        self.comment_ids.clear()
        self.message_ids.clear()
        self.attachment_ids.clear()
        self.folder_ids.clear()
        self.urllink_ids.clear()
        self.subscription_ids.clear()
    
    def has_data(self) -> bool:
        """检查是否有记录的数据"""
        return any([
            self.user_ids, self.project_ids, self.article_ids, 
            self.comment_ids, self.message_ids, self.attachment_ids,
            self.folder_ids, self.urllink_ids, self.subscription_ids
        ])

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 确保静态文件目录存在（用于测试）
static_dir = project_root / "src" / "static"
static_dir.mkdir(parents=True, exist_ok=True)

# 确保配置加载在测试前正确初始化（避免测试失败）
# 在测试环境中，如果没有配置文件，使用默认配置
# 必须在导入任何使用配置的模块之前完成配置加载

# 设置测试环境的模型配置（使用本地模型，避免访问 Hugging Face）
# 优先 modelscope 路径，其次 Hugging Face 默认缓存（sentence-transformers 下载后的位置）
_default_model_path_modelscope = os.path.expanduser(
    "~/.cache/modelscope/hub/models/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)
_default_model_path_huggingface = os.path.expanduser(
    "~/.cache/huggingface/hub/models--sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2"
)

def _get_test_local_model_path():
    """返回可用的本地模型路径，优先 modelscope，其次 Hugging Face 缓存。"""
    if os.path.exists(_default_model_path_modelscope):
        return _default_model_path_modelscope
    if os.path.exists(_default_model_path_huggingface):
        # HF 缓存：实际模型在 snapshots/<revision>/ 下，SentenceTransformer 需要该目录
        snapshots_dir = os.path.join(_default_model_path_huggingface, "snapshots")
        if os.path.isdir(snapshots_dir):
            try:
                revs = sorted(os.listdir(snapshots_dir))
                if revs:
                    snapshot_path = os.path.join(snapshots_dir, revs[0])
                    if os.path.isdir(snapshot_path):
                        return snapshot_path
            except OSError:
                pass
        return _default_model_path_huggingface
    return None

try:
    # 先加载配置工具
    from src.config.utils import load_config_file, get_config_file_path
    # 加载配置文件（这会更新环境变量，但不会覆盖已存在的环境变量）
    config_path = load_config_file()
    if config_path:
        logger.info(f"测试环境使用配置文件: {config_path}")
    else:
        logger.debug("测试环境使用默认配置（未找到配置文件）")
    
    # 在配置加载后，确保使用本地模型（优先级最高）
    _test_local_model_path = _get_test_local_model_path()
    if _test_local_model_path:
        os.environ["MODEL_MODEL_PATH"] = _test_local_model_path
        os.environ["MODEL_PREFER_LOCAL"] = "true"
        os.environ["MODEL_FALLBACK_TO_HUGGINGFACE"] = "false"
        logger.info(f"测试环境强制使用本地模型: {_test_local_model_path}")
    elif not os.getenv("MODEL_MODEL_PATH"):
        logger.warning(
            f"本地模型路径不存在（已检查 modelscope 与 ~/.cache/huggingface/hub），将尝试从 Hugging Face 下载"
        )

except Exception as e:
    # 如果配置加载失败，记录但不中断测试
    logger.debug(f"配置加载初始化失败（测试环境）: {e}")
    import traceback
    logger.debug(traceback.format_exc())
    
    # 即使配置加载失败，也尝试设置本地模型路径
    _test_local_model_path = _get_test_local_model_path()
    if _test_local_model_path:
        os.environ["MODEL_MODEL_PATH"] = _test_local_model_path
        os.environ["MODEL_PREFER_LOCAL"] = "true"
        os.environ["MODEL_FALLBACK_TO_HUGGINGFACE"] = "false"

def cleanup_test_data_by_ids(tracker: TestDataTracker):
    """基于ID精确清理测试数据"""
    if not tracker.has_data():
        print("🧹 没有测试数据需要清理")
        return
    
    print("🧹 开始基于ID清理测试数据...")
    
    # 使用真实数据库连接
    from sqlmodel import create_engine, text
    from sqlalchemy import create_engine as create_sync_engine
    
    # 创建同步引擎
    sync_engine = create_sync_engine(REAL_SYNC_DATABASE_URL, echo=False)
    
    try:
        with sync_engine.connect() as conn:
            # 开始事务
            trans = conn.begin()
            
            try:
                total_deleted = 0
                
                # 按依赖关系顺序删除数据
                if tracker.comment_ids or tracker.message_ids:
                    # 删除评论和留言
                    all_post_ids = tracker.comment_ids | tracker.message_ids
                    if all_post_ids:
                        placeholders = ','.join(map(str, all_post_ids))
                        query = f"DELETE FROM post WHERE id IN ({placeholders})"
                        result = conn.execute(text(query))
                        deleted_count = result.rowcount
                        total_deleted += deleted_count
                        print(f"🗑️ 删除了 {deleted_count} 个测试评论和留言")
                
                if tracker.article_ids:
                    # 删除文章
                    placeholders = ','.join(map(str, tracker.article_ids))
                    query = f"DELETE FROM projectitem WHERE id IN ({placeholders})"
                    result = conn.execute(text(query))
                    deleted_count = result.rowcount
                    total_deleted += deleted_count
                    print(f"🗑️ 删除了 {deleted_count} 个测试文章")
                
                if tracker.attachment_ids:
                    # 删除附件
                    placeholders = ','.join(map(str, tracker.attachment_ids))
                    query = f"DELETE FROM attachment WHERE id IN ({placeholders})"
                    result = conn.execute(text(query))
                    deleted_count = result.rowcount
                    total_deleted += deleted_count
                    print(f"🗑️ 删除了 {deleted_count} 个测试附件")
                
                if tracker.subscription_ids:
                    # 删除订阅
                    placeholders = ','.join(map(str, tracker.subscription_ids))
                    query = f"DELETE FROM subscription WHERE id IN ({placeholders})"
                    result = conn.execute(text(query))
                    deleted_count = result.rowcount
                    total_deleted += deleted_count
                    print(f"🗑️ 删除了 {deleted_count} 个测试订阅")
                
                if tracker.project_ids:
                    # 删除项目
                    placeholders = ','.join(map(str, tracker.project_ids))
                    query = f"DELETE FROM project WHERE id IN ({placeholders})"
                    result = conn.execute(text(query))
                    deleted_count = result.rowcount
                    total_deleted += deleted_count
                    print(f"🗑️ 删除了 {deleted_count} 个测试项目")
                
                if tracker.folder_ids:
                    # 删除分类
                    placeholders = ','.join(map(str, tracker.folder_ids))
                    query = f"DELETE FROM folder WHERE id IN ({placeholders})"
                    result = conn.execute(text(query))
                    deleted_count = result.rowcount
                    total_deleted += deleted_count
                    print(f"🗑️ 删除了 {deleted_count} 个测试分类")
                
                if tracker.urllink_ids:
                    # 删除友情链接
                    placeholders = ','.join(map(str, tracker.urllink_ids))
                    query = f"DELETE FROM urllink WHERE id IN ({placeholders})"
                    result = conn.execute(text(query))
                    deleted_count = result.rowcount
                    total_deleted += deleted_count
                    print(f"🗑️ 删除了 {deleted_count} 个测试友情链接")
                
                if tracker.user_ids:
                    # 删除用户（最后删除，因为其他表可能引用用户）
                    placeholders = ','.join(map(str, tracker.user_ids))
                    query = f"DELETE FROM users WHERE id IN ({placeholders})"
                    result = conn.execute(text(query))
                    deleted_count = result.rowcount
                    total_deleted += deleted_count
                    print(f"🗑️ 删除了 {deleted_count} 个测试用户")
                
                # 提交事务
                trans.commit()
                print(f"✅ 基于ID的测试数据清理完成，共删除 {total_deleted} 条记录")
                
            except Exception as e:
                # 回滚事务
                trans.rollback()
                logger.error(f"Failed to cleanup test data by ID: {e}")
                raise
                
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise
    finally:
        sync_engine.dispose()

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
        result3 = session.execute(text("""
            DELETE FROM projectitem WHERE 
                name LIKE '%Test%' OR name LIKE '%test%' OR
                name LIKE '%Article%' OR name LIKE '%Comment%' OR
                name LIKE '%Message%' OR name LIKE '%Guest%' OR
                name LIKE '%Anonymous%' OR name LIKE '%Login%' OR
                name LIKE '%Required%' OR name LIKE '%Disabled%' OR
                id > 9000
        """))
        print(f"🗑️ 删除了 {result3.rowcount} 个测试文章")
        
        # 删除测试评论和留言（更全面的清理策略）
        result4 = session.execute(text("""
            DELETE FROM post WHERE 
                (content LIKE '%测试%' OR content LIKE '%test%' OR 
                 subject LIKE '%测试%' OR subject LIKE '%test%' OR
                 content LIKE '%Test%' OR subject LIKE '%Test%' OR
                 content LIKE '%留言本%' OR subject LIKE '%留言本%' OR
                 content LIKE '%主贴%' OR subject LIKE '%主贴%' OR
                 content LIKE '%留言%' OR subject LIKE '%留言%') AND
                (posttime > NOW() - INTERVAL '1 day' OR 
                 posttime = '2024-01-01 10:00:00' OR 
                 posttime = '2024-01-01 11:00:00' OR 
                 posttime = '2024-01-01 12:00:00' OR
                 posttime = '2024-01-01 11:01:00' OR
                 posttime = '2024-01-01 11:02:00' OR
                 posttime = '2024-01-01 11:03:00' OR
                 posttime = '2024-01-01 11:04:00' OR
                 posttime = '2024-01-01 11:05:00' OR
                 posttime = '2024-01-01 11:06:00' OR
                 posttime = '2024-01-01 11:07:00' OR
                 posttime = '2024-01-01 11:08:00' OR
                 posttime = '2024-01-01 11:09:00' OR
                 posttime = '2024-01-01 11:10:00')
        """))
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
        logger.error(f"Failed to cleanup test data: {e}")
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
        """提交事务 - 在测试环境中不提交"""
        # 在测试环境中不提交，让事务回滚处理
        pass
    
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
    """自动清理测试数据 - 在每个测试后运行（备用方案）"""
    yield
    # 注意：由于使用了事务回滚，这个清理逻辑主要是备用方案
    # 只有在事务回滚失败时才会执行
    try:
        cleanup_test_data(real_sync_engine)
    except Exception:
        pass

@pytest.fixture
def real_sync_session_with_commit(unified_db_manager):
    """创建真实PostgreSQL同步会话 - 使用统一数据库管理"""
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
            try:
                await savepoint.rollback()
            except (InvalidRequestError, StatementError) as e:
                # 如果事务已经关闭或状态无效，记录警告但继续执行
                logger.warning(f"Failed to rollback savepoint due to transaction state: {e}")
            except Exception as e:
                # 其他未预期的错误，记录错误信息
                logger.error(f"Unexpected error during savepoint rollback: {e}")

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
    """创建测试客户端 - 使用统一数据库管理"""
    from src.database import async_engine, async_session
    from src.main import app
    
    # 保存原始引擎和会话工厂
    original_engine = async_engine
    original_session = async_session
    
    # 创建会话工厂函数
    def create_test_async_session():
        return unified_db_manager.async_session
    
    # 替换为测试引擎和会话工厂
    import src.database
    src.database.async_engine = unified_db_manager.async_engine
    src.database.async_session = create_test_async_session
    
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
        # 如果缓存清理失败，记录警告但继续测试
        logger.warning(f"Failed to clear cache during test cleanup: {e}") 

@pytest.fixture
def test_data_tracker():
    """测试数据跟踪器"""
    tracker = TestDataTracker()
    yield tracker
    # 测试结束后清理跟踪的数据
    cleanup_test_data_by_ids(tracker)