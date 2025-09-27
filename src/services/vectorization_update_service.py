"""
向量化更新服务

当文章发布或修改时，自动更新相关的向量化存储表。
支持增量更新和批量更新，确保搜索索引与内容保持同步。

主要功能：
- 文章向量化更新（标题+内容+片段）
- 评论向量化更新
- 向量数据删除
- 批量向量化处理
- 文本分段和过滤

技术特性：
- 事务安全（与主业务操作在同一事务中）
- 智能文本分段（滑动窗口）
- 内容过滤（跳过无效段落）
- 错误降级处理
"""

import asyncio
import json
import logging
import re
import string
from typing import List, Dict, Any, Optional

import numpy as np
from sqlalchemy import text
from sqlmodel.ext.asyncio.session import AsyncSession

from src.services.vectorization_service import BERTVectorizationService
from src.services.model_cache import get_cached_model
from src.utils.time_utils import TimeUtils

logger = logging.getLogger(__name__)


class VectorizationUpdateService:
    """
    向量化更新服务
    
    负责管理文章和评论的向量化数据更新，包括创建、更新和删除操作。
    支持智能文本分段和内容过滤，确保向量化质量。
    """
    
    def __init__(self, session: AsyncSession):
        """
        初始化向量化更新服务
        
        Args:
            session: 数据库会话
        """
        self.session = session
        self.vectorization_service = None
    
    async def _get_vectorization_service(self) -> Optional[BERTVectorizationService]:
        """
        获取向量化服务实例
        
        优先使用预加载的模型缓存，失败时创建新实例。
        
        Returns:
            Optional[BERTVectorizationService]: 向量化服务实例，失败时返回None
        """
        if self.vectorization_service is None:
            try:
                # 尝试使用预加载的模型缓存
                self.vectorization_service = get_cached_model()
            except RuntimeError:
                # 如果缓存未初始化，尝试直接创建新的向量化服务
                logger.warning("模型缓存未初始化，尝试直接创建向量化服务")
                try:
                    self.vectorization_service = BERTVectorizationService()
                    # 立即尝试加载模型，避免延迟加载失败
                    await self.vectorization_service.load_model()
                except Exception as e:
                    logger.error(f"创建或加载向量化服务失败: {e}")
                    return None
        
        return self.vectorization_service
    
    async def update_article_vectors(self, article_id: int, title: str, content: str) -> bool:
        """
        更新文章向量
        
        对文章标题、内容和片段进行向量化，并存储到数据库中。
        支持增量更新和智能文本分段。
        
        Args:
            article_id: 文章ID
            title: 文章标题
            content: 文章内容
            
        Returns:
            bool: 更新是否成功
        """
        try:
            # 获取向量化服务
            vectorization_service = await self._get_vectorization_service()
            
            # 如果向量化服务不可用，跳过向量化更新
            if vectorization_service is None:
                logger.warning(f"向量化服务不可用，跳过文章 {article_id} 的向量化更新")
                return False
            
            # 向量化标题和内容
            title_vector = await vectorization_service.vectorize_text(title or "")
            content_vector = await vectorization_service.vectorize_text(content or "")
            
            # 处理长文本分段
            content_segments = await self._process_long_text(content or "", vectorization_service)
            
            # 计算统计信息
            total_text_length = len(content or "")
            segment_count = len(content_segments) if content_segments else 1
            max_segment_length = max(len(seg['text']) for seg in content_segments) if content_segments else total_text_length
            
            # 检查是否已存在向量记录
            existing_vector = await self._get_existing_article_vector(article_id)
            
            if existing_vector:
                # 更新现有记录
                article_vector_id = await self._update_existing_article_vector(
                    article_id, title, content, title_vector, content_vector,
                    total_text_length, segment_count, max_segment_length
                )
            else:
                # 创建新记录
                article_vector_id = await self._create_new_article_vector(
                    article_id, title, content, title_vector, content_vector,
                    total_text_length, segment_count, max_segment_length
                )
            
            # 保存片段向量
            if content_segments and article_vector_id:
                await self._save_content_segments(article_vector_id, content_segments)
            
            # 提交事务
            await self.session.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"更新文章 {article_id} 向量失败: {e}")
            # 回滚事务
            try:
                await self.session.rollback()
            except Exception as rollback_error:
                logger.error(f"回滚事务失败: {rollback_error}")
            return False
    
    async def _get_existing_article_vector(self, article_id: int) -> Optional[Dict]:
        """
        获取现有的文章向量记录
        
        Args:
            article_id: 文章ID
            
        Returns:
            Optional[Dict]: 现有向量记录，不存在时返回None
        """
        try:
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
        except Exception as e:
            logger.error(f"获取文章 {article_id} 现有向量记录失败: {e}")
            return None
    
    async def _update_existing_article_vector(
        self, article_id: int, title: str, content: str,
        title_vector: Any, content_vector: Any,
        total_text_length: int, segment_count: int, max_segment_length: int
    ) -> int:
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
        
        # 获取article_vector_id
        try:
            get_id_query = text("SELECT id FROM article_vectors WHERE projectitem_id = :article_id")
            result = await self.session.execute(get_id_query, {"article_id": article_id})
            row = result.fetchone()
            return row[0] if row else None
        except Exception as e:
            logger.error(f"获取文章 {article_id} 向量ID失败: {e}")
            return None
    
    async def _create_new_article_vector(
        self, article_id: int, title: str, content: str,
        title_vector: Any, content_vector: Any,
        total_text_length: int, segment_count: int, max_segment_length: int
    ) -> int:
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
        
        # 获取新创建的article_vector_id
        try:
            get_id_query = text("SELECT id FROM article_vectors WHERE projectitem_id = :article_id")
            result = await self.session.execute(get_id_query, {"article_id": article_id})
            row = result.fetchone()
            return row[0] if row else None
        except Exception as e:
            logger.error(f"获取新创建的文章 {article_id} 向量ID失败: {e}")
            return None
    
    async def delete_article_vectors(self, article_id: int) -> bool:
        """
        删除文章向量
        
        Args:
            article_id: 文章ID
            
        Returns:
            bool: 删除是否成功
        """
        try:
            # 删除文章向量记录（级联删除片段向量）
            query = text("""
                DELETE FROM article_vectors 
                WHERE projectitem_id = :article_id
            """)
            
            await self.session.execute(query, {"article_id": article_id})
            
            # 注意：不在这里提交事务，由调用方管理事务
            # 这样可以确保向量化删除与文章删除在同一个事务中
            
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
        
        return result
    
    async def _get_article_info(self, article_id: int) -> Optional[Dict]:
        """获取文章信息"""
        try:
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
        except Exception as e:
            logger.error(f"获取文章 {article_id} 信息失败: {e}")
            return None
    
    def _vector_to_json(self, vector: Any) -> str:
        """
        将向量转换为JSON字符串
        
        Args:
            vector: 向量数据（numpy数组、列表或元组）
            
        Returns:
            str: JSON格式的向量字符串
        """
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
        
        try:
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
        except Exception as e:
            logger.error(f"获取文章 {article_id} 向量化状态失败: {e}")
            return {
                "vectorized": False,
                "message": f"获取向量化状态失败: {str(e)}"
            }
    
    async def _process_long_text(self, text: str, vectorization_service) -> List[Dict]:
        """
        处理长文本分段
        
        Args:
            text: 原始文本
            vectorization_service: 向量化服务
            
        Returns:
            List[Dict]: 分段信息列表
        """
        if not text or len(text.strip()) < 50:
            # 短文本不需要分段
            return []
        
        # 使用滑动窗口分割文本
        segments = self._split_text_with_sliding_window(text)
        
        # 向量化每个片段
        segment_results = []
        skipped_count = 0
        
        for i, segment in enumerate(segments):
            # 检查是否应该跳过该段落
            if self._should_skip_segment(segment['text']):
                skipped_count += 1
                logger.debug(f"跳过段落 {i}: '{segment['text'][:50]}...' (长度: {len(segment['text'])})")
                continue
                
            try:
                vector = await vectorization_service.vectorize_text(segment['text'])
                segment_results.append({
                    'index': i,
                    'text': segment['text'],
                    'vector': vector,
                    'length': segment['length'],
                    'start_pos': segment['start_pos'],
                    'end_pos': segment['end_pos'],
                    'confidence_score': 1.0,  # 默认置信度
                    'is_key_segment': self._is_key_segment(segment['text']),
                    'semantic_density': self._calculate_semantic_density(segment['text']),
                    'keyword_density': self._calculate_keyword_density(segment['text'])
                })
            except Exception as e:
                logger.warning(f"片段 {i} 向量化失败: {e}")
                continue
        
        if skipped_count > 0:
            logger.info(f"跳过了 {skipped_count} 个无效段落（长度<3或纯标点符号）")
        
        return segment_results
    
    def _split_text_with_sliding_window(self, text: str, window_size: int = 150, step_size: int = 75) -> List[Dict]:
        """
        使用改进的分段策略分割文本：
        1. 优先按段落划分（双换行符）
        2. 如果段落长度超出窗口大小，尝试在句号、问号、感叹号、换行符处分割
        3. 如果找不到合适的分割点，强制分段
        
        Args:
            text: 原始文本
            window_size: 窗口大小（字符数）
            step_size: 步长（字符数）
            
        Returns:
            List[Dict]: 分段信息
        """
        if len(text) <= window_size:
            return [{
                'text': text,
                'length': len(text),
                'start_pos': 0,
                'end_pos': len(text)
            }]
        
        segments = []
        
        # 第一步：按段落分割（双换行符）
        paragraphs = text.split('\n\n')
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            # 在分割阶段就过滤掉无效段落
            if self._should_skip_segment(paragraph):
                continue
                
            if len(paragraph) <= window_size:
                # 段落长度合适，直接作为一个段
                segments.append({
                    'text': paragraph,
                    'length': len(paragraph),
                    'start_pos': text.find(paragraph),
                    'end_pos': text.find(paragraph) + len(paragraph)
                })
            else:
                # 段落太长，需要进一步分割
                sub_segments = self._split_long_paragraph(paragraph, window_size, step_size)
                segments.extend(sub_segments)
        
        return segments
    
    def _split_long_paragraph(self, paragraph: str, window_size: int, step_size: int) -> List[Dict]:
        """
        分割长段落
        
        Args:
            paragraph: 长段落文本
            window_size: 窗口大小
            step_size: 步长
            
        Returns:
            List[Dict]: 分段信息
        """
        segments = []
        start = 0
        
        while start < len(paragraph):
            end = min(start + window_size, len(paragraph))
            
            # 尝试在句号、问号、感叹号、换行符处分割
            if end < len(paragraph):
                # 从窗口末尾向前搜索合适的分割点
                for i in range(end, start + window_size // 2, -1):
                    if paragraph[i] in '。！？\n':
                        end = i + 1
                        break
            
            segment_text = paragraph[start:end].strip()
            if segment_text and not self._should_skip_segment(segment_text):
                segments.append({
                    'text': segment_text,
                    'length': len(segment_text),
                    'start_pos': start,
                    'end_pos': end
                })
            
            start += step_size
        
        return segments
    
    def _should_skip_segment(self, text: str) -> bool:
        """
        判断是否应该跳过该段落
        
        过滤掉过短或只包含标点符号的段落，提高向量化质量。
        
        Args:
            text: 段落文本
            
        Returns:
            bool: 是否应该跳过
        """
        if not text:
            return True
            
        # 去除首尾空白字符
        text = text.strip()
        
        # 1. 长度小于3的段落
        if len(text) < 3:
            return True
            
        # 2. 完全由标点符号组成的段落
        # 中英文标点符号
        punctuation_chars = string.punctuation + '，。！？；：""''（）【】《》〈〉「」『』〔〕…—·'
        
        # 检查是否只包含标点符号、空白字符和换行符
        text_without_punctuation = re.sub(r'[' + re.escape(punctuation_chars) + r'\s\n\r\t]', '', text)
        
        if len(text_without_punctuation) == 0:
            return True
            
        return False

    def _is_key_segment(self, text: str) -> bool:
        """
        判断是否为关键片段
        
        基于关键词检测判断片段的重要性。
        
        Args:
            text: 片段文本
            
        Returns:
            bool: 是否为关键片段
        """
        key_indicators = ['重要', '关键', '核心', '主要', '总结', '结论', '要点']
        return any(indicator in text for indicator in key_indicators)
    
    def _calculate_semantic_density(self, text: str) -> float:
        """
        计算语义密度
        
        基于词汇多样性计算片段的语义丰富程度。
        
        Args:
            text: 片段文本
            
        Returns:
            float: 语义密度 (0-1)
        """
        words = text.split()
        unique_words = set(words)
        return len(unique_words) / len(words) if words else 0.0
    
    def _calculate_keyword_density(self, text: str) -> float:
        """
        计算关键词密度
        
        基于技术关键词计算片段的技术含量。
        
        Args:
            text: 片段文本
            
        Returns:
            float: 关键词密度 (0-1)
        """
        keywords = ['技术', '方法', '实现', '系统', '算法', '数据', '分析', '研究']
        word_count = len(text.split())
        keyword_count = sum(1 for keyword in keywords if keyword in text)
        return keyword_count / word_count if word_count > 0 else 0.0
    
    async def _aggregate_segment_vectors(self, segments: List[Dict]) -> np.ndarray:
        """
        聚合片段向量
        
        Args:
            segments: 片段列表
            
        Returns:
            np.ndarray: 聚合后的向量
        """
        if not segments:
            return np.zeros(384)
        
        vectors = [seg['vector'] for seg in segments]
        
        # 使用简单的平均聚合，避免复杂的权重计算
        return np.mean(vectors, axis=0)
    
    def _position_weight(self, index: int, total: int) -> float:
        """
        计算位置权重（开头和结尾的片段权重更高）
        
        Args:
            index: 片段索引
            total: 总片段数
            
        Returns:
            float: 位置权重
        """
        if total <= 1:
            return 1.0
        
        # 开头和结尾权重更高
        if index == 0 or index == total - 1:
            return 1.2
        elif index < total * 0.1 or index > total * 0.9:
            return 1.1
        else:
            return 1.0
    
    async def _save_content_segments(self, article_vector_id: int, segments: List[Dict]):
        """
        保存内容片段向量
        
        Args:
            article_vector_id: 文章向量ID
            segments: 片段列表
        """
        try:
            # 先删除现有的片段向量
            delete_query = text("""
                DELETE FROM content_segment_vectors 
                WHERE article_vector_id = :article_vector_id
            """)
            await self.session.execute(delete_query, {"article_vector_id": article_vector_id})
            
            # 插入新的片段向量
            for segment in segments:
                segment_vector_json = self._vector_to_json(segment['vector'])
                
                insert_query = text("""
                    INSERT INTO content_segment_vectors (
                        article_vector_id, segment_index, segment_text, segment_vector,
                        segment_length, start_char_pos, end_char_pos,
                        confidence_score, semantic_density, keyword_density,
                        is_key_segment, segment_type, created_at
                    ) VALUES (
                        :article_vector_id, :segment_index, :segment_text, :segment_vector,
                        :segment_length, :start_char_pos, :end_char_pos,
                        :confidence_score, :semantic_density, :keyword_density,
                        :is_key_segment, :segment_type, :created_at
                    )
                """)
                
                await self.session.execute(insert_query, {
                    "article_vector_id": article_vector_id,
                    "segment_index": segment['index'],
                    "segment_text": segment['text'],
                    "segment_vector": segment_vector_json,
                    "segment_length": segment['length'],
                    "start_char_pos": segment['start_pos'],
                    "end_char_pos": segment['end_pos'],
                    "confidence_score": segment['confidence_score'],
                    "semantic_density": segment['semantic_density'],
                    "keyword_density": segment['keyword_density'],
                    "is_key_segment": segment['is_key_segment'],
                    "segment_type": "body",
                    "created_at": TimeUtils.now_utc()
                })
        except Exception as e:
            logger.error(f"保存文章 {article_vector_id} 片段向量失败: {e}")
            # 重新抛出异常，让上层处理事务回滚
            raise

    async def update_comment_vectors(self, comment_id: int, subject: str, content: str, projectitem_id: int) -> bool:
        """
        更新评论向量
        
        Args:
            comment_id: 评论ID
            subject: 评论标题
            content: 评论内容
            projectitem_id: 关联的文章ID
            
        Returns:
            bool: 更新是否成功
        """
        try:
            # 获取向量化服务
            vectorization_service = await self._get_vectorization_service()
            
            # 如果向量化服务不可用，跳过向量化更新
            if vectorization_service is None:
                logger.warning(f"向量化服务不可用，跳过评论 {comment_id} 的向量化更新")
                return False
            
            # 向量化标题（应用过滤原则）
            title_text = subject or ""
            if self._should_skip_segment(title_text):
                # 如果标题应该被跳过，使用空向量
                title_vector = np.zeros(384)
                logger.debug(f"跳过评论 {comment_id} 的标题向量化: '{title_text[:50]}...'")
            else:
                title_vector = await vectorization_service.vectorize_text(title_text)
            
            # 向量化内容（应用过滤原则）
            content_text = content or ""
            if self._should_skip_segment(content_text):
                # 如果内容应该被跳过，使用空向量
                content_vector = np.zeros(384)
                logger.debug(f"跳过评论 {comment_id} 的内容向量化: '{content_text[:50]}...'")
            else:
                content_vector = await vectorization_service.vectorize_text(content_text)
            
            # 计算统计信息
            total_text_length = len(content or "")
            segment_count = 1  # 评论不分段
            max_segment_length = total_text_length
            
            # 检查是否已存在向量记录
            existing_vector = await self._get_existing_comment_vector(comment_id)
            
            if existing_vector:
                # 更新现有记录
                await self._update_existing_comment_vector(
                    comment_id, subject, content, title_vector, content_vector,
                    total_text_length, segment_count, max_segment_length, projectitem_id
                )
            else:
                # 创建新记录
                await self._create_new_comment_vector(
                    comment_id, subject, content, title_vector, content_vector,
                    total_text_length, segment_count, max_segment_length, projectitem_id
                )
            
            # 注意：不在这里提交事务，由调用方管理事务
            # 这样可以确保向量化更新与评论创建在同一个事务中
            
            return True
            
        except Exception as e:
            logger.error(f"更新评论 {comment_id} 向量失败: {e}")
            return False

    async def delete_comment_vectors(self, comment_id: int) -> bool:
        """
        删除评论向量
        
        Args:
            comment_id: 评论ID
            
        Returns:
            bool: 删除是否成功
        """
        try:
            # 删除评论向量记录
            query = text("""
                DELETE FROM comment_vectors 
                WHERE post_id = :comment_id
            """)
            
            await self.session.execute(query, {"comment_id": comment_id})
            
            # 注意：不在这里提交事务，由调用方管理事务
            # 这样可以确保向量化删除与评论删除在同一个事务中
            
            return True
            
        except Exception as e:
            logger.error(f"删除评论 {comment_id} 向量失败: {e}")
            return False

    async def _get_existing_comment_vector(self, comment_id: int) -> Optional[Dict]:
        """获取现有的评论向量记录"""
        try:
            query = text("""
                SELECT id, post_id, title_vector, content_vector, title_text, content_text,
                       segment_count, vectorization_method, total_text_length, max_segment_length,
                       avg_confidence, created_at, updated_at
                FROM comment_vectors 
                WHERE post_id = :comment_id
            """)
            result = await self.session.execute(query, {"comment_id": comment_id})
            row = result.fetchone()
            
            if row:
                return {
                    "id": row[0],
                    "post_id": row[1],
                    "title_vector": row[2],
                    "content_vector": row[3],
                    "title_text": row[4],
                    "content_text": row[5],
                    "segment_count": row[6],
                    "vectorization_method": row[7],
                    "total_text_length": row[8],
                    "max_segment_length": row[9],
                    "avg_confidence": row[10],
                    "created_at": row[11],
                    "updated_at": row[12]
                }
            return None
        except Exception as e:
            logger.error(f"获取评论 {comment_id} 现有向量记录失败: {e}")
            # 回滚事务
            try:
                await self.session.rollback()
            except Exception as rollback_error:
                logger.error(f"回滚事务失败: {rollback_error}")
            return None

    async def _update_existing_comment_vector(self, comment_id: int, subject: str, content: str,
                                           title_vector: np.ndarray, content_vector: np.ndarray,
                                           total_text_length: int, segment_count: int,
                                           max_segment_length: int, projectitem_id: int):
        """更新现有的评论向量记录"""
        try:
            query = text("""
                UPDATE comment_vectors 
                SET title_vector = :title_vector,
                    content_vector = :content_vector,
                    title_text = :title_text,
                    content_text = :content_text,
                    segment_count = :segment_count,
                    vectorization_method = :vectorization_method,
                    total_text_length = :total_text_length,
                    max_segment_length = :max_segment_length,
                    avg_confidence = :avg_confidence,
                    updated_at = :updated_at
                WHERE post_id = :comment_id
            """)
            
            # 将向量转换为JSON格式，与文章向量保持一致
            title_vector_json = self._vector_to_json(title_vector)
            content_vector_json = self._vector_to_json(content_vector)
            
            await self.session.execute(query, {
                "comment_id": comment_id,
                "title_vector": title_vector_json,
                "content_vector": content_vector_json,
                "title_text": subject or "",
                "content_text": content or "",
                "segment_count": segment_count,
                "vectorization_method": "bert",
                "total_text_length": total_text_length,
                "max_segment_length": max_segment_length,
                "avg_confidence": 1.0,
                "updated_at": TimeUtils.now_utc()
            })
            
        except Exception as e:
            logger.error(f"更新评论 {comment_id} 向量记录失败: {e}")
            # 回滚事务
            try:
                await self.session.rollback()
            except Exception as rollback_error:
                logger.error(f"回滚事务失败: {rollback_error}")
            raise

    async def _create_new_comment_vector(self, comment_id: int, subject: str, content: str,
                                       title_vector: np.ndarray, content_vector: np.ndarray,
                                       total_text_length: int, segment_count: int,
                                       max_segment_length: int, projectitem_id: int):
        """创建新的评论向量记录"""
        try:
            query = text("""
                INSERT INTO comment_vectors 
                (post_id, title_vector, content_vector, title_text, content_text,
                 segment_count, vectorization_method, total_text_length, max_segment_length,
                 avg_confidence, created_at, updated_at)
                VALUES 
                (:comment_id, :title_vector, :content_vector, :title_text, :content_text,
                 :segment_count, :vectorization_method, :total_text_length, :max_segment_length,
                 :avg_confidence, :created_at, :updated_at)
            """)
            
            # 将向量转换为JSON格式，与文章向量保持一致
            title_vector_json = self._vector_to_json(title_vector)
            content_vector_json = self._vector_to_json(content_vector)
            
            await self.session.execute(query, {
                "comment_id": comment_id,
                "title_vector": title_vector_json,
                "content_vector": content_vector_json,
                "title_text": subject or "",
                "content_text": content or "",
                "segment_count": segment_count,
                "vectorization_method": "bert",
                "total_text_length": total_text_length,
                "max_segment_length": max_segment_length,
                "avg_confidence": 1.0,
                "created_at": TimeUtils.now_utc(),
                "updated_at": TimeUtils.now_utc()
            })
            
        except Exception as e:
            logger.error(f"创建评论 {comment_id} 向量记录失败: {e}")
            # 回滚事务
            try:
                await self.session.rollback()
            except Exception as rollback_error:
                logger.error(f"回滚事务失败: {rollback_error}")
            raise


# 全局向量化更新服务实例缓存
_vectorization_services = {}

def get_vectorization_update_service(session: AsyncSession) -> VectorizationUpdateService:
    """
    获取向量化更新服务实例（支持实例复用）
    
    使用session的id作为缓存键，避免重复创建相同session的服务实例。
    
    Args:
        session: 数据库会话
        
    Returns:
        VectorizationUpdateService: 向量化更新服务实例
    """
    session_id = id(session)
    
    if session_id not in _vectorization_services:
        _vectorization_services[session_id] = VectorizationUpdateService(session)
    
    return _vectorization_services[session_id]
