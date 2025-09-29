"""
搜索服务

实现基于BERT向量的智能搜索功能，支持文章和评论的语义搜索。
使用分层搜索策略，结合向量相似度计算和动态阈值调整。

主要功能：
- 语义搜索（基于BERT向量相似度）
- 动态阈值调整（根据查询特征）
- 多类型内容搜索（文章+评论）
- 结果排序和分页

技术特性：
- 使用pgvector进行高效向量检索
- 智能阈值计算提高搜索精度
- 支持多种排序方式
- 错误降级处理
"""

import json
import time
from typing import Dict, Any, List

import numpy as np
from sqlalchemy import text
from sqlmodel.ext.asyncio.session import AsyncSession

class HierarchicalSearchService:
    """
    分层搜索服务
    
    基于BERT向量实现智能语义搜索，支持文章和评论的混合搜索。
    使用优化的混合搜索策略：10%文章级 + 90%片段级相似度。
    使用动态阈值调整和智能排序提高搜索质量。
    """
    
    def __init__(self, vectorization_service, session: AsyncSession):
        """
        初始化搜索服务
        
        Args:
            vectorization_service: 向量化服务实例
            session: 数据库会话
        """
        self.vectorization_service = vectorization_service
        self.session = session
        
        # 混合搜索权重配置（优化后：10%文章级 + 90%片段级）
        self.article_weight = 0.1  # 文章级权重
        self.segment_weight = 0.9  # 片段级权重
        
        # 文章级内部权重（标题 vs 内容）
        self.title_weight = 0.3    # 标题权重
        self.content_weight = 0.7  # 内容权重
    
    def calculate_dynamic_threshold(self, query: str, query_vector_json: str) -> float:
        """
        计算动态阈值
        
        根据查询特征动态调整相似度阈值，提高搜索精度。
        短查询使用更高阈值，复杂查询使用较低阈值。
        
        Args:
            query: 搜索查询
            query_vector_json: 查询向量JSON字符串（未使用，保留接口兼容性）
            
        Returns:
            float: 动态阈值 (0.1-0.9)
        """
        # 基础阈值，针对中文查询优化
        base_threshold = 0.45
        
        # 根据查询长度调整阈值
        query_length = len(query.strip())
        if query_length <= 2:  # 短查询，提高阈值
            length_factor = 0.1
        elif query_length <= 5:  # 中等查询
            length_factor = 0.05
        else:  # 长查询，降低阈值
            length_factor = 0.0
        
        # 根据查询复杂度调整阈值
        word_count = len(query.split())
        if word_count >= 3:  # 复杂查询
            complexity_factor = -0.05
        else:
            complexity_factor = 0.0
        
        # 根据查询类型调整阈值
        has_numbers = any(char.isdigit() for char in query)
        has_special = any(char in '!@#$%^&*()' for char in query)
        
        if has_numbers or has_special:  # 精确查询，提高阈值
            precision_factor = 0.05
        else:
            precision_factor = 0.0
        
        # 计算最终阈值
        dynamic_threshold = base_threshold + length_factor + complexity_factor + precision_factor
        
        # 确保阈值在合理范围内
        return max(0.1, min(0.9, dynamic_threshold))
    
    async def hybrid_search_articles(self, query_vector_json: str, sort_by: str, page: int, limit: int, query: str = "") -> Dict[str, Any]:
        """
        混合搜索文章（优化版：10%文章级 + 90%片段级）
        
        结合标题、内容和最佳片段的相似度，使用优化的权重分配。
        
        Args:
            query_vector_json: 查询向量JSON字符串
            sort_by: 排序方式
            page: 页码
            limit: 每页数量
            query: 原始查询字符串
            
        Returns:
            Dict[str, Any]: 搜索结果
        """
        offset = (page - 1) * limit
        
        # 计算动态阈值
        dynamic_threshold = self.calculate_dynamic_threshold(query, query_vector_json)
        adjusted_threshold = dynamic_threshold
        
        # 过滤掉过短的段落
        keyword_length = len(query.strip()) if query else 0
        min_segment_length = max(3, keyword_length)
        
        # 优化的混合搜索SQL：包含标题片段的片段级搜索
        sql = f"""
            WITH all_segments AS (
                -- 标题作为特殊片段（权重更高）
                SELECT 
                    av.projectitem_id,
                    0 as segment_index,
                    av.title_text as segment_text,
                    av.title_vector as segment_vector,
                    1.0 as confidence_score,
                    'title' as segment_type,
                    1.2 as segment_weight  -- 标题片段权重更高
                FROM article_vectors av
                WHERE av.title_vector IS NOT NULL
                AND av.projectitem_id IN (
                    SELECT DISTINCT av2.projectitem_id 
                    FROM article_vectors av2
                    LEFT JOIN projectitem pi2 ON av2.projectitem_id = pi2.id
                    WHERE pi2.status = 1
                )
                
                UNION ALL
                
                -- 内容片段
                SELECT 
                    av.projectitem_id,
                    csv.segment_index,
                    csv.segment_text,
                    csv.segment_vector,
                    csv.confidence_score,
                    'content' as segment_type,
                    1.0 as segment_weight  -- 内容片段标准权重
                FROM article_vectors av
                JOIN content_segment_vectors csv ON av.id = csv.article_vector_id
                LEFT JOIN projectitem pi ON av.projectitem_id = pi.id
                WHERE pi.status = 1
                AND csv.confidence_score >= 0.8
                AND LENGTH(TRIM(csv.segment_text)) >= {min_segment_length}
            ),
            best_segments AS (
                SELECT DISTINCT ON (projectitem_id)
                    projectitem_id,
                    segment_text,
                    segment_type,
                    (1 - (segment_vector <=> '{query_vector_json}'::vector)) as segment_similarity,
                    segment_weight
                FROM all_segments
                WHERE (1 - (segment_vector <=> '{query_vector_json}'::vector)) >= {adjusted_threshold}
                ORDER BY projectitem_id, (1 - (segment_vector <=> '{query_vector_json}'::vector)) DESC
            ),
            article_scores AS (
                -- 文章级相似度（仅作为参考，权重很低）
                SELECT 
                    av.projectitem_id,
                    (1 - (av.title_vector <=> '{query_vector_json}'::vector)) * 0.3 + 
                    (1 - (av.content_vector <=> '{query_vector_json}'::vector)) * 0.7 as article_similarity
                FROM article_vectors av
                LEFT JOIN projectitem pi ON av.projectitem_id = pi.id
                WHERE pi.status = 1
                AND av.title_vector IS NOT NULL
                AND av.content_vector IS NOT NULL
            )
            SELECT 
                bs.projectitem_id as id,
                pi.name as title,
                pi.comment as content,
                u.name as author,
                pi.createtime,
                -- 混合相似度：10%文章级 + 90%片段级
                (COALESCE(art.article_similarity, 0) * 0.1 + 
                 bs.segment_similarity * 0.9) as relevance_score,
                bs.segment_text as best_match_text,
                bs.segment_type as match_type
            FROM best_segments bs
            LEFT JOIN projectitem pi ON bs.projectitem_id = pi.id
            LEFT JOIN users u ON pi.userid = u.id
            LEFT JOIN article_scores art ON bs.projectitem_id = art.projectitem_id
            ORDER BY relevance_score DESC
            LIMIT {limit} OFFSET {offset}
        """
        
        result = await self.session.exec(text(sql))
        items = result.fetchall()
        
        # 获取总数
        count_sql = f"""
            WITH all_segments AS (
                SELECT 
                    av.projectitem_id,
                    av.title_vector as segment_vector
                FROM article_vectors av
                WHERE av.title_vector IS NOT NULL
                AND av.projectitem_id IN (
                    SELECT DISTINCT av2.projectitem_id 
                    FROM article_vectors av2
                    LEFT JOIN projectitem pi2 ON av2.projectitem_id = pi2.id
                    WHERE pi2.status = 1
                )
                
                UNION ALL
                
                SELECT 
                    av.projectitem_id,
                    csv.segment_vector
                FROM article_vectors av
                JOIN content_segment_vectors csv ON av.id = csv.article_vector_id
                LEFT JOIN projectitem pi ON av.projectitem_id = pi.id
                WHERE pi.status = 1
                AND csv.confidence_score >= 0.8
                AND LENGTH(TRIM(csv.segment_text)) >= {min_segment_length}
            ),
            best_segments AS (
                SELECT DISTINCT ON (projectitem_id)
                    projectitem_id,
                    (1 - (segment_vector <=> '{query_vector_json}'::vector)) as segment_similarity
                FROM all_segments
                WHERE (1 - (segment_vector <=> '{query_vector_json}'::vector)) >= {adjusted_threshold}
                ORDER BY projectitem_id, (1 - (segment_vector <=> '{query_vector_json}'::vector)) DESC
            )
            SELECT COUNT(DISTINCT projectitem_id)
            FROM best_segments
        """
        count_result = await self.session.exec(text(count_sql))
        total = count_result.fetchone()[0]
        
        return {
            "items": [self._format_hybrid_article_result(item) for item in items],
            "total": total,
            "has_more": (offset + len(items)) < total,
            "dynamic_threshold": dynamic_threshold,
            "search_strategy": "hybrid_optimized"
        }
    
    async def search(self, query: str, search_type: str = "all", 
                    sort_by: str = "relevance", page: int = 1, limit: int = 10) -> Dict[str, Any]:
        """
        执行搜索
        
        根据搜索类型执行相应的搜索策略，返回格式化的搜索结果。
        
        Args:
            query: 搜索查询
            search_type: 搜索类型 (all/articles/comments)
            sort_by: 排序方式 (relevance/date/popularity)
            page: 页码
            limit: 每页结果数
            
        Returns:
            Dict[str, Any]: 搜索结果，包含items、total、has_more等信息
        """
        start_time = time.time()
        
        try:
            # 1. 将查询文本向量化
            query_vector = await self.vectorization_service.vectorize_text(query)
            query_vector_json = self._vector_to_json(query_vector)
            
            # 2. 根据搜索类型执行不同的搜索策略
            if search_type == "articles":
                # 使用优化的混合搜索策略（10%文章级 + 90%片段级）
                results = await self.hybrid_search_articles(query_vector_json, sort_by, page, limit, query)
            elif search_type == "comments":
                results = await self._search_comments(query_vector_json, sort_by, page, limit, query)
            else:  # all - 使用混合搜索策略
                # 对于混合搜索，先搜索文章，再搜索评论
                article_results = await self.hybrid_search_articles(query_vector_json, sort_by, page, limit, query)
                comment_results = await self._search_comments(query_vector_json, sort_by, page, limit, query)
                
                # 合并结果
                all_items = article_results.get("items", []) + comment_results.get("items", [])
                total_count = article_results.get("total", 0) + comment_results.get("total", 0)
                
                results = {
                    "items": all_items,
                    "total": total_count,
                    "has_more": article_results.get("has_more", False) or comment_results.get("has_more", False),
                    "dynamic_threshold": article_results.get("dynamic_threshold", 0.45),
                    "search_strategy": "hybrid_optimized"
                }
            
            # 3. 计算搜索时间
            search_time = round(time.time() - start_time, 3)
            
            return {
                "items": results.get("items", []),
                "total": results.get("total", 0),
                "has_more": results.get("has_more", False),
                "search_time": search_time,
                "dynamic_threshold": results.get("dynamic_threshold", 0.45)
            }
            
        except Exception as e:
            # 使用logger而不是print
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"搜索服务错误: {e}")
            
            # 返回空结果而不是抛出异常
            return {
                "items": [],
                "total": 0,
                "has_more": False,
                "search_time": round(time.time() - start_time, 3),
                "error": str(e)
            }
    
    async def _search_articles(self, query_vector_json: str, sort_by: str, page: int, limit: int, query: str = "") -> Dict[str, Any]:
        """搜索文章"""
        offset = (page - 1) * limit
        
        # 计算动态阈值
        dynamic_threshold = self.calculate_dynamic_threshold(query, query_vector_json)
        
        # 使用纯语义搜索，动态阈值范围为10%-90%
        # 直接使用动态阈值，不再进一步调整
        adjusted_threshold = dynamic_threshold
        
        # 优化后的SQL：直接使用内容段相似度，避免UNION ALL和复杂GROUP BY
        # 使用DISTINCT ON去重，确保每篇文章只返回最高相似度的记录
        # 过滤掉过短的段落：长度小于3个字符或小于关键词长度的段落
        keyword_length = len(query.strip()) if query else 0
        min_segment_length = max(3, keyword_length)
        
        sql = f"""
            SELECT DISTINCT ON (av.projectitem_id)
                av.projectitem_id as id,
                pi.name as title,
                pi.comment as content,
                u.name as author,
                pi.createtime,
                (1 - (csv.segment_vector <=> '{query_vector_json}'::vector)) as relevance_score
            FROM article_vectors av
            LEFT JOIN projectitem pi ON av.projectitem_id = pi.id
            LEFT JOIN users u ON pi.userid = u.id
            LEFT JOIN content_segment_vectors csv ON av.id = csv.article_vector_id
            WHERE pi.status = 1
            AND (1 - (csv.segment_vector <=> '{query_vector_json}'::vector)) >= {adjusted_threshold}
            AND LENGTH(TRIM(csv.segment_text)) >= {min_segment_length}
            ORDER BY av.projectitem_id, (1 - (csv.segment_vector <=> '{query_vector_json}'::vector)) DESC
            LIMIT {limit} OFFSET {offset}
            """
        
        result = await self.session.exec(text(sql))
        items = result.fetchall()
        
        # 获取总数 - 简化查询，使用相同的过滤条件
        count_sql = f"""
        SELECT COUNT(DISTINCT av.projectitem_id)
        FROM article_vectors av
        LEFT JOIN projectitem pi ON av.projectitem_id = pi.id
        LEFT JOIN content_segment_vectors csv ON av.id = csv.article_vector_id
        WHERE pi.status = 1
        AND (1 - (csv.segment_vector <=> '{query_vector_json}'::vector)) >= {adjusted_threshold}
        AND LENGTH(TRIM(csv.segment_text)) >= {min_segment_length}
        """
        count_result = await self.session.exec(text(count_sql))
        total = count_result.fetchone()[0]
            
        return {
            "items": [self._format_article_result(item) for item in items],
            "total": total,
            "has_more": (offset + len(items)) < total,
            "dynamic_threshold": dynamic_threshold
        }
    
    
    async def _search_comments(self, query_vector_json: str, sort_by: str, page: int, limit: int, query: str = "") -> Dict[str, Any]:
        """搜索评论"""
        offset = (page - 1) * limit
        
        # 使用向量搜索
        sql = f"""
            SELECT 
                p.id,
                p.subject as title,
                p.content,
                u.name as author,
                p.posttime,
                (1 - (cv.content_vector <=> '{query_vector_json}'::vector)) as relevance_score
            FROM comment_vectors cv
            LEFT JOIN post p ON cv.post_id = p.id
            LEFT JOIN users u ON p.userid = u.id
            WHERE p.status = 1
            ORDER BY relevance_score DESC
            LIMIT {limit} OFFSET {offset}
            """
        
        result = await self.session.exec(text(sql))
        items = result.fetchall()
        
        # 获取总数
        count_sql = """
        SELECT COUNT(*)
        FROM comment_vectors cv
        LEFT JOIN post p ON cv.post_id = p.id
        WHERE p.status = 1
        """
        count_result = await self.session.exec(text(count_sql))
        total = count_result.fetchone()[0]
        
        return {
            "items": [self._format_comment_result(item) for item in items],
            "total": total,
            "has_more": (offset + len(items)) < total
        }
    
    
    async def _search_all(self, query_vector_json: str, sort_by: str, page: int, limit: int, query: str = "") -> Dict[str, Any]:
        """搜索所有内容"""
        # 分别搜索文章和评论，使用更大的limit确保有足够的结果
        articles_result = await self._search_articles(query_vector_json, sort_by, page, limit, query)
        comments_result = await self._search_comments(query_vector_json, sort_by, page, limit, query)
        
        # 合并结果
        all_items = articles_result.get("items", []) + comments_result.get("items", [])
        
        # 按相关性排序
        all_items.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        
        # 限制结果数量
        all_items = all_items[:limit]
        
        return {
            "items": all_items,
            "total": articles_result.get("total", 0) + comments_result.get("total", 0),
            "has_more": len(all_items) == limit,
            "dynamic_threshold": articles_result.get("dynamic_threshold", 0.45)
        }
    
    def _vector_to_json(self, vector: np.ndarray) -> str:
        """
        将向量转换为JSON字符串
        
        Args:
            vector: numpy向量数组
            
        Returns:
            str: JSON格式的向量字符串
        """
        return json.dumps(vector.tolist())
    
    def _json_to_vector(self, json_str: str) -> np.ndarray:
        """
        将JSON字符串转换为向量
        
        Args:
            json_str: JSON格式的向量字符串
            
        Returns:
            np.ndarray: 向量数组，失败时返回零向量
        """
        try:
            return np.array(json.loads(json_str))
        except Exception:
            return np.zeros(384)
    
    def _format_article_result(self, item: tuple) -> Dict[str, Any]:
        """
        格式化文章搜索结果
        
        Args:
            item: 数据库查询结果元组
            
        Returns:
            Dict[str, Any]: 格式化的文章搜索结果
        """
        return {
            "id": item[0],
            "title": item[1],
            "content": item[2],
            "author": item[3],
            "created_at": item[4].isoformat() if item[4] else None,
            "relevance_score": float(item[5]) if item[5] else 0.0,
            "type": "article"
        }
    
    def _format_hybrid_article_result(self, item: tuple) -> Dict[str, Any]:
        """
        格式化混合搜索文章结果
        
        Args:
            item: 数据库查询结果元组 (id, title, content, author, createtime, relevance_score, best_match_text, match_type)
            
        Returns:
            Dict[str, Any]: 格式化的混合搜索文章结果
        """
        return {
            "id": item[0],
            "title": item[1],
            "content": item[2],
            "author": item[3],
            "created_at": item[4].isoformat() if item[4] else None,
            "relevance_score": float(item[5]) if item[5] else 0.0,
            "best_match_text": item[6] if len(item) > 6 else None,
            "match_type": item[7] if len(item) > 7 else "content",
            "type": "article",
            "search_strategy": "hybrid_optimized"
        }
    
    def _format_comment_result(self, item: tuple) -> Dict[str, Any]:
        """
        格式化评论搜索结果
        
        Args:
            item: 数据库查询结果元组
            
        Returns:
            Dict[str, Any]: 格式化的评论搜索结果
        """
        return {
            "id": item[0],
            "title": item[1],
            "content": item[2],
            "author": item[3],
            "created_at": item[4].isoformat() if item[4] else None,
            "relevance_score": float(item[5]) if item[5] else 0.0,
            "type": "comment"
        }