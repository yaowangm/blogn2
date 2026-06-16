from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_async_session
from src.repositories.project_repository import ProjectRepository
from src.repositories.project_item_repository import ProjectItemRepository
from src.repositories.user_repository import UserRepository
from src.services.rss_service import RSSService
from src.utils.rss_generator import RSSGenerator
from src.config.app import get_base_url
from src.utils.cache import (
    cache_site_rss, cache_blog_rss, cache_site_rss_full, cache_blog_rss_full
)

router = APIRouter()

def get_rss_service(session: AsyncSession) -> RSSService:
    project_repo = ProjectRepository(session)
    project_item_repo = ProjectItemRepository(session)
    user_repo = UserRepository(session)
    return RSSService(project_repo, project_item_repo, user_repo)

def get_rss_generator() -> RSSGenerator:
    base_url = get_base_url()
    return RSSGenerator(base_url)


def _rss_response(rss_xml: str, filename: str) -> Response:
    return Response(
        content=rss_xml,
        media_type="application/xml",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Cache-Control": "public, max-age=1800",
        },
    )


@cache_site_rss()
async def build_site_rss_xml(limit: int, session: AsyncSession) -> str:
    rss_service = get_rss_service(session)
    rss_generator = get_rss_generator()
    rss_data = await rss_service.get_site_rss_data(limit)
    return rss_generator.generate_rss_xml(rss_data)


@cache_blog_rss()
async def build_blog_rss_xml(project_id: int, limit: int, session: AsyncSession) -> str:
    rss_service = get_rss_service(session)
    rss_generator = get_rss_generator()
    rss_data = await rss_service.get_blog_rss_data(project_id, limit)
    return rss_generator.generate_rss_xml(rss_data)


@cache_site_rss_full()
async def build_site_rss_full_xml(limit: int, session: AsyncSession) -> str:
    rss_service = get_rss_service(session)
    rss_generator = get_rss_generator()
    rss_data = await rss_service.get_site_rss_data(limit)
    return rss_generator.generate_rss_xml_with_content(rss_data)


@cache_blog_rss_full()
async def build_blog_rss_full_xml(project_id: int, limit: int, session: AsyncSession) -> str:
    rss_service = get_rss_service(session)
    rss_generator = get_rss_generator()
    rss_data = await rss_service.get_blog_rss_data(project_id, limit)
    return rss_generator.generate_rss_xml_with_content(rss_data)


@router.get("/rss/site")
async def get_site_rss(
    limit: int = Query(20, ge=1, le=100, description="文章数量限制"),
    session: AsyncSession = Depends(get_async_session)
):
    """获取全站RSS订阅"""
    try:
        rss_xml = await build_site_rss_xml(limit=limit, session=session)
        return _rss_response(rss_xml, "site-rss.xml")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成全站RSS失败: {str(e)}")


@router.get("/rss/blog/{project_id}")
async def get_blog_rss(
    project_id: int,
    limit: int = Query(20, ge=1, le=100, description="文章数量限制"),
    session: AsyncSession = Depends(get_async_session)
):
    """获取指定博客的RSS订阅"""
    try:
        rss_xml = await build_blog_rss_xml(project_id=project_id, limit=limit, session=session)
        return _rss_response(rss_xml, f"blog-{project_id}-rss.xml")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成博客RSS失败: {str(e)}")


@router.get("/rss/site/full")
async def get_site_rss_full(
    limit: int = Query(20, ge=1, le=100, description="文章数量限制"),
    session: AsyncSession = Depends(get_async_session)
):
    """获取全站RSS订阅（包含完整内容）"""
    try:
        rss_xml = await build_site_rss_full_xml(limit=limit, session=session)
        return _rss_response(rss_xml, "site-rss-full.xml")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成全站RSS失败: {str(e)}")


@router.get("/rss/blog/{project_id}/full")
async def get_blog_rss_full(
    project_id: int,
    limit: int = Query(20, ge=1, le=100, description="文章数量限制"),
    session: AsyncSession = Depends(get_async_session)
):
    """获取指定博客的RSS订阅（包含完整内容）"""
    try:
        rss_xml = await build_blog_rss_full_xml(project_id=project_id, limit=limit, session=session)
        return _rss_response(rss_xml, f"blog-{project_id}-rss-full.xml")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成博客RSS失败: {str(e)}")
