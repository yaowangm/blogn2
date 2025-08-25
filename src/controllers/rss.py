from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_async_session
from src.repositories.project_repository import ProjectRepository
from src.repositories.project_item_repository import ProjectItemRepository
from src.repositories.user_repository import UserRepository
from src.services.rss_service import RSSService
from src.utils.rss_generator import RSSGenerator
from src.config.app import get_base_url

# 创建RSS API路由器
router = APIRouter()

def get_rss_service(session: AsyncSession) -> RSSService:
    """获取RSS服务实例"""
    project_repo = ProjectRepository(session)
    project_item_repo = ProjectItemRepository(session)
    user_repo = UserRepository(session)
    return RSSService(project_repo, project_item_repo, user_repo)

def get_rss_generator() -> RSSGenerator:
    """获取RSS生成器实例"""
    # 从环境变量读取基础URL配置
    base_url = get_base_url()
    return RSSGenerator(base_url)

@router.get("/rss/site")
async def get_site_rss(
    limit: int = Query(20, ge=1, le=100, description="文章数量限制"),
    session: AsyncSession = Depends(get_async_session)
):
    """
    获取全站RSS订阅
    
    Args:
        limit: 文章数量限制，默认20，最大100
        session: 数据库会话
        
    Returns:
        RSS 2.0格式的XML响应
    """
    try:
        rss_service = get_rss_service(session)
        rss_generator = get_rss_generator()
        
        # 获取全站RSS数据
        rss_data = await rss_service.get_site_rss_data(limit)
        
        # 生成RSS XML
        rss_xml = rss_generator.generate_rss_xml(rss_data)
        
        return Response(
            content=rss_xml,
            media_type="application/xml",
            headers={
                "Content-Disposition": "attachment; filename=site-rss.xml",
                "Cache-Control": "public, max-age=1800"  # 缓存30分钟
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成全站RSS失败: {str(e)}")

@router.get("/rss/blog/{project_id}")
async def get_blog_rss(
    project_id: int,
    limit: int = Query(20, ge=1, le=100, description="文章数量限制"),
    session: AsyncSession = Depends(get_async_session)
):
    """
    获取指定博客的RSS订阅
    
    Args:
        project_id: 博客ID
        limit: 文章数量限制，默认20，最大100
        session: 数据库会话
        
    Returns:
        RSS 2.0格式的XML响应
    """
    try:
        rss_service = get_rss_service(session)
        rss_generator = get_rss_generator()
        
        # 获取博客RSS数据
        rss_data = await rss_service.get_blog_rss_data(project_id, limit)
        
        # 生成RSS XML
        rss_xml = rss_generator.generate_rss_xml(rss_data)
        
        return Response(
            content=rss_xml,
            media_type="application/xml",
            headers={
                "Content-Disposition": f"attachment; filename=blog-{project_id}-rss.xml",
                "Cache-Control": "public, max-age=1800"  # 缓存30分钟
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成博客RSS失败: {str(e)}")

@router.get("/rss/site/full")
async def get_site_rss_full(
    limit: int = Query(20, ge=1, le=100, description="文章数量限制"),
    session: AsyncSession = Depends(get_async_session)
):
    """
    获取全站RSS订阅（包含完整内容）
    
    Args:
        limit: 文章数量限制，默认20，最大100
        session: 数据库会话
        
    Returns:
        RSS 2.0格式的XML响应（包含完整内容）
    """
    try:
        rss_service = get_rss_service(session)
        rss_generator = get_rss_generator()
        
        # 获取全站RSS数据
        rss_data = await rss_service.get_site_rss_data(limit)
        
        # 生成包含完整内容的RSS XML
        rss_xml = rss_generator.generate_rss_xml_with_content(rss_data)
        
        return Response(
            content=rss_xml,
            media_type="application/xml",
            headers={
                "Content-Disposition": "attachment; filename=site-rss-full.xml",
                "Cache-Control": "public, max-age=1800"  # 缓存30分钟
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成全站RSS失败: {str(e)}")

@router.get("/rss/blog/{project_id}/full")
async def get_blog_rss_full(
    project_id: int,
    limit: int = Query(20, ge=1, le=100, description="文章数量限制"),
    session: AsyncSession = Depends(get_async_session)
):
    """
    获取指定博客的RSS订阅（包含完整内容）
    
    Args:
        project_id: 博客ID
        limit: 文章数量限制，默认20，最大100
        session: 数据库会话
        
    Returns:
        RSS 2.0格式的XML响应（包含完整内容）
    """
    try:
        rss_service = get_rss_service(session)
        rss_generator = get_rss_generator()
        
        # 获取博客RSS数据
        rss_data = await rss_service.get_blog_rss_data(project_id, limit)
        
        # 生成包含完整内容的RSS XML
        rss_xml = rss_generator.generate_rss_xml_with_content(rss_data)
        
        return Response(
            content=rss_xml,
            media_type="application/xml",
            headers={
                "Content-Disposition": f"attachment; filename=blog-{project_id}-rss-full.xml",
                "Cache-Control": "public, max-age=1800"  # 缓存30分钟
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成博客RSS失败: {str(e)}")
