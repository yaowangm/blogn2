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
from src.controllers import metadata, user, blog, project

# 导入缓存相关模块
from src.utils.cache import cache_manager, cache_stats
from src.config.cache import cache_settings, validate_cache_config


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理器
    
    处理应用启动和关闭事件
    """
    # 启动事件
    # 验证缓存配置
    config_info = validate_cache_config()
    print(f"📋 缓存配置已加载: Redis={config_info['redis_host']}:{config_info['redis_port']}, 缓存前缀={config_info['cache_prefix']}")
    
    await cache_manager.initialize()
    
    if cache_manager.is_available():
        print("✅ 缓存系统初始化成功")
    else:
        print("⚠️  缓存系统初始化失败，将使用无缓存模式")
    
    yield
    
    # 关闭事件（如果需要清理资源）


# 创建FastAPI应用实例
app = FastAPI(
    title="BlogN2 API",
    description="一个基于FastAPI的博客系统",
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

# 文件服务配置
UPLOAD_BASE_PATH = "../pic/blogn_img/upload"
AVATAR_BASE_PATH = "../pic/blogn_img/userlogo"

def serve_file(file_path: str, media_type: str = None):
    """
    通用文件服务函数
    
    Args:
        file_path: 文件路径
        media_type: 媒体类型
        
    Returns:
        FileResponse: 文件响应
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
    
    # 检查是否包含路径遍历序列
    if '..' in normalized_path or normalized_path.startswith('/'):
        raise HTTPException(status_code=400, detail="Invalid path")
    
    # 构建完整路径
    full_path = os.path.join(base_path, normalized_path)
    
    # 确保最终路径在基础路径内
    try:
        full_path = os.path.abspath(full_path)
        base_path_abs = os.path.abspath(base_path)
        if not full_path.startswith(base_path_abs):
            raise HTTPException(status_code=400, detail="Path traversal detected")
    except (OSError, ValueError):
        raise HTTPException(status_code=400, detail="Invalid path")
    
    return full_path

# 自定义upload文件路由 - 必须在静态文件挂载之前
@app.get("/static/upload/{path:path}")
async def serve_upload_file(path: str):
    """
    提供upload文件访问
    
    Args:
        path: 文件路径
        
    Returns:
        FileResponse: 文件
    """
    safe_path = validate_and_sanitize_path(UPLOAD_BASE_PATH, path)
    return serve_file(safe_path)

# 添加HEAD方法支持
@app.head("/static/upload/{path:path}")
async def serve_upload_file_head(path: str):
    """
    提供upload文件HEAD请求支持
    
    Args:
        path: 文件路径
        
    Returns:
        FileResponse: 文件头信息
    """
    safe_path = validate_and_sanitize_path(UPLOAD_BASE_PATH, path)
    return serve_file(safe_path)

# 挂载静态文件目录，提供前端资源访问
app.mount("/static", StaticFiles(directory="src/static"), name="static")

# 挂载用户头像目录，直接指向实际路径
# app.mount("/static/userlogo", StaticFiles(directory="../pic/blogn_img/userlogo"), name="userlogo")

# 自定义头像文件路由
@app.get("/avatars/{prefix}/{filename}")
async def serve_avatar(prefix: str, filename: str):
    """
    提供用户头像文件访问
    
    Args:
        prefix: 用户ID前缀
        filename: 头像文件名
        
    Returns:
        FileResponse: 头像文件
    """
    # 验证prefix和filename参数
    if not prefix.isdigit() or not filename:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Invalid avatar parameters")
    
    # 构建头像路径并验证
    avatar_path = f"{prefix}/{filename}"
    safe_path = validate_and_sanitize_path(AVATAR_BASE_PATH, avatar_path)
    return serve_file(safe_path, media_type="image/jpeg")

# 注册API路由，统一使用/api前缀
app.include_router(metadata.router, prefix="/api")
app.include_router(user.router, prefix="/api")
app.include_router(blog.router, prefix="/api")
app.include_router(project.router, prefix="/api")

# 根路径和首页路由 - 都返回首页
@app.get("/")
@app.get("/index.html")
async def root():
    """
    根路径和首页路由
    
    返回网站的首页HTML文件。
    
    Returns:
        FileResponse: 首页HTML文件
    """
    return FileResponse("src/static/index.html")


# 博客页面路由
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



# 健康检查端点
@app.get("/health")
async def health_check():
    """
    健康检查端点
    
    用于监控系统状态和负载均衡器健康检查。
    
    Returns:
        Dict[str, str]: 包含服务状态的字典
    """
    return {"status": "healthy", "service": "BlogN2 API"}


# 缓存管理端点
async def _ensure_cache_initialized():
    """确保缓存系统已初始化"""
    await cache_manager.initialize()


@app.get("/api/cache/status")
async def cache_status():
    """缓存状态检查端点"""
    await _ensure_cache_initialized()
    
    return {
        "cache_enabled": cache_settings.enable_cache,
        "cache_available": cache_manager.is_available(),
        "cache_debug": cache_settings.cache_debug,
        "stats": cache_stats.get_stats()
    }


@app.post("/api/cache/clear")
async def clear_cache():
    """清除所有缓存端点"""
    await _ensure_cache_initialized()
    
    if not cache_manager.is_available():
        return {"success": False, "message": "缓存系统不可用"}
    
    # 清除所有缓存
    try:
        await cache_manager.clear_pattern("*")
        return {"success": True, "message": "缓存清除成功"}
    except Exception as e:
        return {"success": False, "message": f"缓存清除失败: {str(e)}"}


@app.get("/api/cache/stats")
async def get_cache_stats():
    """获取缓存统计信息端点"""
    return {
        "stats": cache_stats.get_stats(),
        "settings": {
            "enable_cache": cache_settings.enable_cache,
            "cache_debug": cache_settings.cache_debug,
            "default_ttl": cache_settings.default_ttl,
            "max_ttl": cache_settings.max_ttl
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 