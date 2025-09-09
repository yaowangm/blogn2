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

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

# 导入API控制器模块
from src.controllers import metadata, user, blog, project, article, urllink, rss, auth
from src.routes import regkey

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

# 添加缓存控制中间件
@app.middleware("http")
async def add_cache_control_headers(request, call_next):
    """
    为敏感API添加缓存控制头的中间件
    """
    response = await call_next(request)
    
    # 为敏感的个人资料相关API添加缓存控制
    if request.url.path.startswith("/api/users/") or request.url.path.startswith("/api/projects/user/"):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, private"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    
    return response

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


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    文件上传API
    
    Args:
        file: 上传的文件
        
    Returns:
        Dict: 包含文件信息的响应
    """
    import os
    import uuid
    from datetime import datetime
    from fastapi import HTTPException
    
    # 检查文件类型
    allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif']
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="只支持jpg、png、gif格式的图片")
    
    # 检查文件大小（1MB = 1048576字节）
    file_content = await file.read()
    if len(file_content) > 1048576:
        raise HTTPException(status_code=400, detail="图片大小不能超过1MB")
    
    # 生成唯一文件名
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in ['.jpg', '.jpeg', '.png', '.gif']:
        raise HTTPException(status_code=400, detail="不支持的文件扩展名")
    
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    
    # 创建按月份命名的子目录（格式：YYYYMM）
    current_time = datetime.now()
    month_dir = current_time.strftime("%Y%m")
    monthly_upload_path = os.path.join(UPLOAD_BASE_PATH, month_dir)
    
    # 确保上传目录和月份子目录存在
    os.makedirs(monthly_upload_path, exist_ok=True)
    
    # 保存文件到月份子目录
    file_path = os.path.join(monthly_upload_path, unique_filename)
    # 生成相对路径（用于存储到数据库）
    relative_path = f"{month_dir}/{unique_filename}"
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)
        
        return {
            "success": True,
            "filename": unique_filename,
            "original_name": file.filename,
            "size": len(file_content),
            "url": f"/upload/{relative_path}",
            "relative_path": relative_path
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")


# ==================== API路由注册 ====================

# 注册API路由，统一使用/api前缀
app.include_router(metadata.router, prefix="/api")
app.include_router(user.router, prefix="/api")
app.include_router(blog.router, prefix="/api")
app.include_router(project.router, prefix="/api")
app.include_router(article.router, prefix="/api")
app.include_router(urllink.router, prefix="/api")
app.include_router(rss.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
# 注册码管理路由
app.include_router(regkey.router, prefix="/api")
# 用户注册路由
from src.routes import user_register
app.include_router(user_register.router, prefix="/api")




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


@app.get("/blog/{project_id}/create-post")
async def create_post_page(project_id: int):
    """
    发表博客文章页面路由
    
    返回发表博客文章的页面HTML文件。
    
    Args:
        project_id: 项目ID
        
    Returns:
        FileResponse: 发表博客文章页面HTML文件
    """
    return FileResponse("src/static/create-post.html")


@app.get("/profile")
@app.get("/profile/{user_id}")
async def profile_page(user_id: int = None):
    """
    个人资料页面路由
    
    支持两种访问方式：
    1. /profile - 显示当前登录用户的个人资料
    2. /profile/{user_id} - 显示指定用户的个人资料
    
    Args:
        user_id: 用户ID，可选参数
        
    Returns:
        FileResponse: 个人资料页面HTML文件
    """
    return FileResponse("src/static/profile.html")


@app.get("/regkey")
async def registration_code_page():
    """
    注册码管理页面路由
    
    注意：此页面需要用户登录，前端会进行认证检查
    如果未登录用户访问，前端会重定向到首页
    
    Returns:
        FileResponse: 注册码管理页面HTML文件
    """
    return FileResponse("src/static/regkey.html")


@app.get("/users")
async def users_list_page():
    """
    用户列表页面路由
    
    注意：此页面需要管理员权限，前端会进行权限检查
    如果非管理员用户访问，前端会重定向到首页
    
    Returns:
        FileResponse: 用户列表页面HTML文件
    """
    return FileResponse("src/static/users.html")


@app.get("/user_register")
async def user_register_page():
    """
    用户注册页面路由
    
    注意：此页面不需要用户登录，任何人都可以访问
    
    Returns:
        FileResponse: 用户注册页面HTML文件
    """
    return FileResponse("src/static/user_register.html")





@app.get("/article/{article_id}")
async def article_page(article_id: int):
    """
    博客文章页面路由
    
    返回指定文章的详情页面HTML文件。
    
    Args:
        article_id: 文章ID
        
    Returns:
        FileResponse: 文章页面HTML文件
    """
    return FileResponse("src/static/article.html")


@app.get("/debug/article-api")
async def debug_article_api():
    """
    调试文章API页面
    
    返回调试页面HTML文件。
    
    Returns:
        FileResponse: 调试页面HTML文件
    """
    return FileResponse("debug_article_api.html")


@app.get("/debug/image-display")
async def debug_image_display():
    """
    调试图片显示页面
    
    返回调试页面HTML文件。
    
    Returns:
        FileResponse: 调试页面HTML文件
    """
    return FileResponse("debug_image_display.html")


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