"""
用户仓库intropiid相关方法单元测试
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from src.repositories.user_repository import UserRepository
from src.models.user import User


class TestUserRepositoryIntro:
    """用户仓库intropiid相关方法测试类"""

    @pytest.fixture
    def mock_session(self):
        """模拟数据库会话"""
        return AsyncMock()

    @pytest.fixture
    def user_repository(self, mock_session):
        """创建UserRepository实例"""
        return UserRepository(mock_session)

    @pytest.fixture
    def sample_user(self):
        """示例用户数据"""
        return User(
            id=1,
            name="testuser",
            email="test@example.com",
            state=1,
            intropiid=None
        )

    @pytest.mark.unit
    async def test_update_intropiid_success(self, user_repository, mock_session, sample_user):
        """测试更新intropiid成功"""
        # 模拟get_by_id返回用户
        mock_result = MagicMock()
        mock_result.first.return_value = sample_user
        mock_session.exec.return_value = mock_result
        
        # 模拟commit成功
        mock_session.commit.return_value = None
        
        # 执行测试
        result = await user_repository.update_intropiid(1, 100)
        
        # 验证结果
        assert result is True
        assert sample_user.intropiid == 100
        
        # 验证方法调用
        mock_session.exec.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.unit
    async def test_update_intropiid_user_not_found(self, user_repository, mock_session):
        """测试更新intropiid失败 - 用户不存在"""
        # 模拟get_by_id返回None
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result
        
        # 执行测试
        result = await user_repository.update_intropiid(999, 100)
        
        # 验证结果
        assert result is False
        
        # 验证方法调用
        mock_session.exec.assert_called_once()
        # 用户不存在时不应该调用commit
        mock_session.commit.assert_not_called()

    @pytest.mark.unit
    async def test_update_intropiid_database_error(self, user_repository, mock_session, sample_user):
        """测试更新intropiid失败 - 数据库错误"""
        # 模拟get_by_id返回用户
        mock_result = MagicMock()
        mock_result.first.return_value = sample_user
        mock_session.exec.return_value = mock_result
        
        # 模拟commit抛出异常
        mock_session.commit.side_effect = Exception("数据库连接错误")
        mock_session.rollback.return_value = None
        
        # 执行测试
        result = await user_repository.update_intropiid(1, 100)
        
        # 验证结果
        assert result is False
        
        # 验证方法调用
        mock_session.exec.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.rollback.assert_called_once()

    @pytest.mark.unit
    async def test_update_intropiid_rollback_error(self, user_repository, mock_session, sample_user):
        """测试更新intropiid失败 - 回滚也失败"""
        # 模拟get_by_id返回用户
        mock_result = MagicMock()
        mock_result.first.return_value = sample_user
        mock_session.exec.return_value = mock_result
        
        # 模拟commit和rollback都抛出异常
        mock_session.commit.side_effect = Exception("数据库连接错误")
        mock_session.rollback.side_effect = Exception("回滚失败")
        
        # 执行测试并验证异常
        with pytest.raises(Exception) as exc_info:
            await user_repository.update_intropiid(1, 100)
        
        # 验证异常信息
        assert "回滚失败" in str(exc_info.value)
        
        # 验证方法调用
        mock_session.exec.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.rollback.assert_called_once()

    @pytest.mark.unit
    async def test_update_intropiid_with_existing_intropiid(self, user_repository, mock_session):
        """测试更新intropiid - 用户已有intropiid"""
        # 创建已有intropiid的用户
        user_with_intro = User(
            id=1,
            name="testuser",
            email="test@example.com",
            state=1,
            intropiid=50  # 已有个人介绍
        )
        
        # 模拟get_by_id返回用户
        mock_result = MagicMock()
        mock_result.first.return_value = user_with_intro
        mock_session.exec.return_value = mock_result
        
        # 模拟commit成功
        mock_session.commit.return_value = None
        
        # 执行测试
        result = await user_repository.update_intropiid(1, 100)
        
        # 验证结果
        assert result is True
        assert user_with_intro.intropiid == 100  # 应该更新为新的intropiid
        
        # 验证方法调用
        mock_session.exec.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.unit
    async def test_update_intropiid_set_to_none(self, user_repository, mock_session):
        """测试更新intropiid - 设置为None（清除个人介绍）"""
        # 创建已有intropiid的用户
        user_with_intro = User(
            id=1,
            name="testuser",
            email="test@example.com",
            state=1,
            intropiid=50
        )
        
        # 模拟get_by_id返回用户
        mock_result = MagicMock()
        mock_result.first.return_value = user_with_intro
        mock_session.exec.return_value = mock_result
        
        # 模拟commit成功
        mock_session.commit.return_value = None
        
        # 执行测试 - 设置为None
        result = await user_repository.update_intropiid(1, None)
        
        # 验证结果
        assert result is True
        assert user_with_intro.intropiid is None
        
        # 验证方法调用
        mock_session.exec.assert_called_once()
        mock_session.commit.assert_called_once()
