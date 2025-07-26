"""
用户控制器单元测试
"""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException
from src.controllers.user import (
    get_user_summary,
    get_new_users,
    get_user_count,
    get_user_by_id
)
from src.services.user_service import UserService
from src.database import User


class TestUserController:
    """用户控制器测试类"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_user_summary_success(self, mock_async_session):
        """测试获取用户摘要成功"""
        # 准备测试数据
        expected_summary = {
            "total_users": 10,
            "recent_users": [
                {"id": 1, "username": "user1"},
                {"id": 2, "username": "user2"}
            ]
        }
        
        # 模拟服务方法
        mock_service = AsyncMock(spec=UserService)
        mock_service.get_user_summary.return_value = expected_summary
        
        # 执行测试
        result = await get_user_summary(user_service=mock_service)
        
        # 验证结果
        assert result == expected_summary
        mock_service.get_user_summary.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_new_users_success(self, mock_async_session):
        """测试获取最新用户成功"""
        # 准备测试数据
        expected_users = [
            User(id=1, name="user1", email="user1@example.com"),
            User(id=2, name="user2", email="user2@example.com")
        ]
        
        # 模拟服务方法
        mock_service = AsyncMock(spec=UserService)
        mock_service.get_top_users.return_value = expected_users
        
        # 执行测试
        result = await get_new_users(user_service=mock_service)
        
        # 验证结果
        assert result == expected_users
        mock_service.get_top_users.assert_called_once_with(3)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_user_count_success(self, mock_async_session):
        """测试获取用户总数成功"""
        # 准备测试数据
        expected_count = 15
        
        # 模拟服务方法
        mock_service = AsyncMock(spec=UserService)
        mock_service.get_user_count.return_value = expected_count
        
        # 执行测试
        result = await get_user_count(user_service=mock_service)
        
        # 验证结果
        assert result == {"count": expected_count}
        mock_service.get_user_count.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_user_by_id_success(self, mock_async_session):
        """测试根据ID获取用户成功"""
        # 准备测试数据
        expected_user = User(
            id=1,
            name="testuser",
            email="test@example.com"
        )
        
        # 模拟服务方法
        mock_service = AsyncMock(spec=UserService)
        mock_service.get_user_by_id.return_value = expected_user
        
        # 执行测试
        result = await get_user_by_id(user_id=1, user_service=mock_service)
        
        # 验证结果
        assert result == expected_user
        mock_service.get_user_by_id.assert_called_once_with(1)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, mock_async_session):
        """测试根据ID获取用户失败 - 用户不存在"""
        # 模拟服务方法返回None
        mock_service = AsyncMock(spec=UserService)
        mock_service.get_user_by_id.return_value = None
        
        # 执行测试并验证异常
        with pytest.raises(HTTPException) as exc_info:
            await get_user_by_id(user_id=999, user_service=mock_service)
        
        # 验证异常信息
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "用户不存在"
        mock_service.get_user_by_id.assert_called_once_with(999)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_user_summary_service_error(self, mock_async_session):
        """测试获取用户摘要服务错误"""
        # 模拟服务方法抛出异常
        mock_service = AsyncMock(spec=UserService)
        mock_service.get_user_summary.side_effect = Exception("数据库连接错误")
        
        # 执行测试并验证异常
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await get_user_summary(user_service=mock_service)
        
        # 验证异常信息
        assert exc_info.value.status_code == 500
        assert "数据库连接错误" in exc_info.value.detail 