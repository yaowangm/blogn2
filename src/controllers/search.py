"""
搜索控制器
实现基于BERT向量的智能搜索功能
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import Optional, Dict, Any

from src.database import get_async_session
from src.utils.auth_dependencies import get_optional_current_user
from src.services.model_cache import get_cached_model
from src.services.search_service import HierarchicalSearchService

router = APIRouter()

@router.get("/search")
async def search_content(
    q: str = Query(..., description="搜索关键词"),
    type: str = Query("all", description="搜索类型: all/articles/comments"),
    sort: str = Query("relevance", description="排序方式: relevance/date/popularity"),
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(10, ge=1, le=100, description="每页结果数量"),
    session: AsyncSession = Depends(get_async_session),
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user)
):
    """
    智能搜索API端点
    
    支持基于BERT向量的语义搜索，包括：
    - 文章搜索
    - 评论搜索
    - 混合搜索
    - 多种排序方式
    """
    try:
        # 使用预加载的模型缓存，如果失败则使用降级方案
        try:
            vectorization_service = get_cached_model()
            search_service = HierarchicalSearchService(vectorization_service, session)
        except RuntimeError:
            # 模型缓存未初始化，使用降级方案
            from src.services.vectorization_service import BERTVectorizationService
            vectorization_service = BERTVectorizationService()
            search_service = HierarchicalSearchService(vectorization_service, session)
        
        # 参数验证
        if not q or not q.strip():
            raise HTTPException(status_code=400, detail="搜索关键词不能为空")
        
        if type not in ['all', 'articles', 'comments']:
            raise HTTPException(status_code=400, detail="搜索类型必须是 all, articles 或 comments")
        
        if sort not in ['relevance', 'date', 'popularity']:
            raise HTTPException(status_code=400, detail="排序方式必须是 relevance, date 或 popularity")
        
        # 执行搜索
        results = await search_service.search(
            query=q.strip(),
            search_type=type,
            sort_by=sort,
            page=page,
            limit=limit
        )
        
        return {
            "query": q,
            "type": type,
            "sort": sort,
            "page": page,
            "limit": limit,
            "total": results.get("total", 0),
            "results": results.get("items", []),
            "has_more": results.get("has_more", False),
            "search_time": results.get("search_time", 0)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"搜索错误: {e}")
        raise HTTPException(status_code=500, detail="搜索服务暂时不可用，请稍后重试")

@router.get("/api/search/suggestions")
async def get_search_suggestions(
    q: str = Query(..., description="搜索关键词"),
    limit: int = Query(5, ge=1, le=20, description="建议数量"),
    session: AsyncSession = Depends(get_async_session)
):
    """
    获取搜索建议
    
    基于用户输入提供搜索建议
    """
    try:
        if not q or len(q.strip()) < 2:
            return {"suggestions": []}
        
        # 这里可以实现基于历史搜索、热门搜索等的建议逻辑
        # 暂时返回简单的建议
        suggestions = await get_search_suggestions_from_db(session, q.strip(), limit)
        
        return {
            "query": q,
            "suggestions": suggestions
        }
        
    except Exception as e:
        print(f"搜索建议错误: {e}")
        return {"suggestions": []}

@router.get("/api/search/trending")
async def get_trending_searches(
    limit: int = Query(10, ge=1, le=50, description="热门搜索数量"),
    session: AsyncSession = Depends(get_async_session)
):
    """
    获取热门搜索关键词
    """
    try:
        # 这里可以实现基于搜索统计的热门关键词逻辑
        # 暂时返回模拟数据
        trending = [
            {"keyword": "Python", "count": 156},
            {"keyword": "机器学习", "count": 89},
            {"keyword": "Web开发", "count": 67},
            {"keyword": "数据库", "count": 45},
            {"keyword": "算法", "count": 34}
        ]
        
        return {
            "trending": trending[:limit]
        }
        
    except Exception as e:
        print(f"热门搜索错误: {e}")
        return {"trending": []}

async def get_search_suggestions_from_db(session: AsyncSession, query: str, limit: int) -> List[str]:
    """
    从数据库获取搜索建议
    """
    try:
        # 这里可以实现基于文章标题、标签等的搜索建议
        # 暂时返回简单的建议
        suggestions = []
        
        # 可以基于文章标题进行模糊匹配
        # 这里简化实现，实际应该使用更复杂的算法
        
        return suggestions[:limit]
        
    except Exception as e:
        print(f"获取搜索建议错误: {e}")
        return []
