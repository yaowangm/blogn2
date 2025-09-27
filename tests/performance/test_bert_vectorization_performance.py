#!/usr/bin/env python3
"""
BERT向量化性能测试

测试BERT向量化功能的性能表现，包括：
- 向量化速度测试
- 内存使用测试
- 并发处理测试
- 搜索性能测试

测试特点：
- 使用真实数据库
- 测量实际性能指标
- 验证性能要求
- 提供性能基准
"""

import pytest
import asyncio
import time
import psutil
import os
from typing import List, Dict, Any
import numpy as np

from src.services.vectorization_service import BERTVectorizationService
from src.services.vectorization_update_service import VectorizationUpdateService
from src.services.search_service import HierarchicalSearchService
from src.models.user import User
from src.models.project_item import ProjectItem
from src.models.post import Post
from sqlalchemy import text


class TestBERTVectorizationPerformance:
    """BERT向量化性能测试类"""
    
    @pytest.fixture(autouse=True)
    async def setup_performance_test_data(self, real_async_session, test_data_tracker):
        """设置性能测试数据"""
        self.session = real_async_session
        self.tracker = test_data_tracker
        
        # 创建测试用户
        test_user = User(
            name="perf_test_user",
            email="perf_test@example.com",
            password="testpassword123",
            state=1
        )
        self.session.add(test_user)
        await self.session.flush()
        self.tracker.add_user(test_user.id)
        self.test_user_id = test_user.id
        
        # 创建大量测试文章用于性能测试
        self.test_articles = []
        for i in range(10):  # 创建10篇测试文章
            article = ProjectItem(
                name=f"性能测试文章{i+1}",
                comment=f"这是第{i+1}篇性能测试文章，包含大量文本内容用于测试向量化性能。文章内容涉及机器学习、深度学习、自然语言处理等多个技术领域，旨在验证BERT向量化系统的处理能力和性能表现。",
                userid=self.test_user_id,
                status=1
            )
            self.session.add(article)
            self.test_articles.append(article)
        
        await self.session.flush()
        
        # 记录文章ID用于清理
        for article in self.test_articles:
            self.tracker.add_article(article.id)
        
        await self.session.commit()
        
        yield
        
        # 测试结束后清理向量化数据
        await self._cleanup_performance_test_data()
    
    async def _cleanup_performance_test_data(self):
        """清理性能测试数据"""
        try:
            article_ids = [article.id for article in self.test_articles]
            if article_ids:
                # 删除文章向量
                await self.session.exec(text("""
                    DELETE FROM article_vectors WHERE projectitem_id = ANY(:article_ids)
                """), {"article_ids": article_ids})
                
                await self.session.commit()
        except Exception as e:
            print(f"清理性能测试数据时出错: {e}")
    
    @pytest.mark.asyncio
    async def test_single_text_vectorization_speed(self):
        """测试单文本向量化速度"""
        vectorization_service = BERTVectorizationService()
        await vectorization_service.load_model()
        
        test_texts = [
            "短文本",
            "这是一个中等长度的测试文本，用于测试向量化性能。",
            "这是一个较长的测试文本，包含更多的内容和信息，用于测试BERT模型在处理长文本时的性能表现。文本内容涉及多个技术领域，包括机器学习、深度学习、自然语言处理等，旨在全面评估向量化系统的处理能力。",
        ]
        
        results = {}
        
        for text in test_texts:
            # 预热
            await vectorization_service.vectorize_text(text)
            
            # 正式测试
            start_time = time.time()
            vector = await vectorization_service.vectorize_text(text)
            end_time = time.time()
            
            processing_time = end_time - start_time
            results[len(text)] = {
                "text_length": len(text),
                "processing_time": processing_time,
                "vector_shape": vector.shape,
                "speed_chars_per_sec": len(text) / processing_time if processing_time > 0 else 0
            }
            
            print(f"文本长度: {len(text)}, 处理时间: {processing_time:.3f}秒, 速度: {len(text)/processing_time:.1f}字符/秒")
        
        # 验证性能要求
        for length, result in results.items():
            assert result["processing_time"] < 5.0, f"文本长度{length}的处理时间过长: {result['processing_time']:.3f}秒"
            assert result["vector_shape"] == (384,), f"向量维度不正确: {result['vector_shape']}"
    
    @pytest.mark.asyncio
    async def test_batch_vectorization_speed(self):
        """测试批量向量化速度"""
        vectorization_service = BERTVectorizationService()
        await vectorization_service.load_model()
        
        # 准备测试数据
        batch_sizes = [1, 5, 10, 20]
        test_text = "批量向量化性能测试文本"
        
        results = {}
        
        for batch_size in batch_sizes:
            texts = [test_text] * batch_size
            
            # 预热
            await vectorization_service.vectorize_batch(texts)
            
            # 正式测试
            start_time = time.time()
            vectors = await vectorization_service.vectorize_batch(texts)
            end_time = time.time()
            
            processing_time = end_time - start_time
            avg_time_per_text = processing_time / batch_size
            
            results[batch_size] = {
                "batch_size": batch_size,
                "total_time": processing_time,
                "avg_time_per_text": avg_time_per_text,
                "texts_per_second": batch_size / processing_time if processing_time > 0 else 0,
                "vectors_count": len(vectors)
            }
            
            print(f"批量大小: {batch_size}, 总时间: {processing_time:.3f}秒, 平均每文本: {avg_time_per_text:.3f}秒, 速度: {batch_size/processing_time:.1f}文本/秒")
        
        # 验证批量处理效率
        for batch_size, result in results.items():
            assert result["vectors_count"] == batch_size, f"批量大小{batch_size}的向量数量不正确"
            assert result["total_time"] < 10.0, f"批量大小{batch_size}的处理时间过长"
    
    @pytest.mark.asyncio
    async def test_memory_usage(self):
        """测试内存使用情况"""
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        vectorization_service = BERTVectorizationService()
        await vectorization_service.load_model()
        
        model_loaded_memory = process.memory_info().rss / 1024 / 1024  # MB
        model_memory_usage = model_loaded_memory - initial_memory
        
        print(f"初始内存: {initial_memory:.1f}MB")
        print(f"模型加载后内存: {model_loaded_memory:.1f}MB")
        print(f"模型内存使用: {model_memory_usage:.1f}MB")
        
        # 验证内存使用合理
        assert model_memory_usage < 2000, f"模型内存使用过多: {model_memory_usage:.1f}MB"
        
        # 测试大量向量化时的内存使用
        vectors = []
        for i in range(100):
            vector = await vectorization_service.vectorize_text(f"测试文本{i}")
            vectors.append(vector)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        total_memory_usage = final_memory - initial_memory
        
        print(f"100个向量后内存: {final_memory:.1f}MB")
        print(f"总内存使用: {total_memory_usage:.1f}MB")
        
        # 验证内存使用稳定
        assert total_memory_usage < 3000, f"总内存使用过多: {total_memory_usage:.1f}MB"
    
    @pytest.mark.asyncio
    async def test_concurrent_vectorization(self):
        """测试并发向量化性能"""
        vectorization_service = BERTVectorizationService()
        await vectorization_service.load_model()
        
        # 准备并发测试数据
        num_concurrent = 5
        texts_per_task = 10
        test_text = "并发向量化性能测试文本"
        
        async def vectorize_batch(texts):
            """并发向量化任务"""
            return await vectorization_service.vectorize_batch(texts)
        
        # 创建并发任务
        tasks = []
        for i in range(num_concurrent):
            texts = [f"{test_text}_{i}_{j}" for j in range(texts_per_task)]
            task = asyncio.create_task(vectorize_batch(texts))
            tasks.append(task)
        
        # 执行并发测试
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        total_time = end_time - start_time
        total_texts = num_concurrent * texts_per_task
        texts_per_second = total_texts / total_time
        
        print(f"并发任务数: {num_concurrent}")
        print(f"每任务文本数: {texts_per_task}")
        print(f"总文本数: {total_texts}")
        print(f"总时间: {total_time:.3f}秒")
        print(f"并发速度: {texts_per_second:.1f}文本/秒")
        
        # 验证并发处理结果
        assert len(results) == num_concurrent
        for i, result in enumerate(results):
            assert len(result) == texts_per_task, f"任务{i}的向量数量不正确"
            for vector in result:
                assert vector.shape == (384,), f"任务{i}的向量维度不正确"
        
        # 验证并发性能
        assert total_time < 30.0, f"并发处理时间过长: {total_time:.3f}秒"
        assert texts_per_second > 1.0, f"并发处理速度过慢: {texts_per_second:.1f}文本/秒"
    
    @pytest.mark.asyncio
    async def test_article_vectorization_performance(self):
        """测试文章向量化性能"""
        update_service = VectorizationUpdateService(self.session)
        
        # 测试单篇文章向量化性能
        article = self.test_articles[0]
        start_time = time.time()
        
        success = await update_service.update_article_vectors(
            article.id,
            article.name,
            article.comment
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        assert success == True
        print(f"单篇文章向量化时间: {processing_time:.3f}秒")
        
        # 验证性能要求
        assert processing_time < 10.0, f"文章向量化时间过长: {processing_time:.3f}秒"
        
        # 测试批量文章向量化性能
        article_ids = [article.id for article in self.test_articles[1:6]]  # 使用5篇文章
        
        start_time = time.time()
        result = await update_service.batch_update_articles(article_ids)
        end_time = time.time()
        
        batch_processing_time = end_time - start_time
        avg_time_per_article = batch_processing_time / len(article_ids)
        
        print(f"批量文章向量化时间: {batch_processing_time:.3f}秒")
        print(f"平均每篇文章: {avg_time_per_article:.3f}秒")
        print(f"成功: {result['success']}, 失败: {result['failed']}")
        
        # 验证批量处理结果
        assert result["success"] == len(article_ids)
        assert result["failed"] == 0
        assert batch_processing_time < 60.0, f"批量文章向量化时间过长: {batch_processing_time:.3f}秒"
    
    @pytest.mark.asyncio
    async def test_search_performance(self):
        """测试搜索性能"""
        # 先创建向量化数据
        update_service = VectorizationUpdateService(self.session)
        
        for article in self.test_articles[:5]:  # 向量化5篇文章
            await update_service.update_article_vectors(
                article.id,
                article.name,
                article.comment
            )
        
        await self.session.commit()
        
        # 创建搜索服务
        vectorization_service = BERTVectorizationService()
        await vectorization_service.load_model()
        search_service = HierarchicalSearchService(vectorization_service, self.session)
        
        # 测试不同查询的搜索性能
        test_queries = [
            "机器学习",
            "深度学习算法",
            "自然语言处理技术",
            "人工智能应用",
            "神经网络模型"
        ]
        
        search_results = {}
        
        for query in test_queries:
            start_time = time.time()
            
            result = await search_service.search(
                query=query,
                search_type="articles",
                page=1,
                limit=10
            )
            
            end_time = time.time()
            search_time = end_time - start_time
            
            search_results[query] = {
                "query": query,
                "search_time": search_time,
                "total_results": result["total"],
                "returned_items": len(result["items"])
            }
            
            print(f"查询: '{query}', 搜索时间: {search_time:.3f}秒, 结果数: {result['total']}")
        
        # 验证搜索性能
        avg_search_time = sum(r["search_time"] for r in search_results.values()) / len(search_results)
        print(f"平均搜索时间: {avg_search_time:.3f}秒")
        
        assert avg_search_time < 2.0, f"平均搜索时间过长: {avg_search_time:.3f}秒"
        
        for query, result in search_results.items():
            assert result["search_time"] < 5.0, f"查询'{query}'的搜索时间过长: {result['search_time']:.3f}秒"
    
    @pytest.mark.asyncio
    async def test_large_text_processing(self):
        """测试大文本处理性能"""
        vectorization_service = BERTVectorizationService()
        await vectorization_service.load_model()
        
        # 创建不同大小的文本
        text_sizes = [100, 500, 1000, 2000, 5000]  # 字符数
        
        results = {}
        
        for size in text_sizes:
            # 生成指定大小的文本
            text = "这是一个性能测试文本。" * (size // 10)
            text = text[:size]  # 精确控制长度
            
            start_time = time.time()
            vector = await vectorization_service.vectorize_text(text)
            end_time = time.time()
            
            processing_time = end_time - start_time
            chars_per_second = size / processing_time if processing_time > 0 else 0
            
            results[size] = {
                "text_size": size,
                "processing_time": processing_time,
                "chars_per_second": chars_per_second,
                "vector_shape": vector.shape
            }
            
            print(f"文本大小: {size}字符, 处理时间: {processing_time:.3f}秒, 速度: {chars_per_second:.1f}字符/秒")
        
        # 验证大文本处理性能
        for size, result in results.items():
            assert result["processing_time"] < 10.0, f"文本大小{size}的处理时间过长"
            assert result["vector_shape"] == (384,), f"文本大小{size}的向量维度不正确"
    
    @pytest.mark.asyncio
    async def test_vectorization_consistency(self):
        """测试向量化一致性"""
        vectorization_service = BERTVectorizationService()
        await vectorization_service.load_model()
        
        test_text = "一致性测试文本"
        
        # 多次向量化同一文本
        vectors = []
        for i in range(5):
            vector = await vectorization_service.vectorize_text(test_text)
            vectors.append(vector)
        
        # 验证向量一致性
        for i in range(1, len(vectors)):
            np.testing.assert_array_almost_equal(
                vectors[0], vectors[i], decimal=5,
                err_msg=f"第{i+1}次向量化结果与第1次不一致"
            )
        
        print("向量化一致性测试通过")
    
    @pytest.mark.asyncio
    async def test_memory_cleanup(self):
        """测试内存清理"""
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 创建和销毁多个向量化服务实例
        for i in range(10):
            vectorization_service = BERTVectorizationService()
            await vectorization_service.load_model()
            
            # 进行一些向量化操作
            for j in range(10):
                await vectorization_service.vectorize_text(f"测试文本{i}_{j}")
            
            # 删除引用（模拟服务销毁）
            del vectorization_service
        
        # 强制垃圾回收
        import gc
        gc.collect()
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        print(f"初始内存: {initial_memory:.1f}MB")
        print(f"最终内存: {final_memory:.1f}MB")
        print(f"内存增长: {memory_increase:.1f}MB")
        
        # 验证内存没有显著泄漏
        assert memory_increase < 500, f"内存泄漏过多: {memory_increase:.1f}MB"


if __name__ == "__main__":
    # 运行性能测试
    pytest.main([__file__, "-v", "--tb=short", "-s"])
