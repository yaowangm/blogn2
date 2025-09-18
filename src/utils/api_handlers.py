"""
API路由处理器

提供API路由的统一注册和管理。
"""

from fastapi import FastAPI, UploadFile, File, Depends
from typing import Dict, Any

from src.controllers import metadata, user, blog, project, article, urllink, rss, auth, subscription, broadcast, global_stats
from src.routes import regkey, user_register
from src.utils.file_handlers import FileHandler
from src.utils.file_utils import validate_and_sanitize_path
from src.config.app import get_upload_dir


class APIHandler:
    """API路由处理器类"""
    
    @staticmethod
    def register_api_routes(app: FastAPI) -> None:
        """
        注册所有API路由
        
        Args:
            app: FastAPI应用实例
        """
        # 注册API路由，统一使用/api前缀
        app.include_router(metadata.router, prefix="/api")
        app.include_router(user.router, prefix="/api")
        app.include_router(blog.router, prefix="/api")
        app.include_router(project.router, prefix="/api")
        app.include_router(article.router, prefix="/api")
        app.include_router(urllink.router, prefix="/api")
        app.include_router(rss.router, prefix="/api")
        app.include_router(auth.router, prefix="/api")
        app.include_router(subscription.router, prefix="/api")
        app.include_router(broadcast.router, prefix="/api")
        app.include_router(global_stats.router, prefix="/api")
        app.include_router(regkey.router, prefix="/api")
        app.include_router(user_register.router, prefix="/api")
    
    @staticmethod
    def register_file_routes(app: FastAPI) -> None:
        """
        注册文件相关路由
        
        Args:
            app: FastAPI应用实例
        """
        # 静态文件服务配置
        UPLOAD_BASE_PATH = get_upload_dir()
        AVATAR_BASE_PATH = "../pic/blogn_img/userlogo"
        
        @app.get("/upload/{file_path:path}")
        async def serve_upload_file(file_path: str):
            """提供上传文件服务"""
            safe_path = validate_and_sanitize_path(UPLOAD_BASE_PATH, file_path)
            return FileHandler.serve_file(safe_path)
        
        @app.get("/avatar/{file_path:path}")
        async def serve_avatar_file(file_path: str):
            """提供用户头像文件服务"""
            safe_path = validate_and_sanitize_path(AVATAR_BASE_PATH, file_path)
            return FileHandler.serve_file(safe_path)
        
        @app.post("/api/upload")
        async def upload_file(file: UploadFile = File(...), temp: bool = False):
            """文件上传API"""
            result = await FileHandler.process_upload_file(file, temp)
            result["original_name"] = file.filename
            return result
        
        @app.get("/api/temp-upload/{filename}")
        async def serve_temp_file(filename: str):
            """提供临时文件服务"""
            safe_filename = FileHandler.sanitize_filename(filename)
            temp_dir = FileHandler.get_temp_dir()
            file_path = f"{temp_dir}/{safe_filename}"
            return FileHandler.serve_file(file_path)
        
        @app.delete("/api/temp-upload/{filename}")
        async def delete_temp_file(filename: str):
            """删除临时文件"""
            return await FileHandler.delete_temp_file(filename)
    
    @staticmethod
    def register_system_routes(app: FastAPI) -> None:
        """
        注册系统相关路由
        
        Args:
            app: FastAPI应用实例
        """
        from src.utils.cache import cache_manager, cache_stats
        from src.config.cache import cache_settings
        
        @app.get("/health")
        async def health_check():
            """健康检查端点"""
            return {"status": "healthy", "service": "BlogN2 API"}
        
        @app.get("/api/cache/status")
        async def cache_status():
            """缓存状态检查端点"""
            return {
                "cache_enabled": cache_settings.enable_cache,
                "cache_available": cache_manager.is_available(),
                "cache_debug": cache_settings.cache_debug,
                "stats": cache_stats.get_stats()
            }
        
        @app.post("/api/cache/clear")
        async def clear_cache():
            """清除所有缓存端点"""
            if not cache_manager.is_available():
                return {"success": False, "message": "缓存系统不可用"}
            
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
    
    @staticmethod
    def register_all_routes(app: FastAPI) -> None:
        """
        注册所有路由
        
        Args:
            app: FastAPI应用实例
        """
        APIHandler.register_api_routes(app)
        APIHandler.register_file_routes(app)
        APIHandler.register_system_routes(app)

