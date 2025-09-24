"""
向量化管理控制器

提供向量化相关的管理API端点，包括：
- 手动触发向量化更新
- 批量向量化处理
- 向量化状态查询
- 向量化数据清理
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from typing import List, Dict, Any, Optional
from sqlmodel.ext.asyncio.session import AsyncSession

from src.database import get_async_session
from src.utils.auth_dependencies import get_current_user
from src.utils.permission_manager import permission_manager
from src.services.vectorization_update_service import get_vectorization_update_service

# 创建向量化管理API路由器
router = APIRouter(tags=["向量化管理"])


@router.post("/admin/vectorization/update/{article_id}")
async def update_article_vectorization(
    article_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    手动更新指定文章的向量化
    
    权限要求：管理员权限
    
    Args:
        article_id: 文章ID
        session: 数据库会话
        current_user: 当前登录用户信息
        
    Returns:
        Dict[str, Any]: 更新结果
    """
    # 权限检查
    if not permission_manager.can_manage_system(current_user):
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    try:
        vectorization_service = get_vectorization_update_service(session)
        
        # 获取文章信息
        from src.repositories.project_item_repository import ProjectItemRepository
        project_item_repo = ProjectItemRepository(session)
        article = await project_item_repo.get_by_id(article_id)
        
        if not article:
            raise HTTPException(status_code=404, detail="文章不存在")
        
        # 更新向量
        success = await vectorization_service.update_article_vectors(
            article_id, article.name, article.comment
        )
        
        if success:
            return {
                "message": "向量化更新成功",
                "article_id": article_id,
                "title": article.name
            }
        else:
            raise HTTPException(status_code=500, detail="向量化更新失败")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"向量化更新失败: {str(e)}")


