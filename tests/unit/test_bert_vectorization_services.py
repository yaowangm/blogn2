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

from datetime import datetime

from src.services.vectorization_service import BERTVectorizationService
from src.services.vectorization_update_service import VectorizationUpdateService
from src.services.search_service import (
    HierarchicalSearchService,
    DEFAULT_THRESHOLD,
    TITLE_ONLY_MIN_SIMILARITY,
)


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
    async def test_process_long_text_uses_batch_vectorization(self, update_service):
        """长文本片段应批量向量化，避免逐片段调用模型。"""
        segments = [
            {"text": "第一段有效内容", "length": 6, "start_pos": 0, "end_pos": 6},
            {"text": "第二段有效内容", "length": 6, "start_pos": 6, "end_pos": 12},
        ]
        update_service._split_text_with_sliding_window = MagicMock(return_value=segments)

        vectorization_service = AsyncMock()
        vectors = [np.array([1.0, 0.0]), np.array([0.0, 1.0])]
        vectorization_service.vectorize_batch = AsyncMock(return_value=vectors)
        vectorization_service.vectorize_text = AsyncMock()

        result = await update_service._process_long_text(
            "这是一段足够长的文本，用来触发分段处理和批量向量化路径。" * 2,
            vectorization_service,
        )

        assert len(result) == 2
        vectorization_service.vectorize_batch.assert_awaited_once_with([
            "第一段有效内容",
            "第二段有效内容",
        ])
        vectorization_service.vectorize_text.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_save_content_segments_uses_bulk_insert(self, update_service, mock_session):
        """保存片段时应删除一次、批量插入一次。"""
        segments = [
            {
                "index": 0,
                "text": "第一段有效内容",
                "vector": np.array([1.0, 0.0]),
                "length": 6,
                "start_pos": 0,
                "end_pos": 6,
                "confidence_score": 1.0,
                "semantic_density": 0.5,
                "keyword_density": 0.1,
                "is_key_segment": False,
            },
            {
                "index": 1,
                "text": "第二段有效内容",
                "vector": np.array([0.0, 1.0]),
                "length": 6,
                "start_pos": 6,
                "end_pos": 12,
                "confidence_score": 1.0,
                "semantic_density": 0.6,
                "keyword_density": 0.2,
                "is_key_segment": True,
            },
        ]

        await update_service._save_content_segments(123, segments)

        assert mock_session.execute.await_count == 2
        insert_call = mock_session.execute.await_args_list[1]
        rows = insert_call.args[1]
        assert len(rows) == 2
        assert rows[0]["article_vector_id"] == 123
        assert rows[1]["segment_index"] == 1

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
        session.execute = AsyncMock()
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
        """测试搜索错误处理：异常时返回降级结果且使用模块级 logger 记录错误"""
        # 模拟向量化服务出错
        search_service.vectorization_service.vectorize_text.side_effect = Exception("向量化失败")

        with patch("src.services.search_service.logger") as mock_logger:
            result = await search_service.search("测试查询")

        assert "items" in result
        assert "total" in result
        assert "error" in result
        assert result["items"] == []
        assert result["total"] == 0
        assert "向量化失败" in result["error"]
        # 确认使用模块级 logger 记录错误（无 except 内重复 import）
        mock_logger.error.assert_called_once()
        call_msg = mock_logger.error.call_args[0][0]
        assert "搜索服务错误" in call_msg
        assert "向量化失败" in call_msg

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
        article_item = (1, "测试标题", "测试内容", "测试作者", datetime(2024, 1, 1, 10, 0, 0), 0.95)
        formatted = search_service._format_article_result(article_item)

        assert formatted["id"] == 1
        assert formatted["title"] == "测试标题"
        assert formatted["content"] == "测试内容"
        assert formatted["author"] == "测试作者"
        assert formatted["type"] == "article"
        assert formatted["relevance_score"] == 0.95

        # 测试评论结果格式化（元组索引 6 为所属博文 projectitem_id）
        comment_item = (2, "评论标题", "评论内容", "评论作者", datetime(2024, 1, 1, 11, 0, 0), 0.85, 42)
        formatted = search_service._format_comment_result(comment_item)

        assert formatted["id"] == 2
        assert formatted["title"] == "评论标题"
        assert formatted["content"] == "评论内容"
        assert formatted["author"] == "评论作者"
        assert formatted["type"] == "comment"
        assert formatted["relevance_score"] == 0.85
        assert formatted["projectitem_id"] == 42
        assert formatted["article_id"] == 42

        # 旧版 SQL 仅 6 列时：无 projectitem_id，字段应为 None（兼容）
        legacy = (3, "旧", "内", "作", datetime(2024, 1, 2, 12, 0, 0), 0.5)
        leg_fmt = search_service._format_comment_result(legacy)
        assert leg_fmt["id"] == 3
        assert leg_fmt["type"] == "comment"
        assert leg_fmt.get("projectitem_id") is None
        assert leg_fmt.get("article_id") is None

        # 留言本等非博文评论：projectitem_id 可为 0，仍应原样返回
        guest = (9, "留", "言", "访", datetime(2024, 1, 3, 8, 0, 0), 0.4, 0)
        gf = search_service._format_comment_result(guest)
        assert gf["projectitem_id"] == 0
        assert gf["article_id"] == 0

    def test_row_relevance_extraction(self, search_service):
        """测试从查询行中正确解析 relevance_score（列名/索引/字典）"""
        # 元组/列表：按索引 5 取值
        row_tuple = (1, "t", "c", "a", None, 0.72, None, None)
        assert HierarchicalSearchService._row_relevance(row_tuple, index=5) == 0.72
        assert HierarchicalSearchService._row_relevance((1, 2, 3), index=5, default=0.5) == 0.5
        # 带 _mapping 的 Row 模拟
        row_mapping = MagicMock()
        row_mapping._mapping = {"relevance_score": 0.88}
        assert HierarchicalSearchService._row_relevance(row_mapping) == 0.88
        # 字典式（keys + []）
        row_dict = {"relevance_score": 0.6}
        assert HierarchicalSearchService._row_relevance(row_dict) == 0.6

    def test_clamp_items_relevance(self, search_service):
        """仅当 relevance_score 为 0 或缺失时设为阈值，有真实分数则保留"""
        threshold = 0.5
        items = [
            {"id": 1, "relevance_score": 0.3},
            {"id": 2, "relevance_score": 0.8},
            {"id": 3, "relevance_score": 0.0},
            {"id": 4},  # 无 relevance_score
        ]
        HierarchicalSearchService._clamp_items_relevance(items, threshold)
        assert items[0]["relevance_score"] == 0.3  # 保留真实分数
        assert items[1]["relevance_score"] == 0.8
        assert items[2]["relevance_score"] == 0.5  # 0 时用阈值兜底
        assert items[3]["relevance_score"] == 0.5  # 缺失时补阈值
        # 阈值为 0 时不修改
        items2 = [{"id": 1, "relevance_score": 0.2}]
        HierarchicalSearchService._clamp_items_relevance(items2, 0.0)
        assert items2[0]["relevance_score"] == 0.2

    def test_constants(self):
        """搜索阈值常量：默认 55%，无正文最低 85%"""
        assert DEFAULT_THRESHOLD == 0.55
        assert TITLE_ONLY_MIN_SIMILARITY == 0.85

    def test_classify_query(self, search_service):
        """查询分类：短中文实体/长查询/普通关键词"""
        assert search_service._classify_query("爱因斯坦") == "simple_entity"
        assert search_service._classify_query("周树人") == "simple_entity"
        assert search_service._classify_query("machine learning") == "keyword_phrase"
        assert search_service._classify_query("这是一段明显超过二十个字符的长查询用于单元测试覆盖逻辑") == "long_query"

    @pytest.mark.asyncio
    async def test_search_articles_dual_channel_merge_and_pagination(self, search_service):
        """articles：关键词+语义双通道合并，按 page/limit 切片返回不同页内容"""
        # 向量有效，走双通道
        search_service.vectorization_service.vectorize_text = AsyncMock(return_value=np.ones(384))

        # 关键词候选（5*limit），语义候选（5*limit），二者部分重叠
        search_service._keyword_search_articles = AsyncMock(
            return_value={
                "items": [
                    {"id": 1, "title": "爱因斯坦", "content": "包含爱因斯坦", "author": "A", "relevance_score": 1.0, "type": "article"},
                    {"id": 2, "title": "T2", "content": "包含爱因斯坦", "author": "B", "relevance_score": 1.0, "type": "article"},
                    {"id": 3, "title": "T3", "content": "包含爱因斯坦", "author": "C", "relevance_score": 1.0, "type": "article"},
                    {"id": 4, "title": "T4", "content": "包含爱因斯坦", "author": "D", "relevance_score": 1.0, "type": "article"},
                ],
                "total": 4,
                "has_more": False,
                "dynamic_threshold": DEFAULT_THRESHOLD,
            }
        )
        search_service.hybrid_search_articles = AsyncMock(
            return_value={
                "items": [
                    {"id": 3, "title": "T3", "content": "包含爱因斯坦", "author": "C", "relevance_score": 0.9, "type": "article"},
                    {"id": 5, "title": "T5", "content": "包含爱因斯坦", "author": "E", "relevance_score": 0.8, "type": "article"},
                ],
                "total": 2,
                "has_more": False,
                "dynamic_threshold": DEFAULT_THRESHOLD,
            }
        )

        page1 = await search_service.search(query="爱因斯坦", search_type="articles", page=1, limit=2)
        page2 = await search_service.search(query="爱因斯坦", search_type="articles", page=2, limit=2)

        assert [x["id"] for x in page1["items"]] != [x["id"] for x in page2["items"]]
        assert len(page1["items"]) <= 2 and len(page2["items"]) <= 2
        assert page1["total"] >= 4  # 合并后至少 4 条

    @pytest.mark.asyncio
    async def test_search_articles_vector_invalid_uses_keyword_only(self, search_service):
        """向量无效时：articles 只走关键词通道，不调用语义通道"""
        search_service.vectorization_service.vectorize_text = AsyncMock(return_value=np.zeros(384))
        search_service._keyword_search_articles = AsyncMock(
            return_value={"items": [{"id": 1, "title": "爱因斯坦", "content": "xx", "author": "a", "relevance_score": 1.0, "type": "article"}],
                          "total": 1, "has_more": False, "dynamic_threshold": DEFAULT_THRESHOLD}
        )
        search_service.hybrid_search_articles = AsyncMock(return_value={"items": [], "total": 0, "has_more": False, "dynamic_threshold": DEFAULT_THRESHOLD})

        out = await search_service.search(query="爱因斯坦", search_type="articles", page=1, limit=10)
        assert out["total"] >= 1
        search_service.hybrid_search_articles.assert_not_called()

    @pytest.mark.asyncio
    async def test_search_all_pagination_changes_page(self, search_service):
        """all：合并文章+评论候选后分页切片，不同页应返回不同 items"""
        search_service.vectorization_service.vectorize_text = AsyncMock(return_value=np.ones(384))

        # 文章候选：6 条
        search_service._keyword_search_articles = AsyncMock(
            return_value={
                "items": [{"id": i, "title": f"A{i}", "content": "包含爱因斯坦", "author": "u", "relevance_score": 1.0, "type": "article"} for i in range(1, 7)],
                "total": 6,
                "has_more": False,
                "dynamic_threshold": DEFAULT_THRESHOLD,
            }
        )
        search_service.hybrid_search_articles = AsyncMock(return_value={"items": [], "total": 0, "has_more": False, "dynamic_threshold": DEFAULT_THRESHOLD})

        # 评论候选：4 条
        search_service._search_comments = AsyncMock(
            return_value={
                "items": [{"id": 100 + i, "title": f"C{i}", "content": "包含爱因斯坦", "author": "u", "relevance_score": 0.6, "type": "comment"} for i in range(1, 5)],
                "total": 4,
                "has_more": False,
            }
        )

        p1 = await search_service.search(query="爱因斯坦", search_type="all", page=1, limit=5)
        p2 = await search_service.search(query="爱因斯坦", search_type="all", page=2, limit=5)
        assert [x["id"] for x in p1["items"]] != [x["id"] for x in p2["items"]]
        assert p1["total"] >= 10

    def test_merge_keyword_skips_no_content(self):
        """关键词合并：无正文的条目不并入，避免仅作者匹配的无内容条目标题无关却排前面"""
        vector_items = [
            {"id": 1, "title": "A", "content": "有内容", "relevance_score": 0.9},
        ]
        keyword_items = [
            {"id": 2, "title": "上头像", "content": None, "relevance_score": 0},   # 无正文，不并入
            {"id": 3, "title": "邱华栋", "content": "", "relevance_score": 0},      # 空正文，不并入
            {"id": 4, "title": "某文", "content": "   ", "relevance_score": 0},    # 仅空白，不并入
        ]
        merged = HierarchicalSearchService._merge_keyword_into_article_items(
            vector_items, keyword_items, limit=10
        )
        ids = [x["id"] for x in merged]
        assert 2 not in ids
        assert 3 not in ids
        assert 4 not in ids
        assert 1 in ids

    def test_merge_keyword_keeps_items_with_content(self):
        """关键词合并：有正文的关键词条并入并参与排序，取前 limit 条"""
        vector_items = [
            {"id": 1, "title": "V1", "content": "正文1", "relevance_score": 0.7},
        ]
        keyword_items = [
            {"id": 2, "title": "邱华栋大骂王朔", "content": "长正文", "relevance_score": 0},
            {"id": 3, "title": "另一篇", "content": "有", "relevance_score": 0},
        ]
        merged = HierarchicalSearchService._merge_keyword_into_article_items(
            vector_items, keyword_items, limit=10
        )
        assert len(merged) == 3
        ids = [x["id"] for x in merged]
        assert 2 in ids and 3 in ids
        # 关键词并入项应被赋予 0.95
        for x in merged:
            if x["id"] in (2, 3):
                assert x["relevance_score"] == 0.95
        # 按 relevance 降序，0.95 在前
        assert merged[0]["relevance_score"] == 0.95

    def test_merge_keyword_respects_limit_and_dedup(self):
        """关键词合并：去重（已在向量结果中的不重复添加），且最多返回 limit 条"""
        vector_items = [
            {"id": 1, "title": "A", "content": "x", "relevance_score": 0.9},
            {"id": 2, "title": "B", "content": "x", "relevance_score": 0.8},
        ]
        keyword_items = [
            {"id": 2, "title": "B", "content": "x", "relevance_score": 0},  # 已存在，不重复
            {"id": 3, "title": "C", "content": "x", "relevance_score": 0},
        ]
        merged = HierarchicalSearchService._merge_keyword_into_article_items(
            vector_items, keyword_items, limit=3
        )
        assert len(merged) == 3
        assert merged[0]["id"] == 3 and merged[0]["relevance_score"] == 0.95
        assert merged[1]["id"] == 1
        assert merged[2]["id"] == 2

    @pytest.mark.asyncio
    async def test_hybrid_search_filters_low_relevance_no_content(self, search_service):
        """混合搜索：无正文且相似度 < TITLE_ONLY_MIN 的条目被过滤，不进入结果"""
        # 模拟一批行：有“无正文+低分”的 1022、有正文的 724、无正文但高分的 999
        dt = datetime(2007, 2, 2, 22, 35, 10)
        rows_batch1 = [
            (724, "邱华栋大骂王朔", "长正文内容", "左轻侯", dt, 0.95, "片段", "content"),
            (1022, "上头像", None, "在北之北", dt, 0.6, "上头像", "title"),   # 无正文+低分，应被过滤
            (999, "邱华栋", "", "某作者", dt, 0.9, "邱华栋", "title"),        # 无正文但>=0.85，保留
        ]
        mock_result = MagicMock()
        mock_result.fetchall.return_value = rows_batch1
        empty_result = MagicMock()
        empty_result.fetchall.return_value = []

        search_service.session.exec = AsyncMock(side_effect=[mock_result, empty_result])

        out = await search_service.hybrid_search_articles(
            "[0.1,0.2]", "relevance", page=1, limit=10, query="邱华栋"
        )
        ids = [x["id"] for x in out["items"]]
        assert 1022 not in ids
        assert 724 in ids
        assert 999 in ids
        assert out["total"] == 2

    @pytest.mark.asyncio
    async def test_hybrid_search_page_size_and_total(self, search_service):
        """混合搜索：每页条数不超过 limit，total 为实际有效条数"""
        dt = datetime(2007, 2, 2, 22, 35, 10)
        # 第一批：5 条，其中 3 条有效（有正文或 relevance>=0.85）
        rows1 = [
            (1, "T1", "有", "A", dt, 0.9, "x", "content"),
            (2, "T2", None, "A", dt, 0.5, "x", "title"),   # 无正文且<0.85，过滤
            (3, "T3", "有", "A", dt, 0.88, "x", "content"),
            (4, "T4", None, "A", dt, 0.9, "x", "title"),   # 无正文但>=0.85，保留
            (5, "T5", "", "A", dt, 0.6, "x", "title"),    # 无正文且<0.85，过滤
        ]
        mock1 = MagicMock()
        mock1.fetchall.return_value = rows1
        mock_empty = MagicMock()
        mock_empty.fetchall.return_value = []

        search_service.session.exec = AsyncMock(side_effect=[mock1, mock_empty])

        out = await search_service.hybrid_search_articles(
            "[0.1,0.2]", "relevance", page=1, limit=10, query="q"
        )
        assert len(out["items"]) <= 10
        assert out["total"] == 3  # 仅 1,3,4 有效
        assert out["has_more"] is False
        ids = [x["id"] for x in out["items"]]
        assert 2 not in ids and 5 not in ids

    @pytest.mark.asyncio
    async def test_hybrid_search_pagination_second_page(self, search_service):
        """混合搜索：第二页返回有效条目的 (limit, 2*limit) 段，total 为实际有效条数"""
        dt = datetime(2007, 2, 2, 22, 35, 10)
        # 单批返回 4 条有效（有正文），然后无更多数据；batch_size=50 故一批即结束
        rows = [
            (1, "T1", "有", "A", dt, 0.9, "x", "content"),
            (2, "T2", "有", "A", dt, 0.88, "x", "content"),
            (3, "T3", "有", "A", dt, 0.85, "x", "content"),
            (4, "T4", "有", "A", dt, 0.82, "x", "content"),
        ]
        mock_batch = MagicMock()
        mock_batch.fetchall.return_value = rows
        mock_empty = MagicMock()
        mock_empty.fetchall.return_value = []

        search_service.session.exec = AsyncMock(side_effect=[mock_batch, mock_empty])

        page1 = await search_service.hybrid_search_articles(
            "[0.1,0.2]", "relevance", page=1, limit=2, query="q"
        )
        assert len(page1["items"]) == 2
        assert page1["total"] == 4
        assert page1["has_more"] is True

        search_service.session.exec = AsyncMock(side_effect=[mock_batch, mock_empty])
        page2 = await search_service.hybrid_search_articles(
            "[0.1,0.2]", "relevance", page=2, limit=2, query="q"
        )
        assert len(page2["items"]) == 2
        assert page2["total"] == 4
        assert page2["has_more"] is False

    @pytest.mark.asyncio
    async def test_search_queries_use_bound_params(self, search_service):
        """搜索 SQL 应通过参数绑定传递动态值，而不是字符串拼接。"""
        article_rows = MagicMock()
        article_rows.fetchall.return_value = []
        article_count = MagicMock()
        article_count.fetchone.return_value = (0,)

        search_service.session.exec = AsyncMock(side_effect=[article_rows, article_count])
        await search_service._search_articles("[0.1,0.2]", "relevance", page=2, limit=7, query="测试")

        article_call = search_service.session.exec.call_args_list[0]
        article_count_call = search_service.session.exec.call_args_list[1]
        assert "query_vector_json" in article_call.kwargs["params"]
        assert article_call.kwargs["params"]["limit"] == 7
        assert article_call.kwargs["params"]["offset"] == 7
        assert article_call.kwargs["params"]["adjusted_threshold"] >= 0.1
        assert article_count_call.kwargs["params"]["min_segment_length"] >= 3
        assert "[0.1,0.2]" not in str(article_call.args[0])

        search_service.session.exec.reset_mock()

        comment_rows = MagicMock()
        comment_rows.fetchall.return_value = []
        comment_count = MagicMock()
        comment_count.fetchone.return_value = (0,)

        search_service.session.exec = AsyncMock(side_effect=[comment_rows, comment_count])
        await search_service._search_comments("[0.1,0.2]", "relevance", page=3, limit=5, query="测试")

        comment_call = search_service.session.exec.call_args_list[0]
        assert comment_call.kwargs["params"]["query_vector_json"] == "[0.1,0.2]"
        assert comment_call.kwargs["params"]["limit"] == 5
        assert comment_call.kwargs["params"]["offset"] == 10
        assert "[0.1,0.2]" not in str(comment_call.args[0])

        search_service.session.exec.reset_mock()

        hybrid_rows = MagicMock()
        hybrid_rows.fetchall.return_value = [
            (1, "标题", "正文", "作者", datetime(2024, 1, 1, 10, 0, 0), 0.9, "正文", "content"),
        ]
        hybrid_empty = MagicMock()
        hybrid_empty.fetchall.return_value = []

        search_service.session.exec = AsyncMock(side_effect=[hybrid_rows, hybrid_empty])
        await search_service.hybrid_search_articles("[0.1,0.2]", "relevance", page=1, limit=4, query="测试")

        hybrid_call = search_service.session.exec.call_args_list[0]
        assert hybrid_call.kwargs["params"]["query_vector_json"] == "[0.1,0.2]"
        assert hybrid_call.kwargs["params"]["batch_limit"] >= 50
        assert hybrid_call.kwargs["params"]["batch_offset"] == 0
        assert hybrid_call.kwargs["params"]["title_only_min_similarity"] == TITLE_ONLY_MIN_SIMILARITY
        assert "[0.1,0.2]" not in str(hybrid_call.args[0])


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
