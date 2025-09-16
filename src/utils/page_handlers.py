"""
页面路由处理器

提供静态页面路由的统一处理逻辑。
"""

from fastapi import APIRouter
from fastapi.responses import FileResponse
from typing import Optional


class PageHandler:
    """页面处理器类"""
    
    @staticmethod
    def create_page_router() -> APIRouter:
        """
        创建页面路由
        
        Returns:
            APIRouter: 页面路由实例
        """
        router = APIRouter()
        
        # 根路径和首页
        @router.get("/")
        async def root():
            """根路径和首页路由"""
            return FileResponse("src/static/index.html")
        
        # 博客页面
        @router.get("/blog/{project_id}")
        async def blog_page(project_id: int):
            """博客页面路由"""
            return FileResponse("src/static/blog.html")
        
        # 留言本页面
        @router.get("/messages")
        async def messages_page():
            """留言本页面路由"""
            return FileResponse("src/static/messages.html")
        
        # 留言本主题页面
        @router.get("/thread/{thread_id}")
        async def thread_page(thread_id: int):
            """留言本主题页面路由"""
            return FileResponse("src/static/thread.html")
        
        # 发表博客文章页面
        @router.get("/blog/{project_id}/create-post")
        async def create_post_page(project_id: int):
            """发表博客文章页面路由"""
            return FileResponse("src/static/create-post.html")
        
        # 编辑博客文章页面
        @router.get("/edit-article/{article_id}")
        async def edit_article_page(article_id: int):
            """编辑博客文章页面路由"""
            return FileResponse("src/static/edit-article.html")
        
        # 个人资料页面
        @router.get("/profile")
        @router.get("/profile/{user_id}")
        async def profile_page(user_id: Optional[int] = None):
            """个人资料页面路由"""
            return FileResponse("src/static/profile.html")
        
        # 注册码管理页面
        @router.get("/regkey")
        async def registration_code_page():
            """注册码管理页面路由"""
            return FileResponse("src/static/regkey.html")
        
        # 用户列表页面
        @router.get("/users")
        async def users_list_page():
            """用户列表页面路由"""
            return FileResponse("src/static/users.html")
        
        # 用户注册页面
        @router.get("/user_register")
        async def user_register_page():
            """用户注册页面路由"""
            return FileResponse("src/static/user_register.html")
        
        # 博客文章页面
        @router.get("/article/{article_id}")
        async def article_page(article_id: int):
            """博客文章页面路由"""
            return FileResponse("src/static/article.html")
        
        # 调试页面
        @router.get("/debug/article-api")
        async def debug_article_api():
            """调试文章API页面"""
            return FileResponse("debug_article_api.html")
        
        @router.get("/debug/image-display")
        async def debug_image_display():
            """调试图片显示页面"""
            return FileResponse("debug_image_display.html")
        
        return router

