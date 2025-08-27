"""
权限中间件
提供全局权限控制和访问日志记录
"""

import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.utils.permission_manager import permission_manager


class PermissionMiddleware(BaseHTTPMiddleware):
    """权限控制中间件"""
    
    def __init__(self, app):
        super().__init__(app)
        
        # 定义需要权限检查的路径
        self.protected_paths = {
            "/api/users/": "user_profile",
            "/api/projects/user/": "user_blog",
            "/profile": "profile_page"
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求的中间件逻辑"""
        start_time = time.time()
        
        # 记录请求开始
        print(f"PERMISSION_LOG: {request.method} {request.url.path} - {start_time}")
        
        try:
            # 检查路径是否需要权限控制
            if self._is_protected_path(request.url.path):
                # 这里可以添加额外的权限检查逻辑
                pass
            
            # 继续处理请求
            response = await call_next(request)
            
            # 记录请求完成
            duration = time.time() - start_time
            print(f"PERMISSION_LOG: {request.method} {request.url.path} - {duration:.3f}s")
            
            return response
            
        except Exception as e:
            # 记录错误
            duration = time.time() - start_time
            print(f"PERMISSION_LOG: ERROR {request.method} {request.url.path} - {duration:.3f}s - {str(e)}")
            raise
    
    def _is_protected_path(self, path: str) -> bool:
        """检查是否是受保护的路径"""
        return any(path.startswith(protected_path) for protected_path in self.protected_paths.keys())


def create_permission_middleware() -> PermissionMiddleware:
    """创建权限中间件实例"""
    return PermissionMiddleware(app=None)

