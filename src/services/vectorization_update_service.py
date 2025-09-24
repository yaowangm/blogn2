"""
向量化更新服务

当文章发布或修改时，自动更新相关的向量化存储表。
支持增量更新和批量更新，确保搜索索引与内容保持同步。
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import text

from src.services.vectorization_service import BERTVectorizationService
from src.services.model_cache import get_cached_model
from src.utils.time_utils import TimeUtils

logger = logging.getLogger(__name__)


class VectorizationUpdateService:
    """向量化更新服务"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.vectorization_service = None
    
    async def _get_vectorization_service(self) -> BERTVectorizationService:
        """获取向量化服务实例"""
        if self.vectorization_service is None:
            try:
                # 尝试使用预加载的模型缓存
                self.vectorization_service = get_cached_model()
            except RuntimeError:
                # 如果缓存未初始化，尝试直接创建新的向量化服务
                logger.warning("模型缓存未初始化，尝试直接创建向量化服务")
                try:
                    from src.services.vectorization_service import BERTVectorizationService
                    self.vectorization_service = BERTVectorizationService()
                    # 不在这里加载模型，让向量化时再加载
                except Exception as e:
                    logger.error(f"创建向量化服务失败: {e}")
                    return None
        
        return self.vectorization_service
    
    async def update_article_vectors(self, article_id: int, title: str, content: str) -> bool:
        """
        更新文章向量
        
        Args:
            article_id: 文章ID
            title: 文章标题
            content: 文章内容
            
        Returns:
            bool: 更新是否成功
        """
        try:
            logger.info(f"开始更新文章 {article_id} 的向量...")
            
            # 获取向量化服务
            vectorization_service = await self._get_vectorization_service()
            
            # 如果向量化服务不可用，跳过向量化更新
            if vectorization_service is None:
                logger.warning(f"向量化服务不可用，跳过文章 {article_id} 的向量化更新")
                return False
            
            # 向量化标题和内容
            title_vector = await vectorization_service.vectorize_text(title or "")
            content_vector = await vectorization_service.vectorize_text(content or "")
            
            # 计算文本统计信息
            total_text_length = len(content or "")
            segment_count = 1
            max_segment_length = len(content or "")
            
            # 检查是否已存在向量记录
            existing_vector = await self._get_existing_article_vector(article_id)
            
            if existing_vector:
                # 更新现有记录
                await self._update_existing_article_vector(
                    article_id, title, content, title_vector, content_vector,
                    total_text_length, segment_count, max_segment_length
                )
                logger.info(f"文章 {article_id} 向量已更新")
            else:
                # 创建新记录
                await self._create_new_article_vector(
                    article_id, title, content, title_vector, content_vector,
                    total_text_length, segment_count, max_segment_length
                )
                logger.info(f"文章 {article_id} 向量已创建")
            
            # 提交事务
            await self.session.commit()
            logger.info(f"文章 {article_id} 向量化事务已提交")
            
            return True
            
        except Exception as e:
            logger.error(f"更新文章 {article_id} 向量失败: {e}")
            return False
    
    async def _get_existing_article_vector(self, article_id: int) -> Optional[Dict]:
        """获取现有的文章向量记录"""
        query = text("""
            SELECT id, title_text, content_text, updated_at
            FROM article_vectors 
            WHERE projectitem_id = :article_id
        """)
        
        result = await self.session.execute(query, {"article_id": article_id})
        row = result.fetchone()
        
        if row:
            return {
                "id": row[0],
                "title_text": row[1],
                "content_text": row[2],
                "updated_at": row[3]
            }
        return None
    
    async def _update_existing_article_vector(
        self, article_id: int, title: str, content: str,
        title_vector: Any, content_vector: Any,
        total_text_length: int, segment_count: int, max_segment_length: int
    ):
        """更新现有的文章向量记录"""
        # 将向量转换为JSON格式
        title_vector_json = self._vector_to_json(title_vector)
        content_vector_json = self._vector_to_json(content_vector)
        
        query = text("""
            UPDATE article_vectors 
            SET 
                title_vector = :title_vector,
                title_text = :title_text,
                content_vector = :content_vector,
                content_text = :content_text,
                total_text_length = :total_text_length,
                max_segment_length = :max_segment_length,
                updated_at = :updated_at
            WHERE projectitem_id = :article_id
        """)
        
        await self.session.execute(query, {
            "article_id": article_id,
            "title_vector": title_vector_json,
            "title_text": title,
            "content_vector": content_vector_json,
            "content_text": content,
            "total_text_length": total_text_length,
            "max_segment_length": max_segment_length,
            "updated_at": TimeUtils.now_utc()
        })
    
    async def _create_new_article_vector(
        self, article_id: int, title: str, content: str,
        title_vector: Any, content_vector: Any,
        total_text_length: int, segment_count: int, max_segment_length: int
    ):
        """创建新的文章向量记录"""
        # 将向量转换为JSON格式
        title_vector_json = self._vector_to_json(title_vector)
        content_vector_json = self._vector_to_json(content_vector)
        
        query = text("""
            INSERT INTO article_vectors (
                projectitem_id, title_vector, title_text, content_vector, content_text,
                segment_count, vectorization_method, total_text_length, max_segment_length,
                avg_confidence, key_segment_ratio, created_at, updated_at
            ) VALUES (
                :article_id, :title_vector, :title_text, :content_vector, :content_text,
                :segment_count, :vectorization_method, :total_text_length, :max_segment_length,
                :avg_confidence, :key_segment_ratio, :created_at, :updated_at
            )
        """)
        
        await self.session.execute(query, {
            "article_id": article_id,
            "title_vector": title_vector_json,
            "title_text": title,
            "content_vector": content_vector_json,
            "content_text": content,
            "segment_count": segment_count,
            "vectorization_method": "direct",
            "total_text_length": total_text_length,
            "max_segment_length": max_segment_length,
            "avg_confidence": 1.0,
            "key_segment_ratio": 0.0,
            "created_at": TimeUtils.now_utc(),
            "updated_at": TimeUtils.now_utc()
        })
    
    async def delete_article_vectors(self, article_id: int) -> bool:
        """
        删除文章向量
        
        Args:
            article_id: 文章ID
            
        Returns:
            bool: 删除是否成功
        """
        try:
            logger.info(f"开始删除文章 {article_id} 的向量...")
            
            # 删除文章向量记录（级联删除片段向量）
            query = text("""
                DELETE FROM article_vectors 
                WHERE projectitem_id = :article_id
            """)
            
            await self.session.execute(query, {"article_id": article_id})
            logger.info(f"文章 {article_id} 向量已删除")
            
            return True
            
        except Exception as e:
            logger.error(f"删除文章 {article_id} 向量失败: {e}")
            return False
    
    async def batch_update_articles(self, article_ids: List[int]) -> Dict[str, Any]:
        """
        批量更新文章向量
        
        Args:
            article_ids: 文章ID列表
            
        Returns:
            Dict[str, Any]: 更新结果统计
        """
        success_count = 0
        failed_count = 0
        failed_articles = []
        
        logger.info(f"开始批量更新 {len(article_ids)} 篇文章的向量...")
        
        for article_id in article_ids:
            try:
                # 获取文章信息
                article_info = await self._get_article_info(article_id)
                if not article_info:
                    failed_count += 1
                    failed_articles.append(article_id)
                    continue
                
                # 更新向量
                success = await self.update_article_vectors(
                    article_id, 
                    article_info["name"], 
                    article_info["comment"]
                )
                
                if success:
                    success_count += 1
                else:
                    failed_count += 1
                    failed_articles.append(article_id)
                    
            except Exception as e:
                logger.error(f"批量更新文章 {article_id} 失败: {e}")
                failed_count += 1
                failed_articles.append(article_id)
        
        result = {
            "total": len(article_ids),
            "success": success_count,
            "failed": failed_count,
            "failed_articles": failed_articles
        }
        
        logger.info(f"批量更新完成: {result}")
        return result
    
    async def _get_article_info(self, article_id: int) -> Optional[Dict]:
        """获取文章信息"""
        query = text("""
            SELECT id, name, comment 
            FROM projectitem 
            WHERE id = :article_id
        """)
        
        result = await self.session.execute(query, {"article_id": article_id})
        row = result.fetchone()
        
        if row:
            return {
                "id": row[0],
                "name": row[1],
                "comment": row[2]
            }
        return None
    
    def _vector_to_json(self, vector: Any) -> str:
        """将向量转换为JSON字符串"""
        import json
        import numpy as np
        
        if hasattr(vector, 'tolist'):
            return json.dumps(vector.tolist())
        elif isinstance(vector, (list, tuple)):
            return json.dumps(list(vector))
        else:
            return json.dumps(vector)
    
    async def get_vectorization_status(self, article_id: int) -> Dict[str, Any]:
        """
        获取文章向量化状态
        
        Args:
            article_id: 文章ID
            
        Returns:
            Dict[str, Any]: 向量化状态信息
        """
        query = text("""
            SELECT 
                av.id,
                av.title_text,
                av.content_text,
                av.segment_count,
                av.vectorization_method,
                av.total_text_length,
                av.avg_confidence,
                av.created_at,
                av.updated_at
            FROM article_vectors av
            WHERE av.projectitem_id = :article_id
        """)
        
        result = await self.session.execute(query, {"article_id": article_id})
        row = result.fetchone()
        
        if row:
            return {
                "vectorized": True,
                "vector_id": row[0],
                "title_text": row[1],
                "content_text": row[2],
                "segment_count": row[3],
                "vectorization_method": row[4],
                "total_text_length": row[5],
                "avg_confidence": row[6],
                "created_at": row[7],
                "updated_at": row[8]
            }
        else:
            return {
                "vectorized": False,
                "message": "文章尚未向量化"
            }


# 全局向量化更新服务实例
_vectorization_update_service = None

def get_vectorization_update_service(session: AsyncSession) -> VectorizationUpdateService:
    """获取向量化更新服务实例"""
    return VectorizationUpdateService(session)
