"""
用户管理功能测试
测试用户列表获取、分页、搜索等管理功能
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException, status
from typing import Dict, Any, List

from src.controllers.user import get_users_list
from src.services.user_service import UserService
from src.models.user import User
from datetime import datetime


class TestUserManagement:
    """用户管理功能测试类"""
    
    @pytest.fixture
    def mock_user_service(self):
        """创建模拟用户服务"""
        service = AsyncMock(spec=UserService)
        return service
    
    @pytest.fixture
    def admin_user(self):
        """创建管理员用户"""
        return {
            "id": 1,
            "name": "admin",
            "state": 10,
            "role": "admin"
        }
    
    @pytest.fixture
    def regular_user(self):
        """创建普通用户"""
        return {
            "id": 2,
            "name": "user",
            "state": 1,
            "role": "user"
        }
    
    @pytest.fixture
    def mock_users_data(self):
        """创建模拟用户数据"""
        users = []
        for i in range(1, 6):
            user = User()
            user.id = i
            user.name = f"user{i}"
            user.state = 1 if i > 1 else 10  # 第一个是管理员
            user.regtime = datetime.now()
            user.point = i * 10
            user.projectid = i
            user.email = f"user{i}@example.com"
            users.append(user)
        return users

    @pytest.mark.asyncio
    async def test_get_users_list_success_admin(self, mock_user_service, admin_user, mock_users_data):
        """测试管理员获取用户列表成功"""
        # 设置模拟返回值
        mock_user_service.get_users_paginated.return_value = {
            "users": [
                {
                    "id": 1,
                    "name": "user1",
                    "state": 10,
                    "regtime": "2024-01-01T00:00:00",
                    "point": 10,
                    "projectid": 1,
                    "email": "user1@example.com"
                },
                {
                    "id": 2,
                    "name": "user2",
                    "state": 1,
                    "regtime": "2024-01-02T00:00:00",
                    "point": 20,
                    "projectid": 2,
                    "email": "user2@example.com"
                }
            ],
            "pagination": {
                "current_page": 1,
                "page_size": 20,
                "total_count": 2,
                "total_pages": 1,
                "has_next": False,
                "has_prev": False
            }
        }
        
        # 测试获取用户列表
        result = await get_users_list(
            page=1,
            page_size=20,
            search=None,
            user_service=mock_user_service,
            current_user=admin_user
        )
        
        # 验证结果
        assert "users" in result
        assert "pagination" in result
        assert len(result["users"]) == 2
        assert result["pagination"]["current_page"] == 1
        assert result["pagination"]["total_count"] == 2
        
        # 验证服务调用
        mock_user_service.get_users_paginated.assert_called_once_with(1, 20, None)

    @pytest.mark.asyncio
    async def test_get_users_list_with_search(self, mock_user_service, admin_user):
        """测试带搜索条件的用户列表获取"""
        # 设置模拟返回值
        mock_user_service.get_users_paginated.return_value = {
            "users": [
                {
                    "id": 1,
                    "name": "testuser",
                    "state": 1,
                    "regtime": "2024-01-01T00:00:00",
                    "point": 10,
                    "projectid": 1,
                    "email": "testuser@example.com"
                }
            ],
            "pagination": {
                "current_page": 1,
                "page_size": 20,
                "total_count": 1,
                "total_pages": 1,
                "has_next": False,
                "has_prev": False
            }
        }
        
        # 测试带搜索的获取用户列表
        result = await get_users_list(
            page=1,
            page_size=20,
            search="test",
            user_service=mock_user_service,
            current_user=admin_user
        )
        
        # 验证结果
        assert len(result["users"]) == 1
        assert result["users"][0]["name"] == "testuser"
        
        # 验证服务调用
        mock_user_service.get_users_paginated.assert_called_once_with(1, 20, "test")

    @pytest.mark.asyncio
    async def test_get_users_list_pagination(self, mock_user_service, admin_user):
        """测试分页功能"""
        # 设置模拟返回值
        mock_user_service.get_users_paginated.return_value = {
            "users": [],
            "pagination": {
                "current_page": 2,
                "page_size": 10,
                "total_count": 25,
                "total_pages": 3,
                "has_next": True,
                "has_prev": True
            }
        }
        
        # 测试分页
        result = await get_users_list(
            page=2,
            page_size=10,
            search=None,
            user_service=mock_user_service,
            current_user=admin_user
        )
        
        # 验证结果
        assert result["pagination"]["current_page"] == 2
        assert result["pagination"]["page_size"] == 10
        assert result["pagination"]["total_count"] == 25
        assert result["pagination"]["total_pages"] == 3
        assert result["pagination"]["has_next"] is True
        assert result["pagination"]["has_prev"] is True
        
        # 验证服务调用
        mock_user_service.get_users_paginated.assert_called_once_with(2, 10, None)

    @pytest.mark.asyncio
    async def test_get_users_list_parameter_validation(self, mock_user_service, admin_user):
        """测试参数验证和规范化"""
        # 设置模拟返回值
        mock_user_service.get_users_paginated.return_value = {
            "users": [],
            "pagination": {
                "current_page": 1,
                "page_size": 20,
                "total_count": 0,
                "total_pages": 0,
                "has_next": False,
                "has_prev": False
            }
        }
        
        # 测试无效参数被规范化
        result = await get_users_list(
            page=0,  # 无效页码，应该被规范化为1
            page_size=150,  # 超过最大限制，应该被规范化为100
            search=None,
            user_service=mock_user_service,
            current_user=admin_user
        )
        
        # 验证服务调用时参数被正确规范化
        mock_user_service.get_users_paginated.assert_called_once_with(1, 100, None)

    @pytest.mark.asyncio
    async def test_get_users_list_not_logged_in(self, mock_user_service):
        """测试未登录用户访问用户列表"""
        # 测试未登录用户
        with pytest.raises(HTTPException) as exc_info:
            await get_users_list(
                page=1,
                page_size=20,
                search=None,
                user_service=mock_user_service,
                current_user=None
            )
        
        assert exc_info.value.status_code == 401
        assert "需要登录才能访问" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_users_list_regular_user(self, mock_user_service, regular_user):
        """测试普通用户访问用户列表"""
        # 测试普通用户（非管理员）
        with pytest.raises(HTTPException) as exc_info:
            await get_users_list(
                page=1,
                page_size=20,
                search=None,
                user_service=mock_user_service,
                current_user=regular_user
            )
        
        assert exc_info.value.status_code == 403
        assert "需要管理员权限" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_users_list_empty_result(self, mock_user_service, admin_user):
        """测试空结果"""
        # 设置模拟返回值
        mock_user_service.get_users_paginated.return_value = {
            "users": [],
            "pagination": {
                "current_page": 1,
                "page_size": 20,
                "total_count": 0,
                "total_pages": 0,
                "has_next": False,
                "has_prev": False
            }
        }
        
        # 测试空结果
        result = await get_users_list(
            page=1,
            page_size=20,
            search="nonexistent",
            user_service=mock_user_service,
            current_user=admin_user
        )
        
        # 验证结果
        assert len(result["users"]) == 0
        assert result["pagination"]["total_count"] == 0
        
        # 验证服务调用
        mock_user_service.get_users_paginated.assert_called_once_with(1, 20, "nonexistent")

    @pytest.mark.asyncio
    async def test_get_users_list_large_page_size(self, mock_user_service, admin_user):
        """测试大页面大小限制"""
        # 设置模拟返回值
        mock_user_service.get_users_paginated.return_value = {
            "users": [],
            "pagination": {
                "current_page": 1,
                "page_size": 100,
                "total_count": 0,
                "total_pages": 0,
                "has_next": False,
                "has_prev": False
            }
        }
        
        # 测试超过最大限制的页面大小
        result = await get_users_list(
            page=1,
            page_size=200,  # 超过最大限制100
            search=None,
            user_service=mock_user_service,
            current_user=admin_user
        )
        
        # 验证服务调用时页面大小被限制为100
        mock_user_service.get_users_paginated.assert_called_once_with(1, 100, None)

    @pytest.mark.asyncio
    async def test_get_users_list_negative_page(self, mock_user_service, admin_user):
        """测试负数页码处理"""
        # 设置模拟返回值
        mock_user_service.get_users_paginated.return_value = {
            "users": [],
            "pagination": {
                "current_page": 1,
                "page_size": 20,
                "total_count": 0,
                "total_pages": 0,
                "has_next": False,
                "has_prev": False
            }
        }
        
        # 测试负数页码
        result = await get_users_list(
            page=-5,  # 负数页码
            page_size=20,
            search=None,
            user_service=mock_user_service,
            current_user=admin_user
        )
        
        # 验证服务调用时页码被规范化为1
        mock_user_service.get_users_paginated.assert_called_once_with(1, 20, None)

    @pytest.mark.asyncio
    async def test_get_users_list_zero_page_size(self, mock_user_service, admin_user):
        """测试零页面大小处理"""
        # 设置模拟返回值
        mock_user_service.get_users_paginated.return_value = {
            "users": [],
            "pagination": {
                "current_page": 1,
                "page_size": 1,
                "total_count": 0,
                "total_pages": 0,
                "has_next": False,
                "has_prev": False
            }
        }
        
        # 测试零页面大小
        result = await get_users_list(
            page=1,
            page_size=0,  # 零页面大小
            search=None,
            user_service=mock_user_service,
            current_user=admin_user
        )
        
        # 验证服务调用时页面大小被规范化为1
        mock_user_service.get_users_paginated.assert_called_once_with(1, 1, None)

    @pytest.mark.asyncio
    async def test_get_users_list_search_with_whitespace(self, mock_user_service, admin_user):
        """测试搜索条件包含空白字符的处理"""
        # 设置模拟返回值
        mock_user_service.get_users_paginated.return_value = {
            "users": [],
            "pagination": {
                "current_page": 1,
                "page_size": 20,
                "total_count": 0,
                "total_pages": 0,
                "has_next": False,
                "has_prev": False
            }
        }
        
        # 测试包含空白字符的搜索条件
        result = await get_users_list(
            page=1,
            page_size=20,
            search="  test  ",  # 包含前后空格
            user_service=mock_user_service,
            current_user=admin_user
        )
        
        # 验证服务调用
        mock_user_service.get_users_paginated.assert_called_once_with(1, 20, "  test  ")

    @pytest.mark.asyncio
    async def test_get_users_list_service_error(self, mock_user_service, admin_user):
        """测试服务层错误处理"""
        from fastapi import HTTPException
        
        # 设置模拟服务抛出异常
        mock_user_service.get_users_paginated.side_effect = Exception("数据库连接失败")
        
        # 测试服务错误
        with pytest.raises(HTTPException) as exc_info:
            await get_users_list(
                page=1,
                page_size=20,
                search=None,
                user_service=mock_user_service,
                current_user=admin_user
            )
        
        assert exc_info.value.status_code == 500
        assert "获取用户列表失败" in str(exc_info.value.detail)
        assert "数据库连接失败" in str(exc_info.value.detail)
