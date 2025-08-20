"""
BlogN2 FastAPI 主应用

提供博客系统的核心API服务，包括用户管理、博客管理、缓存系统等。
"""

import sys
import os
from pathlib import Path
from contextlib import asynccontextmanager

# 添加项目根目录到Python路径，确保模块导入正确
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

# 导入API控制器模块
from src.controllers import metadata, user, blog, project, urllink

# 导入缓存相关模块
from src.utils.cache import cache_manager, cache_stats
from src.config.cache import cache_settings, validate_cache_config


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理器
    
    处理应用启动和关闭事件，包括缓存系统初始化。
    """
    # 启动事件：验证缓存配置并初始化缓存系统
    config_info = validate_cache_config()
    print(f"📋 缓存配置已加载: Redis={config_info['redis_host']}:{config_info['redis_port']}, 缓存前缀={config_info['cache_prefix']}")
    
    await cache_manager.initialize()
    
    if cache_manager.is_available():
        print("✅ 缓存系统初始化成功")
    else:
        print("⚠️  缓存系统初始化失败，将使用无缓存模式")
    
    yield
    
    # 关闭事件：清理资源（如需要）


# 创建FastAPI应用实例
app = FastAPI(
    title="BlogN2 API",
    description="一个基于FastAPI的博客系统，支持用户管理、博客发布、评论系统等功能",
    version="1.0.0",
    lifespan=lifespan
)

# 配置CORS中间件，允许跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该限制具体域名以提高安全性
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务配置
UPLOAD_BASE_PATH = "../pic/blogn_img/upload"
AVATAR_BASE_PATH = "../pic/blogn_img/userlogo"

# 挂载静态文件目录
app.mount("/static", StaticFiles(directory="src/static"), name="static")


def serve_file(file_path: str, media_type: str = None):
    """
    通用文件服务函数
    
    Args:
        file_path: 文件路径
        media_type: 媒体类型
        
    Returns:
        FileResponse: 文件响应
        
    Raises:
        HTTPException: 当文件不存在时抛出404错误
    """
    import os
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type=media_type)
    else:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="File not found")


def validate_and_sanitize_path(base_path: str, user_path: str) -> str:
    """
    验证和清理路径，防止路径遍历攻击
    
    Args:
        base_path: 基础路径
        user_path: 用户提供的路径
        
    Returns:
        str: 清理后的安全路径
        
    Raises:
        HTTPException: 当路径不安全时抛出400错误
    """
    import os
    from fastapi import HTTPException
    
    # 规范化路径
    normalized_path = os.path.normpath(user_path)
    
    # 检查路径是否包含路径遍历攻击
    if normalized_path.startswith('..') or normalized_path.startswith('/'):
        raise HTTPException(status_code=400, detail="Invalid path")
    
    # 构建完整路径
    full_path = os.path.join(base_path, normalized_path)
    
    # 确保最终路径在基础路径内
    if not os.path.abspath(full_path).startswith(os.path.abspath(base_path)):
        raise HTTPException(status_code=400, detail="Path traversal detected")
    
    return full_path


# ==================== 文件服务路由 ====================

@app.get("/upload/{file_path:path}")
async def serve_upload_file(file_path: str):
    """
    提供上传文件服务
    
    Args:
        file_path: 文件路径
        
    Returns:
        FileResponse: 文件响应
    """
    safe_path = validate_and_sanitize_path(UPLOAD_BASE_PATH, file_path)
    return serve_file(safe_path)


@app.get("/avatar/{file_path:path}")
async def serve_avatar_file(file_path: str):
    """
    提供用户头像文件服务
    
    Args:
        file_path: 文件路径
        
    Returns:
        FileResponse: 文件响应
    """
    safe_path = validate_and_sanitize_path(AVATAR_BASE_PATH, file_path)
    return serve_file(safe_path)


# ==================== API路由注册 ====================

# 注册API路由，统一使用/api前缀
app.include_router(metadata.router, prefix="/api")
app.include_router(user.router, prefix="/api")
app.include_router(blog.router, prefix="/api")
app.include_router(project.router, prefix="/api")
app.include_router(urllink.router, prefix="/api")


# ==================== 页面路由 ====================

@app.get("/")
async def root():
    """
    根路径和首页路由
    
    返回网站的首页HTML文件。
    
    Returns:
        FileResponse: 首页HTML文件
    """
    return FileResponse("src/static/index.html")


@app.get("/blog/{project_id}")
async def blog_page(project_id: int):
    """
    博客页面路由
    
    返回指定项目的博客页面HTML文件。
    
    Args:
        project_id: 项目ID
        
    Returns:
        FileResponse: 博客页面HTML文件
    """
    return FileResponse("src/static/blog.html")


# ==================== 系统端点 ====================

@app.get("/health")
async def health_check():
    """
    健康检查端点
    
    用于监控系统状态和负载均衡器健康检查。
    
    Returns:
        Dict[str, str]: 包含服务状态的字典
    """
    return {"status": "healthy", "service": "BlogN2 API"}


# ==================== 缓存管理端点 ====================

async def _ensure_cache_initialized():
    """确保缓存系统已初始化"""
    await cache_manager.initialize()


@app.get("/api/cache/status")
async def cache_status():
    """
    缓存状态检查端点
    
    返回缓存系统的当前状态和统计信息。
    
    Returns:
        Dict: 包含缓存状态和统计信息的字典
    """
    await _ensure_cache_initialized()
    
    return {
        "cache_enabled": cache_settings.enable_cache,
        "cache_available": cache_manager.is_available(),
        "cache_debug": cache_settings.cache_debug,
        "stats": cache_stats.get_stats()
    }


@app.post("/api/cache/clear")
async def clear_cache():
    """
    清除所有缓存端点
    
    清除系统中的所有缓存数据。
    
    Returns:
        Dict: 包含操作结果的字典
    """
    await _ensure_cache_initialized()
    
    if not cache_manager.is_available():
        return {"success": False, "message": "缓存系统不可用"}
    
    try:
        await cache_manager.clear_pattern("*")
        return {"success": True, "message": "缓存清除成功"}
    except Exception as e:
        return {"success": False, "message": f"缓存清除失败: {str(e)}"}


@app.get("/api/cache/stats")
async def get_cache_stats():
    """
    获取缓存统计信息端点
    
    返回详细的缓存统计信息和配置。
    
    Returns:
        Dict: 包含缓存统计和设置的字典
    """
    return {
        "stats": cache_stats.get_stats(),
        "settings": {
            "enable_cache": cache_settings.enable_cache,
            "cache_debug": cache_settings.cache_debug,
            "default_ttl": cache_settings.default_ttl,
            "max_ttl": cache_settings.max_ttl
        }
    }


# ==================== 应用启动 ====================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 