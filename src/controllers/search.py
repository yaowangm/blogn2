"""
搜索控制器
实现基于BERT向量的智能搜索功能
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import Optional, Dict, Any, List

from src.database import get_async_session
from src.utils.auth_dependencies import get_optional_current_user
from src.services.model_cache import get_cached_model
from src.services.search_service import HierarchicalSearchService, DEFAULT_THRESHOLD
from src.config.model import get_model_path

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/search")
async def search_content(
    request: Request,
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
        # 优先使用 lifespan 中初始化的同一模型实例（Docker 下避免与请求时 get_cached_model 不一致）
        search_method = "bert"  # 默认使用BERT搜索
        model_error = False  # 标记模型是否出错
        vectorization_service = getattr(request.app.state, "model_cache", None)
        if vectorization_service is None:
            try:
                vectorization_service = get_cached_model()
            except RuntimeError:
                vectorization_service = None
        if vectorization_service is None:
            # 模型缓存未初始化，返回错误而不是创建新实例
            search_method = "bert_model_error"  # 模型加载失败
            model_error = True
            # 不创建新的BERTVectorizationService实例，直接返回错误
            return {
                "query": q,
                "type": type,
                "sort": sort,
                "page": page,
                "limit": limit,
                "total": 0,
                "results": [],
                "has_more": False,
                "search_time": 0.0,
                "search_method": "bert_model_error",
                "error": "BERT模型未初始化，请稍后重试"
            }

        search_service = HierarchicalSearchService(vectorization_service, session)

        # 参数验证
        if not q or not q.strip():
            raise HTTPException(status_code=400, detail="搜索关键词不能为空")
        
        if type not in ['all', 'articles', 'comments']:
            raise HTTPException(status_code=400, detail="搜索类型必须是 all, articles 或 comments")
        
        if sort not in ['relevance', 'date', 'popularity']:
            raise HTTPException(status_code=400, detail="排序方式必须是 relevance, date 或 popularity")
        
        # 执行搜索
        try:
            results = await search_service.search(
                query=q.strip(),
                search_type=type,
                sort_by=sort,
                page=page,
                limit=limit
            )
            
            # 检查搜索结果，判断是否因为模型错误导致返回零向量
            if results.get("total", 0) == 0 and results.get("items", []) == []:
                if model_error:
                    search_method = "bert_model_error"  # 模型出错导致零向量
                else:
                    search_method = "bert_no_results"  # 模型正常但没有匹配结果
                    
        except Exception as e:
            # 搜索过程中出现异常，说明模型有问题
            search_method = "bert_search_error"
            results = {
                "items": [],
                "total": 0,
                "has_more": False,
                "search_time": 0.0,
                "error": str(e)
            }
        
        th = results.get("dynamic_threshold", DEFAULT_THRESHOLD)
        for it in results.get("items", []):
            try:
                cur = float(it.get("relevance_score") or 0)
            except (TypeError, ValueError):
                cur = 0
            # 仅当分数缺失或≤0 时用阈值兜底，避免前端显示 0%
            it["relevance_score"] = th if cur <= 0 else cur
        resp = {
            "query": q,
            "type": type,
            "sort": sort,
            "page": page,
            "limit": limit,
            "total": results.get("total", 0),
            "results": results.get("items", []),
            "has_more": results.get("has_more", False),
            "search_time": results.get("search_time", 0),
            "search_method": search_method,
            "dynamic_threshold": th
        }
        # 诊断：当前使用的模型路径。与“当初写入 article_vectors 时用的路径”须一致（同一 snapshot），否则向量空间不一致会搜出大量无关结果
        try:
            resp["model_path"] = get_model_path() or ""
        except Exception:
            resp["model_path"] = ""
        # 若结果数异常多：可能是当前进程解析到的模型路径与写库时不同（例如本地用 ~/.cache/.../snapshots/A，Docker 用挂载的 .../snapshots/B）
        if resp.get("total", 0) > 200 and resp.get("search_method") == "bert":
            resp["_hint"] = "结果过多可能因当前模型路径与写库时不一致（对比本地与 Docker 的 model_path 及 snapshot 是否相同）。可在本环境调用 POST /api/admin/vectorization/reindex-all 全量重算向量后再试"
        return resp
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"搜索错误: {e}")
        raise HTTPException(status_code=500, detail="搜索服务暂时不可用，请稍后重试")

@router.get("/search/debug-vector")
async def debug_search_vector(
    request: Request,
    q: str = Query("左轻侯", description="用于向量化的文本"),
    session: AsyncSession = Depends(get_async_session)
):
    """
    诊断接口：返回当前模型路径及查询文本的向量（前5维、范数），用于对比本地与 Docker 是否使用同一模型。
    """
    try:
        vec_service = getattr(request.app.state, "model_cache", None) or get_cached_model()
        import numpy as np
        v = await vec_service.vectorize_text(q.strip() or "左轻侯")
        norm = float(np.linalg.norm(v)) if v is not None and len(v) else 0
        first_5 = v[:5].tolist() if v is not None and len(v) >= 5 else (v.tolist() if v is not None else [])
        return {
            "query": q or "左轻侯",
            "model_path": get_model_path() or "",
            "vector_norm": round(norm, 6),
            "vector_first_5": first_5,
            "from_app_state": getattr(request.app.state, "model_cache", None) is not None,
        }
    except Exception as e:
        return {"error": str(e), "model_path": get_model_path() or ""}


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
        logger.error(f"搜索建议错误: {e}")
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
        logger.error(f"热门搜索错误: {e}")
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
        logger.error(f"获取搜索建议错误: {e}")
        return []