@router.post("/admin/vectorization/batch-update")
async def batch_update_vectorization(
    article_ids: List[int] = Query(..., description="文章ID列表"),
    session: AsyncSession = Depends(get_async_session),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    批量更新文章向量化
    
    权限要求：管理员权限
    
    Args:
        article_ids: 文章ID列表
        session: 数据库会话
        current_user: 当前登录用户信息
        
    Returns:
        Dict[str, Any]: 批量更新结果
    """
    # 权限检查
    if not permission_manager.can_manage_system(current_user):
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    try:
        vectorization_service = get_vectorization_update_service(session)
        
        # 批量更新向量
        result = await vectorization_service.batch_update_articles(article_ids)
        
        return {
            "message": "批量向量化更新完成",
            "result": result
        }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量向量化更新失败: {str(e)}")


@router.get("/admin/vectorization/status/{article_id}")
async def get_vectorization_status(
    article_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    获取文章向量化状态
    
    权限要求：管理员权限
    
    Args:
        article_id: 文章ID
        session: 数据库会话
        current_user: 当前登录用户信息
        
    Returns:
        Dict[str, Any]: 向量化状态信息
    """
    # 权限检查
    if not permission_manager.can_manage_system(current_user):
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    try:
        vectorization_service = get_vectorization_update_service(session)
        
        # 获取向量化状态
        status = await vectorization_service.get_vectorization_status(article_id)
        
        return status
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取向量化状态失败: {str(e)}")


@router.delete("/admin/vectorization/delete/{article_id}")
async def delete_article_vectorization(
    article_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    删除文章向量化数据
    
    权限要求：管理员权限
    
    Args:
        article_id: 文章ID
        session: 数据库会话
        current_user: 当前登录用户信息
        
    Returns:
        Dict[str, Any]: 删除结果
    """
    # 权限检查
    if not permission_manager.can_manage_system(current_user):
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    try:
        vectorization_service = get_vectorization_update_service(session)
        
        # 删除向量
        success = await vectorization_service.delete_article_vectors(article_id)
        
        if success:
            return {
                "message": "向量化数据删除成功",
                "article_id": article_id
            }
        else:
            raise HTTPException(status_code=500, detail="向量化数据删除失败")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"向量化数据删除失败: {str(e)}")


@router.get("/admin/vectorization/stats")
async def get_vectorization_stats(
    session: AsyncSession = Depends(get_async_session),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    获取向量化统计信息
    
    权限要求：管理员权限
    
    Args:
        session: 数据库会话
        current_user: 当前登录用户信息
        
    Returns:
        Dict[str, Any]: 向量化统计信息
    """
    # 权限检查
    if not permission_manager.can_manage_system(current_user):
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    try:
        from sqlalchemy import text
        
        # 统计向量化数据
        stats_query = text("""
            SELECT 
                COUNT(*) as total_articles,
                COUNT(av.id) as vectorized_articles,
                COUNT(*) - COUNT(av.id) as unvectorized_articles,
                AVG(av.total_text_length) as avg_text_length,
                AVG(av.avg_confidence) as avg_confidence
            FROM projectitem pi
            LEFT JOIN article_vectors av ON pi.id = av.projectitem_id
            WHERE pi.itemtype != 3
        """)
        
        result = await session.execute(stats_query)
        row = result.fetchone()
        
        return {
            "total_articles": row[0] or 0,
            "vectorized_articles": row[1] or 0,
            "unvectorized_articles": row[2] or 0,
            "vectorization_rate": round((row[1] or 0) / (row[0] or 1) * 100, 2),
            "avg_text_length": round(row[3] or 0, 2),
            "avg_confidence": round(row[4] or 0, 2)
        }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取向量化统计失败: {str(e)}")


@router.post("/admin/vectorization/reindex-all")
async def reindex_all_articles(
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_async_session),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    重新索引所有文章（后台任务）
    
    权限要求：管理员权限
    
    Args:
        background_tasks: 后台任务
        session: 数据库会话
        current_user: 当前登录用户信息
        
    Returns:
        Dict[str, Any]: 任务启动结果
    """
    # 权限检查
    if not permission_manager.can_manage_system(current_user):
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    try:
        # 获取所有文章ID
        from sqlalchemy import text
        query = text("""
            SELECT id FROM projectitem 
            WHERE itemtype != 3
            ORDER BY id
        """)
        
        result = await session.execute(query)
        article_ids = [row[0] for row in result.fetchall()]
        
        if not article_ids:
            return {
                "message": "没有找到需要重新索引的文章",
                "total_articles": 0
            }
        
        # 添加后台任务
        background_tasks.add_task(reindex_articles_background, article_ids)
        
        return {
            "message": "重新索引任务已启动",
            "total_articles": len(article_ids),
            "status": "processing"
        }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动重新索引任务失败: {str(e)}")


async def reindex_articles_background(article_ids: List[int]):
    """后台重新索引文章"""
    try:
        from src.database import get_async_session
        from src.services.vectorization_update_service import get_vectorization_update_service
        
        async for session in get_async_session():
            vectorization_service = get_vectorization_update_service(session)
            
            # 批量更新向量
            result = await vectorization_service.batch_update_articles(article_ids)
            
            print(f"后台重新索引完成: {result}")
            break
            
    except Exception as e:
        print(f"后台重新索引失败: {e}")


# 普通用户向量化API端点
@router.post("/vectorization/update/{article_id}")
async def update_my_article_vectorization(
    article_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    更新自己文章的向量化
    
    权限要求：登录用户，只能更新自己的文章
    
    Args:
        article_id: 文章ID
        session: 数据库会话
        current_user: 当前登录用户信息
        
    Returns:
        Dict[str, Any]: 更新结果
    """
    try:
        vectorization_service = get_vectorization_update_service(session)
        
        # 获取文章信息并检查权限
        from src.repositories.project_item_repository import ProjectItemRepository
        project_item_repo = ProjectItemRepository(session)
        article = await project_item_repo.get_by_id(article_id)
        
        if not article:
            raise HTTPException(status_code=404, detail="文章不存在")
        
        # 检查用户是否有权限更新这篇文章
        # 管理员可以更新任何文章，普通用户只能更新自己的文章
        if not permission_manager.can_manage_system(current_user):
            if article.userid != current_user.get("id"):
                raise HTTPException(status_code=403, detail="只能更新自己的文章")
        
        # 更新向量
        success = await vectorization_service.update_article_vectors(
            article_id, article.name, article.comment
        )
        
        if success:
            return {
                "message": "向量化更新成功",
                "article_id": article_id,
                "title": article.name
            }
        else:
            raise HTTPException(status_code=500, detail="向量化更新失败")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"向量化更新失败: {str(e)}")


@router.get("/vectorization/status/{article_id}")
async def get_my_article_vectorization_status(
    article_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    获取自己文章的向量化状态
    
    权限要求：登录用户，只能查看自己的文章
    
    Args:
        article_id: 文章ID
        session: 数据库会话
        current_user: 当前登录用户信息
        
    Returns:
        Dict[str, Any]: 向量化状态信息
    """
    try:
        # 获取文章信息并检查权限
        from src.repositories.project_item_repository import ProjectItemRepository
        project_item_repo = ProjectItemRepository(session)
        article = await project_item_repo.get_by_id(article_id)
        
        if not article:
            raise HTTPException(status_code=404, detail="文章不存在")
        
        # 检查用户是否有权限查看这篇文章
        if not permission_manager.can_manage_system(current_user):
            if article.userid != current_user.get("id"):
                raise HTTPException(status_code=403, detail="只能查看自己的文章")
        
        vectorization_service = get_vectorization_update_service(session)
        
        # 获取向量化状态
        status = await vectorization_service.get_vectorization_status(article_id)
        
        return status
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取向量化状态失败: {str(e)}")
