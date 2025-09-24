"""
搜索服务
实现基于BERT向量的智能搜索功能
"""

import time
import json
import numpy as np
from typing import Dict, Any
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import text
from src.services.vectorization_service import BERTVectorizationService

class HierarchicalSearchService:
    """分层搜索服务"""
    
    def __init__(self, vectorization_service: BERTVectorizationService, session: AsyncSession):
        self.vectorization_service = vectorization_service
        self.session = session
    
    async def search(self, query: str, search_type: str = "all", 
                    sort_by: str = "relevance", page: int = 1, limit: int = 10) -> Dict[str, Any]:
        """
        执行智能搜索
        
        Args:
            query: 搜索关键词
            search_type: 搜索类型 (all/articles/comments)
            sort_by: 排序方式 (relevance/date/popularity)
            page: 页码
            limit: 每页结果数量
            
        Returns:
            搜索结果字典
        """
        start_time = time.time()
        
        try:
            # 1. 将查询文本向量化
            query_vector = await self.vectorization_service.vectorize_text(query)
            query_vector_json = self._vector_to_json(query_vector)
            
            # 2. 根据搜索类型执行不同的搜索策略
            if search_type == "articles":
                results = await self._search_articles(query_vector_json, sort_by, page, limit, query)
            elif search_type == "comments":
                results = await self._search_comments(query_vector_json, sort_by, page, limit, query)
            else:  # all
                results = await self._search_all(query_vector_json, sort_by, page, limit, query)
            
            # 3. 计算搜索时间
            search_time = round(time.time() - start_time, 3)
            
            return {
                "items": results.get("items", []),
                "total": results.get("total", 0),
                "has_more": results.get("has_more", False),
                "search_time": search_time
            }
            
        except Exception as e:
            print(f"搜索服务错误: {e}")
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
        
        try:
            # 检查向量表是否存在
            check_sql = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'article_vectors'
            );
            """
            result = await self.session.exec(text(check_sql))
            table_exists = result.fetchone()[0]
            
            if not table_exists:
                # 如果向量表不存在，使用传统文本搜索
                return await self._search_articles_fallback(query, sort_by, page, limit)
            
            # 使用向量搜索，结合关键词匹配加分
            sql = f"""
            SELECT 
                pi.id,
                pi.name as title,
                pi.comment as content,
                u.name as author,
                pi.createtime,
                (
                    (1 - (av.content_vector <=> '{query_vector_json}'::vector)) +
                    CASE 
                        WHEN LOWER(pi.name) LIKE LOWER('%{query}%') THEN 0.1
                        WHEN LOWER(pi.comment) LIKE LOWER('%{query}%') THEN 0.05
                        ELSE 0
                    END
                ) as relevance_score
            FROM article_vectors av
            LEFT JOIN projectitem pi ON av.projectitem_id = pi.id
            LEFT JOIN users u ON pi.userid = u.id
            WHERE pi.status = 1
            ORDER BY relevance_score DESC
            LIMIT {limit} OFFSET {offset}
            """
            
            result = await self.session.exec(text(sql))
            items = result.fetchall()
            
            # 获取总数
            count_sql = """
            SELECT COUNT(*)
            FROM article_vectors av
            LEFT JOIN projectitem pi ON av.projectitem_id = pi.id
            WHERE pi.status = 1
            """
            count_result = await self.session.exec(text(count_sql))
            total = count_result.fetchone()[0]
            
            return {
                "items": [self._format_article_result(item) for item in items],
                "total": total,
                "has_more": (offset + len(items)) < total
            }
            
        except Exception as e:
            print(f"文章搜索错误: {e}")
            # 降级到传统搜索
            return await self._search_articles_fallback(query, sort_by, page, limit)
    
    async def _search_articles_fallback(self, query: str, sort_by: str, page: int, limit: int) -> Dict[str, Any]:
        """文章搜索降级方案（传统文本搜索）"""
        offset = (page - 1) * limit
        
        # 构建搜索条件
        search_condition = f"pi.name ILIKE '%{query}%' OR pi.comment ILIKE '%{query}%'"
        
        # 构建排序条件
        if sort_by == "date":
            order_clause = "pi.createtime DESC"
        elif sort_by == "popularity":
            order_clause = "pi.accesscount DESC"
        else:  # relevance
            order_clause = f"""
                CASE 
                    WHEN pi.name ILIKE '%{query}%' THEN 3
                    WHEN pi.comment ILIKE '%{query}%' THEN 2
                    ELSE 1
                END DESC
            """
        
        sql = f"""
        SELECT 
            pi.id,
            pi.name as title,
            pi.comment as content,
            u.name as author,
            pi.createtime,
            1.0 as relevance_score
        FROM projectitem pi
        LEFT JOIN users u ON pi.userid = u.id
        WHERE pi.status = 1 AND ({search_condition})
        ORDER BY {order_clause}
        LIMIT {limit} OFFSET {offset}
        """
        
        result = await self.session.exec(text(sql))
        items = result.fetchall()
        
        # 获取总数
        count_sql = f"""
        SELECT COUNT(*)
        FROM projectitem pi
        WHERE pi.status = 1 AND ({search_condition})
        """
        count_result = await self.session.exec(text(count_sql))
        total = count_result.fetchone()[0]
        
        return {
            "items": [self._format_article_result(item) for item in items],
            "total": total,
            "has_more": (offset + len(items)) < total
        }
    
    async def _search_comments(self, query_vector_json: str, sort_by: str, page: int, limit: int, query: str = "") -> Dict[str, Any]:
        """搜索评论"""
        offset = (page - 1) * limit
        
        try:
            # 检查评论向量表是否存在
            check_sql = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'comment_vectors'
            );
            """
            result = await self.session.exec(text(check_sql))
            table_exists = result.fetchone()[0]
            
            if not table_exists:
                # 如果向量表不存在，使用传统文本搜索
                return await self._search_comments_fallback(query, sort_by, page, limit)
            
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
            
        except Exception as e:
            print(f"评论搜索错误: {e}")
            # 降级到传统搜索
            return await self._search_comments_fallback(query, sort_by, page, limit)
    
    async def _search_comments_fallback(self, query: str, sort_by: str, page: int, limit: int) -> Dict[str, Any]:
        """评论搜索降级方案（传统文本搜索）"""
        offset = (page - 1) * limit
        
        # 构建搜索条件
        search_condition = f"p.subject ILIKE '%{query}%' OR p.content ILIKE '%{query}%'"
        
        # 构建排序条件
        if sort_by == "date":
            order_clause = "p.createtime DESC"
        else:  # relevance
            order_clause = f"""
                CASE 
                    WHEN p.subject ILIKE '%{query}%' THEN 3
                    WHEN p.content ILIKE '%{query}%' THEN 2
                    ELSE 1
                END DESC
            """
        
        sql = f"""
        SELECT 
            p.id,
            p.subject as title,
            p.content,
            u.name as author,
            p.posttime,
            1.0 as relevance_score
        FROM post p
        LEFT JOIN users u ON p.userid = u.id
        WHERE p.status = 1 AND ({search_condition})
        ORDER BY {order_clause}
        LIMIT {limit} OFFSET {offset}
        """
        
        result = await self.session.exec(text(sql))
        items = result.fetchall()
        
        # 获取总数
        count_sql = f"""
        SELECT COUNT(*)
        FROM post p
        WHERE p.status = 1 AND ({search_condition})
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
            "has_more": len(all_items) == limit
        }
    
    def _vector_to_json(self, vector: np.ndarray) -> str:
        """将向量转换为JSON字符串"""
        return json.dumps(vector.tolist())
    
    def _json_to_vector(self, json_str: str) -> np.ndarray:
        """将JSON字符串转换为向量"""
        try:
            return np.array(json.loads(json_str))
        except:
            return np.zeros(768)
    
    def _format_article_result(self, item: tuple) -> Dict[str, Any]:
        """格式化文章搜索结果"""
        return {
            "id": item[0],
            "title": item[1],
            "content": item[2],
            "author": item[3],
            "created_at": item[4].isoformat() if item[4] else None,
            "relevance_score": float(item[5]) if item[5] else 0.0,
            "type": "article"
        }
    
    def _format_comment_result(self, item: tuple) -> Dict[str, Any]:
        """格式化评论搜索结果"""
        return {
            "id": item[0],
            "title": item[1],
            "content": item[2],
            "author": item[3],
            "created_at": item[4].isoformat() if item[4] else None,
            "relevance_score": float(item[5]) if item[5] else 0.0,
            "type": "comment"
        }