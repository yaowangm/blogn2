#!/usr/bin/env python3
"""
BERT向量化服务单元测试

测试BERT向量化相关服务的独立功能，不依赖数据库：
- BERTVectorizationService
- VectorizationUpdateService (模拟数据库)
- HierarchicalSearchService (模拟数据库)

测试特点：
- 使用模拟对象，不依赖真实数据库
- 快速执行，适合持续集成
- 测试核心业务逻辑
"""

import pytest
import numpy as np
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List, Dict, Any

from src.services.vectorization_service import BERTVectorizationService
from src.services.vectorization_update_service import VectorizationUpdateService
from src.services.search_service import HierarchicalSearchService


class TestBERTVectorizationService:
    """BERT向量化服务单元测试"""
    
    @pytest.fixture
    def vectorization_service(self):
        """创建向量化服务实例"""
        return BERTVectorizationService()
    
    @pytest.mark.asyncio
    async def test_singleton_pattern(self):
        """测试单例模式"""
        service1 = BERTVectorizationService()
        service2 = BERTVectorizationService()
        
        assert service1 is service2
        assert id(service1) == id(service2)
    
    @pytest.mark.asyncio
    async def test_model_loading(self, vectorization_service):
        """测试模型加载"""
        # 重置模型状态，确保测试隔离
        BERTVectorizationService._model_loaded = False
        BERTVectorizationService._loading = False
        BERTVectorizationService._model = None
        
        # 模拟模型加载成功
        with patch.object(vectorization_service, '_load_model_sync') as mock_load:
            mock_load.return_value = None
            
            await vectorization_service.load_model()
            
            assert vectorization_service.is_model_loaded() == True
            mock_load.assert_called_once()

    @pytest.mark.asyncio
    async def test_model_loading_wait_timeout_returns_without_hanging(self, vectorization_service):
        """等待加载时 300s 超时后直接返回，不无限等待（避免加载线程异常时卡死）"""
        BERTVectorizationService._model_loaded = False
        BERTVectorizationService._loading = True
        BERTVectorizationService._model = None
        time_values = [0.0, 301.0]
        mock_loop = MagicMock()
        mock_loop.time.side_effect = lambda: time_values.pop(0) if time_values else 302.0
        try:
            with patch("asyncio.get_running_loop", return_value=mock_loop):
                await vectorization_service.load_model()
            assert vectorization_service.is_model_loaded() is False
        finally:
            BERTVectorizationService._loading = False

    @pytest.mark.asyncio
    async def test_text_vectorization(self, vectorization_service):
        """测试文本向量化"""
        # 模拟向量化结果
        mock_vector = np.random.rand(384).astype(np.float32)
        
        with patch.object(vectorization_service, '_vectorize_sync', return_value=mock_vector):
            with patch.object(vectorization_service, 'is_model_loaded', return_value=True):
                result = await vectorization_service.vectorize_text("测试文本")
                
                assert isinstance(result, np.ndarray)
                assert result.shape == (384,)
                np.testing.assert_array_equal(result, mock_vector)
    
    @pytest.mark.asyncio
    async def test_empty_text_handling(self, vectorization_service):
        """测试空文本处理"""
        with patch.object(vectorization_service, 'is_model_loaded', return_value=True):
            # 测试空字符串
            result1 = await vectorization_service.vectorize_text("")
            assert isinstance(result1, np.ndarray)
            assert result1.shape == (384,)
            assert np.allclose(result1, 0)
            
            # 测试None
            result2 = await vectorization_service.vectorize_text(None)
            assert isinstance(result2, np.ndarray)
            assert result2.shape == (384,)
            assert np.allclose(result2, 0)
            
            # 测试只有空格的字符串
            result3 = await vectorization_service.vectorize_text("   \n\t  ")
            assert isinstance(result3, np.ndarray)
            assert result3.shape == (384,)
            assert np.allclose(result3, 0)
    
    @pytest.mark.asyncio
    async def test_batch_vectorization(self, vectorization_service):
        """测试批量向量化"""
        texts = ["文本1", "文本2", "文本3"]
        mock_vectors = [np.random.rand(384) for _ in texts]
        
        with patch.object(vectorization_service, '_vectorize_batch_sync', return_value=mock_vectors):
            with patch.object(vectorization_service, 'is_model_loaded', return_value=True):
                results = await vectorization_service.vectorize_batch(texts)
                
                assert len(results) == 3
                for i, result in enumerate(results):
                    assert isinstance(result, np.ndarray)
                    assert result.shape == (384,)
                    np.testing.assert_array_equal(result, mock_vectors[i])
    
    @pytest.mark.asyncio
    async def test_text_preprocessing(self, vectorization_service):
        """测试文本预处理"""
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
    
    @pytest.mark.asyncio
    async def test_vector_conversion(self, vectorization_service):
        """测试向量转换功能"""
        # 测试向量转JSON
        test_vector = np.array([1.0, 2.0, 3.0])
        json_str = vectorization_service.vector_to_json(test_vector)
        
        assert isinstance(json_str, str)
        assert json_str == "[1.0, 2.0, 3.0]"
        
        # 测试JSON转向量
        converted_vector = vectorization_service.json_to_vector(json_str)
        np.testing.assert_array_equal(converted_vector, test_vector)
        
        # 测试无效JSON
        invalid_vector = vectorization_service.json_to_vector("invalid json")
        assert isinstance(invalid_vector, np.ndarray)
        assert invalid_vector.shape == (384,)
        assert np.allclose(invalid_vector, 0)
    
    @pytest.mark.asyncio
    async def test_model_info(self, vectorization_service):
        """测试模型信息获取"""
        info = await vectorization_service.get_model_info()
        
        assert "model_name" in info
        assert "model_loaded" in info
        assert "max_length" in info
        assert "device" in info
        assert "vector_dimension" in info
        
        assert info["model_name"] == "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        assert info["max_length"] == 512
        assert info["vector_dimension"] == 384

    def test_shutdown_executor_releases_executor(self):
        """关闭后 _executor 被清空，且原线程池已 shutdown，无法再提交任务"""
        # 触发创建线程池
        old_executor = BERTVectorizationService._get_executor()
        assert BERTVectorizationService._executor is old_executor

        BERTVectorizationService.shutdown_executor()

        assert BERTVectorizationService._executor is None
        # 已关闭的 executor 不能再提交新任务
        with pytest.raises(RuntimeError, match="cannot schedule new futures after shutdown"):
            old_executor.submit(lambda: None)

    def test_shutdown_executor_idempotent(self):
        """多次调用 shutdown_executor 不报错，且 _executor 保持为 None"""
        BERTVectorizationService._get_executor()
        BERTVectorizationService.shutdown_executor()
        assert BERTVectorizationService._executor is None

        BERTVectorizationService.shutdown_executor()
        BERTVectorizationService.shutdown_executor()
        assert BERTVectorizationService._executor is None

    def test_get_executor_after_shutdown_creates_new(self):
        """关闭后再次 _get_executor() 会创建新的线程池，保证服务可继续使用"""
        first = BERTVectorizationService._get_executor()
        BERTVectorizationService.shutdown_executor()
        assert BERTVectorizationService._executor is None

        second = BERTVectorizationService._get_executor()
        assert first is not second
        assert BERTVectorizationService._executor is second
        # 新 executor 可正常提交任务
        f = second.submit(lambda: 42)
        assert f.result() == 42
        BERTVectorizationService.shutdown_executor()

    def test_shutdown_executor_when_none_is_no_op(self):
        """未创建过 executor 时调用 shutdown 不报错"""
        BERTVectorizationService.shutdown_executor()
        assert BERTVectorizationService._executor is None
        BERTVectorizationService.shutdown_executor()
        assert BERTVectorizationService._executor is None

    def test_shutdown_executor_clears_even_if_shutdown_raises(self):
        """shutdown 过程异常时仍会清空 _executor，避免泄漏"""
        executor = BERTVectorizationService._get_executor()
        with patch.object(executor, "shutdown", side_effect=RuntimeError("模拟异常")):
            BERTVectorizationService.shutdown_executor()
        assert BERTVectorizationService._executor is None
        # 测试中未真正关闭，此处补关避免线程泄漏
        executor.shutdown(wait=False)


