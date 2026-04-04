"""
BlogN2 FastAPI 主应用

提供博客系统的核心API服务，包括：
- 用户管理：注册、登录、权限控制
- 博客管理：文章发布、编辑、删除
- 评论系统：文章评论、留言本
- 文件管理：图片上传、静态文件服务
- 缓存系统：Redis缓存、性能优化
- 权限管理：基于角色的访问控制

架构特点：
- 模块化设计：控制器、服务、仓储分层
- 统一错误处理：全局异常捕获和格式化
- 缓存优化：关键数据缓存提升性能
- 安全防护：路径遍历防护、文件类型验证
"""

import sys
import os
import logging
from pathlib import Path
from urllib.parse import urlparse
from contextlib import asynccontextmanager
import warnings

# 添加项目根目录到Python路径，确保模块导入正确
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 抑制已知的警告
warnings.filterwarnings("ignore", message="torch.utils._pytree._register_pytree_node is deprecated")
warnings.filterwarnings("ignore", message="The `use_auth_token` argument is deprecated")

from fastapi import FastAPI
import uvicorn

# 设置日志记录器
logger = logging.getLogger(__name__)

# 导入缓存相关模块
from src.utils.cache import cache_manager, cache_stats
from src.config.cache import cache_settings, validate_cache_config
from src.config.utils import get_config_file_path

# 导入工具类
from src.config.app import get_uvicorn_log_level
from src.utils.middleware_handlers import MiddlewareHandler
from src.utils.api_handlers import APIHandler
from src.utils.page_handlers import PageHandler
from src.services.model_cache import initialize_model_cache


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理器
    
    处理应用启动和关闭事件，包括缓存系统初始化。
    """
    # 启动事件：打印配置文件信息
    config_file = get_config_file_path()
    if config_file:
        logger.info(f"📄 使用配置文件: {config_file}")
    else:
        logger.info("📄 使用默认配置（未使用配置文件）")
    
    # 打印当前使用的数据库连接信息（不含密码，便于排查认证问题）
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        try:
            p = urlparse(db_url.replace("postgresql+asyncpg://", "http://").replace("postgresql://", "http://"))
            logger.warning(f"数据库连接: 主机={p.hostname} 端口={p.port or 5432} 用户={p.username}")
        except Exception:
            logger.warning("数据库连接: DATABASE_URL 已设置但解析失败，请检查格式")
    else:
        logger.warning("数据库连接: DATABASE_URL 未设置")
    
    # 验证缓存配置并初始化缓存系统
    config_info = validate_cache_config()
    logger.info(f"缓存配置已加载: Redis={config_info['redis_host']}:{config_info['redis_port']}, 缓存前缀={config_info['cache_prefix']}")
    
    await cache_manager.initialize()
    
    if cache_manager.is_available():
        logger.info("缓存系统初始化成功")
    else:
        logger.warning("缓存系统初始化失败，将使用无缓存模式")
    
    # BERT 模型路径（启动时输出，便于排查挂载与解析）
    from src.config.model import get_model_path
    model_path = get_model_path()
    host_path = os.getenv("BERT_MODEL_HOST_PATH")
    if host_path:
        logger.warning(f"BERT 模型: 宿主机路径={host_path} -> 容器内使用={model_path or '(未解析)'}")
    else:
        logger.warning(f"BERT 模型路径: {model_path or '(未设置，将使用 model_name)'}")
    # 预加载BERT模型（使用跨进程共享缓存）
    model_cache = await initialize_model_cache()
    if model_cache is not None:
        logger.info("BERT模型缓存初始化成功")
        app.state.model_cache = model_cache  # 供搜索等接口使用同一实例，避免请求时拿到错误模型
    else:
        logger.warning("BERT模型缓存初始化失败，搜索功能将使用降级方案")
        app.state.model_cache = None

    # 应用启动成功（使用 warning 级别，确保在 warning 日志级别下也能显示）
    logger.warning("✅ 应用启动成功，服务已就绪")

    yield
    
    # 关闭事件：清理资源
    logger.info("清理模型缓存...")
    from src.services.shared_model_cache import get_shared_model_cache
    shared_cache = get_shared_model_cache()
    shared_cache.cleanup()
    from src.services.vectorization_service import BERTVectorizationService
    BERTVectorizationService.shutdown_executor()


# 创建FastAPI应用实例
app = FastAPI(
    title="BlogN2 API",
    description="一个基于FastAPI的博客系统，支持用户管理、博客发布、评论系统等功能",
    version="1.0.0",
    lifespan=lifespan
)

# 配置中间件
MiddlewareHandler.setup_all_middleware(app)


# 注册所有路由
APIHandler.register_all_routes(app)

# 注册页面路由
page_router = PageHandler.create_page_router()
app.include_router(page_router)


# ==================== 应用启动 ====================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=get_uvicorn_log_level(),
        access_log=False  # 关闭HTTP请求日志
    ) 