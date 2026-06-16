"""
页面路由处理器

提供静态页面路由的统一处理逻辑。
"""

from pathlib import Path
from typing import Awaitable, Callable, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from sqlmodel.ext.asyncio.session import AsyncSession

from src.database import get_async_session
from src.config.app import get_base_url
from src.utils.static_assets import build_versioned_html_response
from src.utils.share_preview import (
    ArticleShareMeta,
    get_request_public_base_url,
    inject_article_share_preview,
    merge_public_base_with_config,
    load_article_share_meta,
    load_blog_share_meta,
    load_thread_share_meta,
)


class PageHandler:
    """页面处理器类"""

    @staticmethod
    def _get_static_file_path(filename: str) -> str:
        """
        获取静态文件的绝对路径

        Args:
            filename: 文件名

        Returns:
            str: 文件的绝对路径
        """
        # 获取项目根目录（从当前文件位置推断）
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent
        static_file = project_root / "src" / "static" / filename
        return str(static_file.resolve())

    @staticmethod
    def _serve_static_html(filename: str) -> HTMLResponse:
        """读取静态 HTML 模板并注入资源版本号，避免浏览器缓存旧页面。"""
        static_path = PageHandler._get_static_file_path(filename)
        with open(static_path, encoding="utf-8") as f:
            template = f.read()
        return build_versioned_html_response(template)

    @staticmethod
    async def _maybe_share_preview_html(
        request: Request,
        session: AsyncSession,
        *,
        static_filename: str,
        load_share_meta: Callable[
            [AsyncSession, int], Awaitable[Optional[ArticleShareMeta]]
        ],
        resource_id: int,
        not_found_detail: str,
        og_type: str = "article",
    ) -> HTMLResponse:
        """
        对文章 / 博客首页 / 留言主题页：始终返回注入分享 meta 与站点 icon 后的 HTML，
        不依赖 User-Agent（微信等抓取端 UA 多变，与浏览器共用同一路径）。

        资源不存在时 ``load_share_meta`` 返回 None，则 ``404``。
        """
        static_path = PageHandler._get_static_file_path(static_filename)
        meta = await load_share_meta(session, resource_id)
        if meta is None:
            raise HTTPException(status_code=404, detail=not_found_detail)
        with open(static_path, encoding="utf-8") as f:
            template = f.read()
        public_base = merge_public_base_with_config(
            get_request_public_base_url(
                url_scheme=request.url.scheme,
                url_netloc=request.url.netloc,
                headers=dict(request.headers),
            ),
            get_base_url(),
        )
        html = inject_article_share_preview(
            template,
            meta,
            og_type=og_type,
            public_base_url=public_base,
        )
        return build_versioned_html_response(html)

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
            return PageHandler._serve_static_html("index.html")

        # 博客页面
        @router.get("/blog/{project_id}")
        async def blog_page(
            project_id: int,
            request: Request,
            session: AsyncSession = Depends(get_async_session),
        ):
            """博客页面路由（社交爬虫请求返回带 Open Graph 的 HTML）"""
            return await PageHandler._maybe_share_preview_html(
                request,
                session,
                static_filename="blog.html",
                load_share_meta=load_blog_share_meta,
                resource_id=project_id,
                not_found_detail="项目不存在",
                og_type="website",
            )

        # 留言本页面
        @router.get("/messages")
        async def messages_page():
            """留言本页面路由"""
            return PageHandler._serve_static_html("messages.html")

        # 留言本主题页面
        @router.get("/thread/{thread_id}")
        async def thread_page(
            thread_id: int,
            request: Request,
            session: AsyncSession = Depends(get_async_session),
        ):
            """留言本主题页面（社交爬虫请求返回带 Open Graph 的 HTML）"""
            return await PageHandler._maybe_share_preview_html(
                request,
                session,
                static_filename="thread.html",
                load_share_meta=load_thread_share_meta,
                resource_id=thread_id,
                not_found_detail="主题不存在",
                og_type="article",
            )

        # 发表博客文章页面
        @router.get("/blog/{project_id}/create-post")
        async def create_post_page(project_id: int):
            """发表博客文章页面路由"""
            return PageHandler._serve_static_html("create-post.html")

        # 编辑博客文章页面
        @router.get("/edit-article/{article_id}")
        async def edit_article_page(article_id: int):
            """编辑博客文章页面路由"""
            return PageHandler._serve_static_html("edit-article.html")

        # 个人资料页面
        @router.get("/profile")
        @router.get("/profile/{user_id}")
        async def profile_page(user_id: Optional[int] = None):
            """个人资料页面路由"""
            return PageHandler._serve_static_html("profile.html")

        # 注册码管理页面
        @router.get("/regkey")
        async def registration_code_page():
            """注册码管理页面路由"""
            return PageHandler._serve_static_html("regkey.html")

        # 用户列表页面
        @router.get("/users")
        async def users_list_page():
            """用户列表页面路由"""
            return PageHandler._serve_static_html("users.html")

        # 用户注册页面
        @router.get("/user_register")
        async def user_register_page():
            """用户注册页面路由"""
            return PageHandler._serve_static_html("user_register.html")

        # 忘记密码页面
        @router.get("/forgot-password")
        async def forgot_password_page():
            """忘记密码页面路由"""
            return PageHandler._serve_static_html("forgot-password.html")

        # 重置密码页面
        @router.get("/reset-password")
        async def reset_password_page():
            """重置密码页面路由"""
            return PageHandler._serve_static_html("reset-password.html")

        # 博客文章页面
        @router.get("/article/{article_id}")
        async def article_page(
            article_id: int,
            request: Request,
            session: AsyncSession = Depends(get_async_session),
        ):
            """博客文章页面路由（社交爬虫请求返回带 Open Graph 的 HTML）"""
            return await PageHandler._maybe_share_preview_html(
                request,
                session,
                static_filename="article.html",
                load_share_meta=load_article_share_meta,
                resource_id=article_id,
                not_found_detail="文章不存在",
                og_type="article",
            )

        # 订阅的博客页面
        @router.get("/blog/{project_id}/subscriptions")
        async def subscriptions_page(project_id: int):
            """订阅的博客页面路由"""
            return PageHandler._serve_static_html("subscriptions.html")

        # 分类维护页面
        @router.get("/blog/{project_id}/categories/maintenance")
        async def category_maintenance_page(project_id: int):
            """分类维护页面路由"""
            return PageHandler._serve_static_html("category-maintenance.html")

        # 管理友情链接页面
        @router.get("/manage-friend-links")
        async def manage_friend_links_page():
            """管理友情链接页面路由"""
            return PageHandler._serve_static_html("manage-friend-links.html")

        # 调试页面（这些文件可能在项目根目录）
        @router.get("/debug/article-api")
        async def debug_article_api():
            """调试文章API页面"""
            # 调试文件可能在项目根目录
            current_file = Path(__file__)
            project_root = current_file.parent.parent.parent
            debug_file = project_root / "debug_article_api.html"
            return FileResponse(str(debug_file.resolve()))

        @router.get("/debug/image-display")
        async def debug_image_display():
            """调试图片显示页面"""
            # 调试文件可能在项目根目录
            current_file = Path(__file__)
            project_root = current_file.parent.parent.parent
            debug_file = project_root / "debug_image_display.html"
            return FileResponse(str(debug_file.resolve()))

        # 搜索页面
        @router.get("/search")
        async def search_page():
            """搜索页面路由"""
            return PageHandler._serve_static_html("search.html")

        return router