class TestVectorizationUpdateService:
    """向量化更新服务单元测试"""
    
    @pytest.fixture
    def mock_session(self):
        """创建模拟数据库会话"""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        return session
    
    @pytest.fixture
    def update_service(self, mock_session):
        """创建向量化更新服务实例"""
        return VectorizationUpdateService(mock_session)
    
    @pytest.mark.asyncio
    async def test_get_vectorization_service(self, update_service):
        """测试获取向量化服务"""
        with patch('src.services.vectorization_update_service.get_cached_model') as mock_get_cached:
            mock_service = AsyncMock()
            mock_get_cached.return_value = mock_service
            
            result = await update_service._get_vectorization_service()
            
            assert result == mock_service
            mock_get_cached.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_vectorization_service_fallback(self, update_service):
        """测试向量化服务获取失败时的降级处理"""
        with patch('src.services.vectorization_update_service.get_cached_model', side_effect=RuntimeError()):
            with patch('src.services.vectorization_update_service.BERTVectorizationService') as mock_service_class:
                mock_service = AsyncMock()
                mock_service_class.return_value = mock_service
                
                result = await update_service._get_vectorization_service()
                
                assert result == mock_service
                mock_service.load_model.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_vector_to_json(self, update_service):
        """测试向量转JSON功能"""
        # 测试numpy数组
        vector = np.array([1.0, 2.0, 3.0])
        result = update_service._vector_to_json(vector)
        assert result == "[1.0, 2.0, 3.0]"
        
        # 测试列表
        vector_list = [1.0, 2.0, 3.0]
        result = update_service._vector_to_json(vector_list)
        assert result == "[1.0, 2.0, 3.0]"
        
        # 测试元组
        vector_tuple = (1.0, 2.0, 3.0)
        result = update_service._vector_to_json(vector_tuple)
        assert result == "[1.0, 2.0, 3.0]"
    
    @pytest.mark.asyncio
    async def test_should_skip_segment(self, update_service):
        """测试段落跳过逻辑"""
        # 应该跳过的段落
        assert update_service._should_skip_segment("") == True
        assert update_service._should_skip_segment("  ") == True
        assert update_service._should_skip_segment("ab") == True  # 长度小于3
        assert update_service._should_skip_segment("!!!") == True  # 只有标点符号
        assert update_service._should_skip_segment("，。！？") == True  # 只有中文标点
        
        # 不应该跳过的段落
        assert update_service._should_skip_segment("正常文本") == False
        assert update_service._should_skip_segment("Hello World") == False
        assert update_service._should_skip_segment("123456") == False
        assert update_service._should_skip_segment("测试，内容。") == False
    
    @pytest.mark.asyncio
    async def test_is_key_segment(self, update_service):
        """测试关键片段识别"""
        # 关键片段
        assert update_service._is_key_segment("这是重要的内容") == True
        assert update_service._is_key_segment("关键信息") == True
        assert update_service._is_key_segment("核心算法") == True
        assert update_service._is_key_segment("主要结论") == True
        
        # 非关键片段
        assert update_service._is_key_segment("普通文本") == False
        assert update_service._is_key_segment("一般内容") == False
    
    @pytest.mark.asyncio
    async def test_calculate_semantic_density(self, update_service):
        """测试语义密度计算"""
        # 高语义密度（词汇多样）
        high_density = update_service._calculate_semantic_density("机器学习 深度学习 神经网络 算法")
        assert 0.5 <= high_density <= 1.0
        
        # 低语义密度（重复词汇）
        low_density = update_service._calculate_semantic_density("测试 测试 测试 测试")
        assert 0.0 <= low_density <= 0.5
        
        # 空文本
        empty_density = update_service._calculate_semantic_density("")
        assert empty_density == 0.0
    
    @pytest.mark.asyncio
    async def test_calculate_keyword_density(self, update_service):
        """测试关键词密度计算"""
        # 高关键词密度
        high_density = update_service._calculate_keyword_density("技术实现方法系统算法")
        assert high_density > 0.0
        
        # 低关键词密度
        low_density = update_service._calculate_keyword_density("普通文本内容")
        assert low_density == 0.0
        
        # 空文本
        empty_density = update_service._calculate_keyword_density("")
        assert empty_density == 0.0


