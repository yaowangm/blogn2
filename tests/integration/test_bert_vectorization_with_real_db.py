#!/usr/bin/env python3
"""
BERT向量化功能集成测试

使用真实数据库测试BERT向量化的完整功能，包括：
- 文章向量化
- 评论向量化
- 搜索功能
- 批量处理
- 数据清理

测试特点：
- 使用真实PostgreSQL数据库
- 自动清理测试数据
- 验证向量化质量
- 测试搜索准确性
"""

import pytest
import asyncio
import numpy as np
from typing import List, Dict, Any
from unittest.mock import patch
import time

from src.services.vectorization_service import BERTVectorizationService
from src.services.vectorization_update_service import VectorizationUpdateService
from src.services.search_service import HierarchicalSearchService
from src.models.user import User
from src.models.project_item import ProjectItem
from src.models.post import Post
from sqlalchemy import text


class TestBERTVectorizationIntegration:
    """BERT向量化集成测试类"""
    
    @pytest.fixture(autouse=True)
    async def setup_test_data(self, real_async_session, test_data_tracker):
        """设置测试数据"""
        self.session = real_async_session
        self.tracker = test_data_tracker
        
        # 创建测试用户
        test_user = User(
            name="vectorization_test_user",
            email="vector_test@example.com",
            password="testpassword123",
            state=1
        )
        self.session.add(test_user)
        await self.session.flush()
        self.tracker.add_user(test_user.id)
        self.test_user_id = test_user.id
        
        # 创建测试文章
        test_article = ProjectItem(
            name="机器学习基础教程",
            comment="这是一篇关于机器学习基础知识的详细教程，包含算法原理、实现方法和实际应用案例。",
            userid=self.test_user_id,
            status=1
        )
        self.session.add(test_article)
        await self.session.flush()
        self.tracker.add_article(test_article.id)
        self.test_article_id = test_article.id
        
        # 创建测试评论
        test_comment = Post(
            subject="很好的教程",
            content="这篇教程写得非常详细，对初学者很有帮助。特别是算法原理部分解释得很清楚。",
            userid=self.test_user_id,
            projectitemid=self.test_article_id,
            status=1
        )
        self.session.add(test_comment)
        await self.session.flush()
        self.tracker.add_comment(test_comment.id)
        self.test_comment_id = test_comment.id
        
        await self.session.commit()
        
        yield
        
        # 测试结束后清理向量化数据
        await self._cleanup_vectorization_data()
    
    async def _cleanup_vectorization_data(self):
        """清理向量化相关数据"""
        try:
            # 删除文章向量
            await self.session.execute(text("""
                DELETE FROM article_vectors WHERE projectitem_id = :article_id
            """), {"article_id": self.test_article_id})
            
            # 删除评论向量
            await self.session.execute(text("""
                DELETE FROM comment_vectors WHERE post_id = :comment_id
            """), {"comment_id": self.test_comment_id})
            
            await self.session.commit()
        except Exception as e:
            print(f"清理向量化数据时出错: {e}")
    
    @pytest.mark.asyncio
    async def test_vectorization_service_basic_functionality(self):
        """测试向量化服务基本功能（使用已加载模型，不重置单例以免二次加载导致零向量）"""
        # 创建向量化服务（复用已加载模型，与 test_article_vectorization 等一致）
        vectorization_service = BERTVectorizationService()
        await vectorization_service.load_model()
        assert vectorization_service.is_model_loaded() == True

        # 测试文本向量化
        test_text = "这是一个测试文本"
        vector = await vectorization_service.vectorize_text(test_text)

        # 验证向量格式
        assert isinstance(vector, np.ndarray)
        assert vector.shape == (384,)  # 384维向量
        assert not np.any(np.isnan(vector)), "向量不应含 nan"
        assert np.linalg.norm(vector) > 1e-6, (
            "模型返回零向量，请确认 MODEL_MODEL_PATH / BERT_MODEL_HUB_HOST_PATH 指向有效本地模型"
        )
        
        # 测试空文本处理
        empty_vector = await vectorization_service.vectorize_text("")
        assert isinstance(empty_vector, np.ndarray)
        assert empty_vector.shape == (384,)
        assert np.allclose(empty_vector, 0)  # 空文本返回零向量
        
        # 测试批量向量化
        texts = ["文本1", "文本2", "文本3"]
        vectors = await vectorization_service.vectorize_batch(texts)
        
        assert len(vectors) == 3
        for vector in vectors:
            assert isinstance(vector, np.ndarray)
            assert vector.shape == (384,)
    
    @pytest.mark.asyncio
    async def test_article_vectorization(self):
        """测试文章向量化功能"""
        # 创建向量化更新服务
        update_service = VectorizationUpdateService(self.session)
        
        # 向量化测试文章
        success = await update_service.update_article_vectors(
            self.test_article_id,
            "机器学习基础教程",
            "这是一篇关于机器学习基础知识的详细教程，包含算法原理、实现方法和实际应用案例。机器学习是人工智能的一个重要分支，它通过算法和统计模型使计算机系统能够自动学习和改进性能。深度学习作为机器学习的子领域，使用多层神经网络来模拟人脑的工作方式，在图像识别、自然语言处理等领域取得了突破性进展。"
        )
        
        assert success == True
        
        # 验证文章向量是否创建
        result = await self.session.execute(text("""
            SELECT id, title_text, content_text, segment_count
            FROM article_vectors 
            WHERE projectitem_id = :article_id
        """), {"article_id": self.test_article_id})
        
        article_vector = result.fetchone()
        assert article_vector is not None
        assert article_vector[1] == "机器学习基础教程"
        assert article_vector[2] == "这是一篇关于机器学习基础知识的详细教程，包含算法原理、实现方法和实际应用案例。机器学习是人工智能的一个重要分支，它通过算法和统计模型使计算机系统能够自动学习和改进性能。深度学习作为机器学习的子领域，使用多层神经网络来模拟人脑的工作方式，在图像识别、自然语言处理等领域取得了突破性进展。"
        assert article_vector[3] >= 1  # 至少有一个片段
        
        # 验证片段向量是否创建
        segment_result = await self.session.execute(text("""
            SELECT COUNT(*) FROM content_segment_vectors 
            WHERE article_vector_id = :article_vector_id
        """), {"article_vector_id": article_vector[0]})
        
        segment_count = segment_result.fetchone()[0]
        assert segment_count > 0
    
    @pytest.mark.asyncio
    async def test_comment_vectorization(self):
        """测试评论向量化功能"""
        # 创建向量化更新服务
        update_service = VectorizationUpdateService(self.session)
        
        # 向量化测试评论
        success = await update_service.update_comment_vectors(
            self.test_comment_id,
            "很好的教程",
            "这篇教程写得非常详细，对初学者很有帮助。特别是算法原理部分解释得很清楚。",
            self.test_article_id
        )
        
        assert success == True
        
        # 验证评论向量是否创建
        result = await self.session.execute(text("""
            SELECT id, title_text, content_text, segment_count
            FROM comment_vectors 
            WHERE post_id = :comment_id
        """), {"comment_id": self.test_comment_id})
        
        comment_vector = result.fetchone()
        assert comment_vector is not None
        assert comment_vector[1] == "很好的教程"
        assert comment_vector[2] == "这篇教程写得非常详细，对初学者很有帮助。特别是算法原理部分解释得很清楚。"
        assert comment_vector[3] == 1  # 评论不分段
    
    @pytest.mark.asyncio
    async def test_search_functionality(self):
        """测试搜索功能"""
        # 先创建向量化数据
        update_service = VectorizationUpdateService(self.session)
        
        # 向量化文章
        await update_service.update_article_vectors(
            self.test_article_id,
            "机器学习基础教程",
            "这是一篇关于机器学习基础知识的详细教程，包含算法原理、实现方法和实际应用案例。"
        )
        
        # 向量化评论
        await update_service.update_comment_vectors(
            self.test_comment_id,
            "很好的教程",
            "这篇教程写得非常详细，对初学者很有帮助。特别是算法原理部分解释得很清楚。",
            self.test_article_id
        )
        
        await self.session.commit()
        
        # 创建搜索服务
        vectorization_service = BERTVectorizationService()
        await vectorization_service.load_model()
        search_service = HierarchicalSearchService(vectorization_service, self.session)
        
        # 测试文章搜索
        article_results = await search_service.search(
            query="机器学习算法",
            search_type="articles",
            page=1,
            limit=10
        )
        
        assert "items" in article_results
        assert "total" in article_results
        assert "search_time" in article_results
        assert article_results["total"] >= 0
        
        # 测试评论搜索
        comment_results = await search_service.search(
            query="教程详细",
            search_type="comments",
            page=1,
            limit=10
        )
        
        assert "items" in comment_results
        assert "total" in comment_results
        assert comment_results["total"] >= 0
        
        # 测试混合搜索
        all_results = await search_service.search(
            query="机器学习",
            search_type="all",
            page=1,
            limit=10
        )
        
        assert "items" in all_results
        assert "total" in all_results
        assert all_results["total"] >= 0
    
    @pytest.mark.asyncio
    async def test_dynamic_threshold_calculation(self):
        """测试动态阈值计算"""
        vectorization_service = BERTVectorizationService()
        await vectorization_service.load_model()
        search_service = HierarchicalSearchService(vectorization_service, self.session)
        
        # 测试不同查询的阈值
        test_queries = [
            "AI",  # 短查询
            "机器学习算法",  # 中等查询
            "深度学习神经网络算法原理",  # 长查询
            "Python编程123",  # 包含数字
            "测试@#$%",  # 包含特殊字符
        ]
        
        for query in test_queries:
            query_vector = await vectorization_service.vectorize_text(query)
            query_vector_json = search_service._vector_to_json(query_vector)
            threshold = search_service.calculate_dynamic_threshold(query, query_vector_json)
            
            # 验证阈值在合理范围内
            assert 0.1 <= threshold <= 0.9
            print(f"查询 '{query}' 的阈值: {threshold:.3f}")
    
    @pytest.mark.asyncio
    async def test_vectorization_quality(self):
        """测试向量化质量（使用已加载模型，不重置单例以免二次加载导致零向量/nan）"""
        vectorization_service = BERTVectorizationService()
        await vectorization_service.load_model()

        # 测试相似文本的向量相似度
        text1 = "机器学习算法"
        text2 = "机器学习方法"
        text3 = "深度学习技术"

        vector1 = await vectorization_service.vectorize_text(text1)
        vector2 = await vectorization_service.vectorize_text(text2)
        vector3 = await vectorization_service.vectorize_text(text3)

        # 计算余弦相似度（零向量会得到 nan，需先排除）
        def cosine_similarity(a, b):
            na, nb = np.linalg.norm(a), np.linalg.norm(b)
            if na < 1e-9 or nb < 1e-9:
                return float("nan")
            return float(np.dot(a, b) / (na * nb))

        sim_1_2 = cosine_similarity(vector1, vector2)
        sim_1_3 = cosine_similarity(vector1, vector3)

        assert not np.isnan(sim_1_2) and not np.isnan(sim_1_3), (
            "向量为零或无效导致相似度为 nan，请检查 MODEL_MODEL_PATH / 本地模型路径"
        )
        # 相似文本应该有更高的相似度
        assert sim_1_2 > sim_1_3, f"相似文本相似度应更高: sim(1,2)={sim_1_2:.3f}, sim(1,3)={sim_1_3:.3f}"
        assert sim_1_2 > 0.5, f"相似度应较高: {sim_1_2:.3f}"
        print(f"'{text1}' 和 '{text2}' 的相似度: {sim_1_2:.3f}")
        print(f"'{text1}' 和 '{text3}' 的相似度: {sim_1_3:.3f}")
    
    @pytest.mark.asyncio
    async def test_text_preprocessing(self):
        """测试文本预处理功能"""
        vectorization_service = BERTVectorizationService()
        
        # 测试各种文本预处理
        test_cases = [
            ("<p>HTML标签</p>", "HTML标签"),
            ("  多余空格  ", "多余空格"),
            ("特殊字符!@#$%", "特殊字符"),
            ("换行符\n\n测试", "换行符 测试"),
            ("", ""),
            ("a" * 3000, "a" * 2000),  # 超长文本截断
        ]
        
        for input_text, expected in test_cases:
            result = vectorization_service._preprocess_text(input_text)
            assert result == expected
            print(f"预处理: '{input_text[:20]}...' -> '{result[:20]}...'")
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """测试错误处理"""
        # 测试向量化服务错误处理
        vectorization_service = BERTVectorizationService()
        
        # 测试空文本
        empty_vector = await vectorization_service.vectorize_text("")
        assert np.allclose(empty_vector, 0)
        
        # 测试None文本
        none_vector = await vectorization_service.vectorize_text(None)
        assert np.allclose(none_vector, 0)
        
        # 测试更新服务错误处理
        update_service = VectorizationUpdateService(self.session)
        
        # 测试不存在的文章ID
        success = await update_service.update_article_vectors(
            99999,  # 不存在的ID
            "测试标题",
            "测试内容"
        )
        assert success == False
        
        # 测试不存在的评论ID
        success = await update_service.update_comment_vectors(
            99999,  # 不存在的ID
            "测试标题",
            "测试内容",
            1
        )
        assert success == False
    
    @pytest.mark.asyncio
    async def test_batch_processing(self):
        """测试批量处理功能"""
        # 创建多个测试文章
        test_articles = []
        for i in range(3):
            article = ProjectItem(
                name=f"测试文章{i+1}",
                comment=f"这是第{i+1}篇测试文章的内容，用于测试批量向量化功能。",
                userid=self.test_user_id,
                status=1
            )
            self.session.add(article)
            test_articles.append(article)
        
        await self.session.flush()
        
        # 记录文章ID用于清理
        for article in test_articles:
            self.tracker.add_article(article.id)
        
        await self.session.commit()
        
        # 测试批量向量化
        update_service = VectorizationUpdateService(self.session)
        
        article_ids = [article.id for article in test_articles]
        result = await update_service.batch_update_articles(article_ids)
        
        assert result["total"] == 3
        assert result["success"] == 3
        assert result["failed"] == 0
        assert len(result["failed_articles"]) == 0
        
        # 验证向量是否创建
        for article_id in article_ids:
            vector_result = await self.session.execute(text("""
                SELECT COUNT(*) FROM article_vectors 
                WHERE projectitem_id = :article_id
            """), {"article_id": article_id})
            
            count = vector_result.fetchone()[0]
            assert count == 1
    
    @pytest.mark.asyncio
    async def test_vectorization_status(self):
        """测试向量化状态查询"""
        update_service = VectorizationUpdateService(self.session)
        
        # 先向量化文章
        await update_service.update_article_vectors(
            self.test_article_id,
            "机器学习基础教程",
            "这是一篇关于机器学习基础知识的详细教程。"
        )
        await self.session.commit()
        
        # 查询向量化状态
        status = await update_service.get_vectorization_status(self.test_article_id)
        
        assert status["vectorized"] == True
        assert "vector_id" in status
        assert status["title_text"] == "机器学习基础教程"
        assert status["content_text"] == "这是一篇关于机器学习基础知识的详细教程。"
        assert status["segment_count"] >= 1
        assert status["total_text_length"] > 0
        
        # 测试未向量化的文章
        unvectorized_status = await update_service.get_vectorization_status(99999)
        assert unvectorized_status["vectorized"] == False
        assert "message" in unvectorized_status
    
    @pytest.mark.asyncio
    async def test_data_cleanup(self):
        """测试数据清理功能"""
        update_service = VectorizationUpdateService(self.session)
        
        # 先创建向量化数据
        await update_service.update_article_vectors(
            self.test_article_id,
            "测试文章",
            "测试内容"
        )
        
        await update_service.update_comment_vectors(
            self.test_comment_id,
            "测试评论",
            "测试评论内容",
            self.test_article_id
        )
        
        await self.session.commit()
        
        # 验证数据存在
        article_count = await self.session.execute(text("""
            SELECT COUNT(*) FROM article_vectors 
            WHERE projectitem_id = :article_id
        """), {"article_id": self.test_article_id})
        assert article_count.fetchone()[0] == 1
        
        comment_count = await self.session.execute(text("""
            SELECT COUNT(*) FROM comment_vectors 
            WHERE post_id = :comment_id
        """), {"comment_id": self.test_comment_id})
        assert comment_count.fetchone()[0] == 1
        
        # 删除向量化数据
        article_success = await update_service.delete_article_vectors(self.test_article_id)
        comment_success = await update_service.delete_comment_vectors(self.test_comment_id)
        
        assert article_success == True
        assert comment_success == True
        
        await self.session.commit()
        
        # 验证数据已删除
        article_count_after = await self.session.execute(text("""
            SELECT COUNT(*) FROM article_vectors 
            WHERE projectitem_id = :article_id
        """), {"article_id": self.test_article_id})
        assert article_count_after.fetchone()[0] == 0
        
        comment_count_after = await self.session.execute(text("""
            SELECT COUNT(*) FROM comment_vectors 
            WHERE post_id = :comment_id
        """), {"comment_id": self.test_comment_id})
        assert comment_count_after.fetchone()[0] == 0


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])
