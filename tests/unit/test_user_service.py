"""
用户服务单元测试
"""

import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime
from src.services.user_service import UserService
from src.repositories.user_repository import UserRepository
from src.database import User


class TestUserService:
    """用户服务测试类"""

    @pytest.fixture
    def mock_user_repo(self):
        """模拟用户仓库"""
        return AsyncMock(spec=UserRepository)

    @pytest.fixture
    def user_service(self, mock_user_repo):
        """创建用户服务实例"""
        return UserService(mock_user_repo)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_user_count_success(self, user_service, mock_user_repo):
        """测试获取用户总数成功"""
        # 准备测试数据
        expected_count = 25
        
        # 模拟仓库方法
        mock_user_repo.count.return_value = expected_count
        
        # 执行测试
        result = await user_service.get_user_count()
        
        # 验证结果
        assert result == expected_count
        mock_user_repo.count.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_user_by_id_success(self, user_service, mock_user_repo):
        """测试根据ID获取用户成功"""
        # 准备测试数据
        expected_user = User(
            id=1,
            name="testuser",
            email="test@example.com",
            regtime=datetime.now()
        )
        
        # 模拟仓库方法
        mock_user_repo.get_by_id.return_value = expected_user
        
        # 执行测试
        result = await user_service.get_user_by_id(1)
        
        # 验证结果
        assert result == expected_user
        assert result.id == 1
        assert result.name == "testuser"
        mock_user_repo.get_by_id.assert_called_once_with(1)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, user_service, mock_user_repo):
        """测试根据ID获取用户失败 - 用户不存在"""
        # 模拟仓库方法返回None
        mock_user_repo.get_by_id.return_value = None
        
        # 执行测试
        result = await user_service.get_user_by_id(999)
        
        # 验证结果
        assert result is None
        mock_user_repo.get_by_id.assert_called_once_with(999)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_user_by_email_success(self, user_service, mock_user_repo):
        """测试根据邮箱获取用户成功"""
        # 准备测试数据
        expected_user = User(
            id=1,
            name="testuser",
            email="test@example.com"
        )
        
        # 模拟仓库方法
        mock_user_repo.get_by_email.return_value = expected_user
        
        # 执行测试
        result = await user_service.get_user_by_email("test@example.com")
        
        # 验证结果
        assert result == expected_user
        assert result.email == "test@example.com"
        mock_user_repo.get_by_email.assert_called_once_with("test@example.com")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_user_by_name_success(self, user_service, mock_user_repo):
        """测试根据用户名获取用户成功"""
        # 准备测试数据
        expected_user = User(
            id=1,
            name="testuser",
            email="test@example.com"
        )
        
        # 模拟仓库方法
        mock_user_repo.get_by_name.return_value = expected_user
        
        # 执行测试
        result = await user_service.get_user_by_name("testuser")
        
        # 验证结果
        assert result == expected_user
        assert result.name == "testuser"
        mock_user_repo.get_by_name.assert_called_once_with("testuser")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_active_users_success(self, user_service, mock_user_repo):
        """测试获取活跃用户成功"""
        # 准备测试数据
        expected_users = [
            User(id=1, name="user1", email="user1@example.com"),
            User(id=2, name="user2", email="user2@example.com")
        ]
        
        # 模拟仓库方法
        mock_user_repo.get_active_users.return_value = expected_users
        
        # 执行测试
        result = await user_service.get_active_users(limit=10)
        
        # 验证结果
        assert result == expected_users
        assert len(result) == 2
        mock_user_repo.get_active_users.assert_called_once_with(10)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_active_users_default_limit(self, user_service, mock_user_repo):
        """测试获取活跃用户使用默认限制"""
        # 准备测试数据
        expected_users = [User(id=1, name="user1")]
        
        # 模拟仓库方法
        mock_user_repo.get_active_users.return_value = expected_users
        
        # 执行测试（不传limit参数）
        result = await user_service.get_active_users()
        
        # 验证结果
        assert result == expected_users
        mock_user_repo.get_active_users.assert_called_once_with(None)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_recent_users_success(self, user_service, mock_user_repo):
        """测试获取最近注册用户成功"""
        # 准备测试数据
        expected_users = [
            User(id=1, name="user1", regtime=datetime.now()),
            User(id=2, name="user2", regtime=datetime.now())
        ]
        
        # 模拟仓库方法
        mock_user_repo.get_recent_users.return_value = expected_users
        
        # 执行测试
        result = await user_service.get_recent_users(limit=10)
        
        # 验证结果
        assert result == expected_users
        assert len(result) == 2
        mock_user_repo.get_recent_users.assert_called_once_with(10)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_top_users_success(self, user_service, mock_user_repo):
        """测试获取前N个用户成功"""
        # 准备测试数据
        expected_users = [
            User(id=1, name="user1"),
            User(id=2, name="user2"),
            User(id=3, name="user3")
        ]
        
        # 模拟仓库方法
        mock_user_repo.get_recent_users.return_value = expected_users
        
        # 执行测试
        result = await user_service.get_top_users(limit=3)
        
        # 验证结果
        assert result == expected_users
        assert len(result) == 3
        mock_user_repo.get_recent_users.assert_called_once_with(3)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_user_summary_success(self, user_service, mock_user_repo):
        """测试获取用户统计摘要成功"""
        # 准备测试数据
        test_time = datetime.now()
        expected_users = [
            User(id=1, name="user1", email="user1@example.com", regtime=test_time),
            User(id=2, name="user2", email="user2@example.com", regtime=test_time)
        ]
        
        # 模拟仓库方法
        mock_user_repo.count.return_value = 50
        mock_user_repo.get_recent_users.return_value = expected_users
        
        # 执行测试
        result = await user_service.get_user_summary()
        
        # 验证结果
        assert result["total_users"] == 50
        assert len(result["recent_users"]) == 2
        assert result["recent_users"][0]["id"] == 1
        assert result["recent_users"][0]["name"] == "user1"
        assert result["recent_users"][0]["email"] == "user1@example.com"
        assert result["recent_users"][0]["regtime"] == test_time.isoformat()
        
        # 验证方法调用
        mock_user_repo.count.assert_called_once()
        mock_user_repo.get_recent_users.assert_called_once_with(3)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_user_summary_with_null_regtime(self, user_service, mock_user_repo):
        """测试获取用户统计摘要 - 注册时间为空"""
        # 准备测试数据
        expected_users = [
            User(id=1, name="user1", email="user1@example.com", regtime=None)
        ]
        
        # 模拟仓库方法
        mock_user_repo.count.return_value = 1
        mock_user_repo.get_recent_users.return_value = expected_users
        
        # 执行测试
        result = await user_service.get_user_summary()
        
        # 验证结果
        assert result["total_users"] == 1
        assert result["recent_users"][0]["regtime"] is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_user_summary_empty_users(self, user_service, mock_user_repo):
        """测试获取用户统计摘要 - 无用户"""
        # 模拟仓库方法
        mock_user_repo.count.return_value = 0
        mock_user_repo.get_recent_users.return_value = []
        
        # 执行测试
        result = await user_service.get_user_summary()
        
        # 验证结果
        assert result["total_users"] == 0
        assert result["recent_users"] == [] 