class TestHierarchicalSearchService:
    """分层搜索服务单元测试"""
    
    @pytest.fixture
    def mock_vectorization_service(self):
        """创建模拟向量化服务"""
        service = AsyncMock()
        service.vectorize_text = AsyncMock(return_value=np.random.rand(384))
        return service
    
    @pytest.fixture
    def mock_session(self):
        """创建模拟数据库会话"""
        session = AsyncMock()
        session.exec = AsyncMock()
        return session
    
    @pytest.fixture
    def search_service(self, mock_vectorization_service, mock_session):
        """创建搜索服务实例"""
        return HierarchicalSearchService(mock_vectorization_service, mock_session)
    
    def test_dynamic_threshold_calculation(self, search_service):
        """测试动态阈值计算"""
        # 短查询应该有更高阈值
        short_threshold = search_service.calculate_dynamic_threshold("AI", "[]")
        long_threshold = search_service.calculate_dynamic_threshold("深度学习神经网络算法原理", "[]")
        
        assert short_threshold > long_threshold
        assert 0.1 <= short_threshold <= 0.9
        assert 0.1 <= long_threshold <= 0.9
        
        # 复杂查询应该有更低阈值
        simple_threshold = search_service.calculate_dynamic_threshold("AI", "[]")
        complex_threshold = search_service.calculate_dynamic_threshold("机器学习 深度学习 神经网络", "[]")
        
        assert complex_threshold < simple_threshold
        
        # 包含数字的查询应该有更高阈值
        normal_threshold = search_service.calculate_dynamic_threshold("机器学习算法", "[]")
        number_threshold = search_service.calculate_dynamic_threshold("机器学习算法123", "[]")
        
        assert number_threshold > normal_threshold
    
    @pytest.mark.asyncio
    async def test_search_error_handling(self, search_service):
        """测试搜索错误处理"""
        # 模拟向量化服务出错
        search_service.vectorization_service.vectorize_text.side_effect = Exception("向量化失败")
        
        result = await search_service.search("测试查询")
        
        assert "items" in result
        assert "total" in result
        assert "error" in result
        assert result["items"] == []
        assert result["total"] == 0
        assert "向量化失败" in result["error"]
    
    def test_vector_conversion(self, search_service):
        """测试向量转换功能"""
        # 测试向量转JSON
        test_vector = np.array([1.0, 2.0, 3.0])
        json_str = search_service._vector_to_json(test_vector)
        assert json_str == "[1.0, 2.0, 3.0]"
        
        # 测试JSON转向量
        converted_vector = search_service._json_to_vector(json_str)
        np.testing.assert_array_equal(converted_vector, test_vector)
        
        # 测试无效JSON
        invalid_vector = search_service._json_to_vector("invalid json")
        assert isinstance(invalid_vector, np.ndarray)
        assert invalid_vector.shape == (384,)
        assert np.allclose(invalid_vector, 0)
    
    def test_result_formatting(self, search_service):
        """测试结果格式化"""
        # 测试文章结果格式化
        from datetime import datetime
        article_item = (1, "测试标题", "测试内容", "测试作者", datetime(2024, 1, 1, 10, 0, 0), 0.95)
        formatted = search_service._format_article_result(article_item)
        
        assert formatted["id"] == 1
        assert formatted["title"] == "测试标题"
        assert formatted["content"] == "测试内容"
        assert formatted["author"] == "测试作者"
        assert formatted["type"] == "article"
        assert formatted["relevance_score"] == 0.95
        
        # 测试评论结果格式化
        comment_item = (2, "评论标题", "评论内容", "评论作者", datetime(2024, 1, 1, 11, 0, 0), 0.85)
        formatted = search_service._format_comment_result(comment_item)
        
        assert formatted["id"] == 2
        assert formatted["title"] == "评论标题"
        assert formatted["content"] == "评论内容"
        assert formatted["author"] == "评论作者"
        assert formatted["type"] == "comment"
        assert formatted["relevance_score"] == 0.85


