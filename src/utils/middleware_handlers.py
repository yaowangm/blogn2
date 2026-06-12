"""
中间件处理器

提供应用中间件的统一配置和管理。
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.utils.cache import cache_manager, cache_stats
from src.config.cache import cache_settings
from src.config.app import (
    get_cors_allow_origins,
    get_cors_allow_methods,
    get_cors_allow_headers,
    get_cors_allow_credentials,
)
from src.utils.static_assets import apply_static_cache_headers


class MiddlewareHandler:
    """中间件处理器类"""

    @staticmethod
    def setup_cors_middleware(app: FastAPI) -> None:
        """
        配置CORS中间件

        Args:
            app: FastAPI应用实例
        """
        app.add_middleware(
            CORSMiddleware,
            allow_origins=get_cors_allow_origins(),
            allow_credentials=get_cors_allow_credentials(),
            allow_methods=get_cors_allow_methods(),
            allow_headers=get_cors_allow_headers(),
        )

    @staticmethod
    def setup_cache_control_middleware(app: FastAPI) -> None:
        """
        配置缓存控制中间件

        Args:
            app: FastAPI应用实例
        """
        @app.middleware("http")
        async def add_cache_control_headers(request: Request, call_next):
            """
            为敏感API添加缓存控制头的中间件
            """
            response = await call_next(request)

            # 为敏感的个人资料相关API添加缓存控制
            if request.url.path.startswith("/api/users/") or request.url.path.startswith("/api/projects/user/"):
                response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, private"
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"

            # 重置密码页包含敏感 token，避免 Referer 传播
            if request.url.path.startswith("/reset-password"):
                response.headers["Referrer-Policy"] = "no-referrer"

            path = request.url.path
            if path.startswith("/static/"):
                apply_static_cache_headers(
                    response,
                    path,
                    request.url.query,
                )
            elif "text/html" in response.headers.get("content-type", ""):
                response.headers["Cache-Control"] = "no-cache, must-revalidate"
                response.headers["Pragma"] = "no-cache"

            return response

    @staticmethod
    def setup_static_files(app: FastAPI) -> None:
        """
        配置静态文件服务

        Args:
            app: FastAPI应用实例
        """
        from pathlib import Path
        static_dir = Path("src/static")
        if static_dir.exists() and static_dir.is_dir():
            app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
        else:
            # 如果目录不存在，创建它（用于测试环境）
            static_dir.mkdir(parents=True, exist_ok=True)
            app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @staticmethod
    def setup_all_middleware(app: FastAPI) -> None:
        """
        配置所有中间件

        Args:
            app: FastAPI应用实例
        """
        MiddlewareHandler.setup_cors_middleware(app)
        MiddlewareHandler.setup_cache_control_middleware(app)
        MiddlewareHandler.setup_static_files(app)

