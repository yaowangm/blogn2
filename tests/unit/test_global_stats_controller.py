"""
全局统计控制器单元测试

测试全局统计API端点的功能
"""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException
from src.controllers.global_stats import (
    get_global_stats,
    sync_global_stats
)
from src.models.glovar import Glovar


class TestGlobalStatsController:
    """全局统计控制器测试类"""

    @pytest.fixture
    def mock_session(self):
        """模拟数据库会话"""
        return AsyncMock()

    @pytest.fixture
    def sample_stats_data(self):
        """示例统计数据"""
        return {
            "usercount": 100,
            "projectcount": 50,
            "projectitemcount": 200
        }

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_global_stats_success(self, mock_session, sample_stats_data):
        """测试成功获取全局统计"""
        # 准备测试数据
        with patch('src.controllers.global_stats.GlobalStatsService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.get_all_stats.return_value = sample_stats_data
            mock_service_class.return_value = mock_service
            
            # 执行测试
            result = await get_global_stats(session=mock_session)
            
            # 验证结果
            expected = {
                "usercount": 100,
                "projectcount": 50,
                "projectitemcount": 200
            }
            assert result == expected
            mock_service_class.assert_called_once_with(mock_session)
            mock_service.get_all_stats.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_global_stats_empty(self, mock_session):
        """测试获取空统计数据"""
        # 准备测试数据
        with patch('src.controllers.global_stats.GlobalStatsService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.get_all_stats.return_value = {}
            mock_service_class.return_value = mock_service
            
            # 执行测试
            result = await get_global_stats(session=mock_session)
            
            # 验证结果
            expected = {
                "usercount": 0,
                "projectcount": 0,
                "projectitemcount": 0
            }
            assert result == expected
            mock_service_class.assert_called_once_with(mock_session)
            mock_service.get_all_stats.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_global_stats_partial_data(self, mock_session):
        """测试获取部分统计数据"""
        # 准备测试数据
        partial_data = {"usercount": 100}  # 只有用户数
        with patch('src.controllers.global_stats.GlobalStatsService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.get_all_stats.return_value = partial_data
            mock_service_class.return_value = mock_service
            
            # 执行测试
            result = await get_global_stats(session=mock_session)
            
            # 验证结果
            expected = {
                "usercount": 100,
                "projectcount": 0,
                "projectitemcount": 0
            }
            assert result == expected
            mock_service_class.assert_called_once_with(mock_session)
            mock_service.get_all_stats.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_global_stats_service_error(self, mock_session):
        """测试获取全局统计时服务错误"""
        # 准备测试数据
        with patch('src.controllers.global_stats.GlobalStatsService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.get_all_stats.side_effect = Exception("数据库连接错误")
            mock_service_class.return_value = mock_service
            
            # 执行测试并验证异常
            with pytest.raises(HTTPException) as exc_info:
                await get_global_stats(session=mock_session)
            
            # 验证异常信息
            assert exc_info.value.status_code == 500
            assert "数据库连接错误" in exc_info.value.detail
            mock_service_class.assert_called_once_with(mock_session)
            mock_service.get_all_stats.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sync_global_stats_success(self, mock_session):
        """测试成功同步全局统计"""
        # 准备测试数据
        with patch('src.controllers.global_stats.GlobalStatsService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.sync_stats_from_database.return_value = True
            mock_service_class.return_value = mock_service
            
            # 执行测试 - 提供current_user参数
            result = await sync_global_stats(
                session=mock_session,
                current_user={"id": 1, "state": 10}  # 管理员用户
            )
            
            # 验证结果
            expected = {"message": "全局统计同步成功", "stats": mock_service.get_all_stats.return_value}
            assert result == expected
            mock_service_class.assert_called_once_with(mock_session)
            mock_service.sync_stats_from_database.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sync_global_stats_failure(self, mock_session):
        """测试同步全局统计失败"""
        # 准备测试数据
        with patch('src.controllers.global_stats.GlobalStatsService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.sync_stats_from_database.return_value = False
            mock_service_class.return_value = mock_service
            
            # 执行测试并验证异常
            with pytest.raises(HTTPException) as exc_info:
                await sync_global_stats(
                    session=mock_session,
                    current_user={"id": 1, "state": 10}  # 管理员用户
                )
            
            # 验证异常信息
            assert exc_info.value.status_code == 500
            assert "同步全局统计失败" in exc_info.value.detail
            mock_service_class.assert_called_once_with(mock_session)
            mock_service.sync_stats_from_database.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sync_global_stats_service_error(self, mock_session):
        """测试同步全局统计时服务错误"""
        # 准备测试数据
        with patch('src.controllers.global_stats.GlobalStatsService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.sync_stats_from_database.side_effect = Exception("数据库错误")
            mock_service_class.return_value = mock_service
            
            # 执行测试并验证异常
            with pytest.raises(HTTPException) as exc_info:
                await sync_global_stats(
                    session=mock_session,
                    current_user={"id": 1, "state": 10}  # 管理员用户
                )
            
            # 验证异常信息
            assert exc_info.value.status_code == 500
            assert "数据库错误" in exc_info.value.detail
            mock_service_class.assert_called_once_with(mock_session)
            mock_service.sync_stats_from_database.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_global_stats_with_none_values(self, mock_session):
        """测试获取包含None值的统计数据"""
        # 准备测试数据
        data_with_none = {
            "usercount": 100,
            "projectcount": None,  # None值
            "projectitemcount": 200
        }
        with patch('src.controllers.global_stats.GlobalStatsService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.get_all_stats.return_value = data_with_none
            mock_service_class.return_value = mock_service
            
            # 执行测试
            result = await get_global_stats(session=mock_session)
            
            # 验证结果 - 控制器会使用get方法，None值保持为None
            expected = {
                "usercount": 100,
                "projectcount": None,  # None值保持为None
                "projectitemcount": 200
            }
            assert result == expected
            mock_service_class.assert_called_once_with(mock_session)
            mock_service.get_all_stats.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_global_stats_with_negative_values(self, mock_session):
        """测试获取包含负值的统计数据"""
        # 准备测试数据
        data_with_negative = {
            "usercount": 100,
            "projectcount": -5,  # 负值
            "projectitemcount": 200
        }
        with patch('src.controllers.global_stats.GlobalStatsService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.get_all_stats.return_value = data_with_negative
            mock_service_class.return_value = mock_service
            
            # 执行测试
            result = await get_global_stats(session=mock_session)
            
            # 验证结果 - 负值应该保持原样
            expected = {
                "usercount": 100,
                "projectcount": -5,
                "projectitemcount": 200
            }
            assert result == expected
            mock_service_class.assert_called_once_with(mock_session)
            mock_service.get_all_stats.assert_called_once()