class TestVectorizationIntegration:
    """向量化集成测试（模拟环境）"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_vectorization(self):
        """测试端到端向量化流程"""
        # 创建模拟服务
        vectorization_service = BERTVectorizationService()
        mock_vector = np.random.rand(384)
        
        with patch.object(vectorization_service, '_vectorize_sync', return_value=mock_vector):
            with patch.object(vectorization_service, 'is_model_loaded', return_value=True):
                # 测试文本向量化
                result = await vectorization_service.vectorize_text("测试文本")
                
                assert isinstance(result, np.ndarray)
                assert result.shape == (384,)
                np.testing.assert_array_equal(result, mock_vector)
                
                # 测试向量转换
                json_str = vectorization_service.vector_to_json(result)
                converted_back = vectorization_service.json_to_vector(json_str)
                np.testing.assert_array_equal(converted_back, result)
    
    @pytest.mark.asyncio
    async def test_error_recovery(self):
        """测试错误恢复机制"""
        vectorization_service = BERTVectorizationService()
        
        # 模拟向量化失败
        with patch.object(vectorization_service, '_vectorize_sync', side_effect=Exception("向量化失败")):
            with patch.object(vectorization_service, 'is_model_loaded', return_value=True):
                result = await vectorization_service.vectorize_text("测试文本")
                
                # 应该返回零向量而不是抛出异常
                assert isinstance(result, np.ndarray)
                assert result.shape == (384,)
                assert np.allclose(result, 0)


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])
