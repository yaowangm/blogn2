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
from typing import Any, AsyncGenerator, Dict, Generator
from unittest.mock import AsyncMock, MagicMock
from dotenv import load_dotenv
from sqlalchemy.exc import InvalidRequestError, StatementError

# 加载环境变量
load_dotenv()

# 配置日志记录器
logger = logging.getLogger(__name__)

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 始终从项目根目录加载 .env，保证 MODEL_MODEL_PATH 等配置生效（与运行 pytest 的 cwd 无关）
_env_file = project_root / ".env"
if _env_file.exists():
    load_dotenv(_env_file, override=False)

# 测试环境禁止回退到网络下载：本地路径失败时立即报错，避免长时间尝试连接 Hugging Face
os.environ["MODEL_FALLBACK_TO_HUGGINGFACE"] = "false"

# 测试环境不强制设备：get_model_device() 会根据 torch.cuda.get_arch_list() 判断当前 GPU 是否被 PyTorch 支持，不支持则自动用 CPU
# 若需强制 CPU 可设置 os.environ["MODEL_DEVICE"] = "cpu"

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

def _path_has_config_json(path):
    """判断目录下是否含 config.json（模型有效）。"""
    return bool(path and os.path.isdir(path) and os.path.isfile(os.path.join(path, "config.json")))


def _resolve_path_to_model_dir(path):
    """若 path 含 config.json 则返回 path，否则若为 hub 目录则尝试 snapshots/<rev>，否则返回 None。"""
    if not path or not os.path.isdir(path):
        return None
    path = os.path.abspath(os.path.expanduser(path.strip()))
    if _path_has_config_json(path):
        return path
    snapshots_dir = os.path.join(path, "snapshots")
    if os.path.isdir(snapshots_dir):
        try:
            for rev in sorted(os.listdir(snapshots_dir)):
                snapshot_path = os.path.join(snapshots_dir, rev)
                if _path_has_config_json(snapshot_path):
                    return snapshot_path
        except OSError:
            pass
    return None


def _get_test_local_model_path():
    """返回可用的本地模型路径（必须含 config.json）。优先 BERT_MODEL_HUB_HOST_PATH，其次 modelscope，再 HF 缓存。"""
    # .env 中常用于宿主机挂载的路径（Docker 用 MODEL_MODEL_PATH，宿主机可用此变量）
    hub_host = os.getenv("BERT_MODEL_HUB_HOST_PATH")
    if hub_host:
        resolved = _resolve_path_to_model_dir(hub_host)
        if resolved:
            return resolved
    if _path_has_config_json(_default_model_path_modelscope):
        return _default_model_path_modelscope
    resolved = _resolve_path_to_model_dir(_default_model_path_huggingface)
    if resolved:
        return resolved
    return None


def _configured_model_path_exists():
    """判断 .env 中配置的 MODEL_MODEL_PATH 在当前机器上是否存在且含 config.json。"""
    raw = os.getenv("MODEL_MODEL_PATH")
    if not raw or not raw.strip():
        return False
    path = os.path.expanduser(raw.strip())
    return _path_has_config_json(path)


try:
    # 先加载配置工具
    from src.config.utils import load_config_file, get_config_file_path
    # 加载配置文件（这会更新环境变量，但不会覆盖已存在的环境变量）
    config_path = load_config_file()
    if config_path:
        logger.info(f"测试环境使用配置文件: {config_path}")
    else:
        logger.debug("测试环境使用默认配置（未找到配置文件）")

    # 模型路径：优先使用 .env 中且在当前机器存在的路径；否则尝试本机可用路径（如 Docker 路径在宿主机不存在时）
    configured_exists = _configured_model_path_exists()
    if configured_exists:
        logger.info(f"测试环境使用配置中的模型路径: {os.getenv('MODEL_MODEL_PATH')}")
    else:
        had_configured_path = bool(os.getenv("MODEL_MODEL_PATH"))
        _test_local_model_path = _get_test_local_model_path()
        if _test_local_model_path:
            os.environ["MODEL_MODEL_PATH"] = _test_local_model_path
            os.environ["MODEL_PREFER_LOCAL"] = "true"
            os.environ["MODEL_FALLBACK_TO_HUGGINGFACE"] = "false"
            logger.info(
                f"测试环境：配置路径不可用，使用本机检测的模型路径: {_test_local_model_path}"
                if had_configured_path
                else f"测试环境使用自动检测的本地模型: {_test_local_model_path}"
            )
        elif os.getenv("MODEL_MODEL_PATH"):
            logger.warning(
                "测试环境：配置的模型路径在当前机器不存在（如 Docker 路径），且未检测到本机模型，BERT 相关测试将失败"
            )
        else:
            logger.warning(
                "本地模型路径不存在（已检查 modelscope 与 ~/.cache/huggingface/hub），BERT 相关测试将失败"
            )

except Exception as e:
    # 如果配置加载失败，记录但不中断测试
    logger.debug(f"配置加载初始化失败（测试环境）: {e}")
    import traceback
    logger.debug(traceback.format_exc())

    # 仅当未配置 MODEL_MODEL_PATH 时使用自动检测的路径
    if not os.getenv("MODEL_MODEL_PATH"):
        _test_local_model_path = _get_test_local_model_path()
        if _test_local_model_path:
            os.environ["MODEL_MODEL_PATH"] = _test_local_model_path
            os.environ["MODEL_PREFER_LOCAL"] = "true"
            os.environ["MODEL_FALLBACK_TO_HUGGINGFACE"] = "false"


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

def get_database_url() -> str:
    """当前 pytest 会话使用的数据库 URL（configure 后为临时测试库）。"""
    url = os.getenv("DATABASE_URL")
    if not url:
        raise ValueError("DATABASE_URL 环境变量未设置，请在 .env 文件中配置数据库连接信息")
    return url


def get_sync_database_url() -> str:
    return get_database_url().replace("+asyncpg", "+psycopg2")


def pytest_configure(config):
    """pytest 启动时创建独立临时库，避免写入 .env 中的生产库。"""
    if os.getenv("BLOGN_SKIP_TEST_DB_LIFECYCLE", "").strip().lower() in ("1", "true", "yes"):
        return
    from tests.db_lifecycle import provision_test_database

    provision_test_database()


def pytest_sessionfinish(session, exitstatus):
    """pytest 结束时删除临时测试库。"""
    if os.getenv("BLOGN_SKIP_TEST_DB_LIFECYCLE", "").strip().lower() in ("1", "true", "yes"):
        return
    from tests.db_lifecycle import destroy_test_database

    destroy_test_database()

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
        get_database_url(),
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
        get_sync_database_url(),
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
    os.environ["DATABASE_URL"] = get_database_url()

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