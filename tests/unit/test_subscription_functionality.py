"""
博客订阅功能单元测试

测试博客订阅、取消订阅、状态检查等功能
"""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException
# 导入控制器模块
import src.controllers.subscription as subscription_controller
from src.services.subscription_service import SubscriptionService
from src.models.user import User
from src.models.project import Project
from src.models.relation import Relation


class TestSubscriptionFunctionality:
    """博客订阅功能测试类"""

    @pytest.fixture
    def mock_session(self):
        """模拟数据库会话"""
        return AsyncMock()

    @pytest.fixture
    def sample_user(self):
        """示例用户"""
        return User(
            id=1,
            name="testuser",
            email="test@example.com",
            state=1,
            projectid=1,  # 有博客项目
            regtime=None,
            intropiid=None,
            lastupdate=None
        )

    @pytest.fixture
    def sample_project(self):
        """示例项目"""
        return Project(
            id=2,
            title="目标博客",
            userid=2,
            status=1
        )

    @pytest.fixture
    def sample_relation(self):
        """示例订阅关系"""
        return Relation(
            id=1,
            projectid=1,  # 订阅者项目
            objectid=2,   # 目标项目
            acttype=1     # 订阅类型
        )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_subscribe_to_blog_success(self, mock_session, sample_user, sample_project):
        """测试成功订阅博客"""
        # 准备测试数据
        with patch('src.controllers.subscription.SubscriptionService') as mock_service_class:
            with patch('src.services.user_service.UserService') as mock_user_service_class:
                with patch('src.repositories.user_repository.UserRepository') as mock_user_repo_class:
                    # 模拟用户服务
                    mock_user_service = AsyncMock()
                    mock_user_service.get_user_by_id.return_value = sample_user
                    mock_user_service_class.return_value = mock_user_service
                    
                    # 模拟用户仓库
                    mock_user_repo = AsyncMock()
                    mock_user_repo_class.return_value = mock_user_repo
                    
                    # 模拟订阅服务
                    mock_service = AsyncMock()
                    mock_service.subscribe_to_blog.return_value = {
                        "success": True,
                        "message": "订阅成功",
                        "relation_id": 1
                    }
                    mock_service_class.return_value = mock_service
                    
                    # 执行测试
                    result = await subscription_controller.subscribe_to_blog(
                        target_project_id=2,
                        current_user={"id": 1, "state": 1},
                        session=mock_session
                    )
                    
                    # 验证结果
                    assert result["success"] is True
                    assert result["message"] == "订阅成功"
                    assert result["relation_id"] == 1
                    mock_service.subscribe_to_blog.assert_called_once_with(1, 2)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_subscribe_to_blog_not_logged_in(self, mock_session):
        """测试未登录用户订阅博客"""
        # 执行测试并验证异常
        with pytest.raises(HTTPException) as exc_info:
            await subscription_controller.subscribe_to_blog(
                target_project_id=2,
                current_user=None,
                session=mock_session
            )
        
        # 验证异常信息
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "需要登录才能订阅博客"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_subscribe_to_blog_no_blog(self, mock_session):
        """测试没有博客的用户订阅"""
        # 准备测试数据 - 用户没有博客项目
        user_without_blog = User(
            id=1,
            name="testuser",
            email="test@example.com",
            state=1,
            projectid=None,  # 没有博客项目
            regtime=None,
            intropiid=None,
            lastupdate=None
        )
        
        with patch('src.repositories.user_repository.UserRepository') as mock_user_repo_class:
            with patch('src.services.user_service.UserService') as mock_user_service_class:
                mock_user_repo = AsyncMock()
                mock_user_service = AsyncMock()
                mock_user_service.get_user_by_id.return_value = user_without_blog
                mock_user_repo_class.return_value = mock_user_repo
                mock_user_service_class.return_value = mock_user_service
                
                # 执行测试并验证异常
                with pytest.raises(HTTPException) as exc_info:
                    await subscription_controller.subscribe_to_blog(
                        target_project_id=2,
                        current_user={"id": 1, "state": 1},
                        session=mock_session
                    )
                
                # 验证异常信息
                assert exc_info.value.status_code == 400
                assert exc_info.value.detail == "您还没有创建博客，无法订阅其他博客"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_subscribe_to_own_blog(self, mock_session, sample_user):
        """测试订阅自己的博客"""
        with patch('src.repositories.user_repository.UserRepository') as mock_user_repo_class:
            with patch('src.services.user_service.UserService') as mock_user_service_class:
                mock_user_repo = AsyncMock()
                mock_user_service = AsyncMock()
                mock_user_service.get_user_by_id.return_value = sample_user
                mock_user_repo_class.return_value = mock_user_repo
                mock_user_service_class.return_value = mock_user_service
                
                # 执行测试并验证异常
                with pytest.raises(HTTPException) as exc_info:
                    await subscription_controller.subscribe_to_blog(
                        target_project_id=1,  # 订阅自己的博客
                        current_user={"id": 1, "state": 1},
                        session=mock_session
                    )
                
                # 验证异常信息
                assert exc_info.value.status_code == 400
                assert exc_info.value.detail == "不能订阅自己的博客"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_subscribe_to_blog_already_subscribed(self, mock_session, sample_user):
        """测试订阅已经订阅的博客"""
        with patch('src.repositories.user_repository.UserRepository') as mock_user_repo_class:
            with patch('src.services.user_service.UserService') as mock_user_service_class:
                mock_user_repo = AsyncMock()
                mock_user_service = AsyncMock()
                mock_user_service.get_user_by_id.return_value = sample_user
                mock_user_repo_class.return_value = mock_user_repo
                mock_user_service_class.return_value = mock_user_service
                
                # 模拟订阅服务返回已订阅
                with patch('src.controllers.subscription.SubscriptionService') as mock_service_class:
                    mock_service = AsyncMock()
                    mock_service.subscribe_to_blog.return_value = {
                        "success": False,
                        "message": "已经订阅过该博客"
                    }
                    mock_service_class.return_value = mock_service
                    
                    # 执行测试并验证异常
                    with pytest.raises(HTTPException) as exc_info:
                        await subscription_controller.subscribe_to_blog(
                            target_project_id=2,
                            current_user={"id": 1, "state": 1},
                            session=mock_session
                        )
                    
                    # 验证异常信息
                    assert exc_info.value.status_code == 400
                    assert exc_info.value.detail == "已经订阅过该博客"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_unsubscribe_from_blog_success(self, mock_session, sample_user):
        """测试成功取消订阅博客"""
        with patch('src.repositories.user_repository.UserRepository') as mock_user_repo_class:
            with patch('src.services.user_service.UserService') as mock_user_service_class:
                mock_user_repo = AsyncMock()
                mock_user_service = AsyncMock()
                mock_user_service.get_user_by_id.return_value = sample_user
                mock_user_repo_class.return_value = mock_user_repo
                mock_user_service_class.return_value = mock_user_service
                
                # 模拟订阅服务
                with patch('src.controllers.subscription.SubscriptionService') as mock_service_class:
                    mock_service = AsyncMock()
                    mock_service.unsubscribe_from_blog.return_value = {
                        "success": True,
                        "message": "取消订阅成功"
                    }
                    mock_service_class.return_value = mock_service
                    
                    # 执行测试
                    result = await subscription_controller.unsubscribe_from_blog(
                        target_project_id=2,
                        current_user={"id": 1, "state": 1},
                        session=mock_session
                    )
                    
                    # 验证结果
                    assert result["success"] is True
                    assert result["message"] == "取消订阅成功"
                    mock_service.unsubscribe_from_blog.assert_called_once_with(1, 2)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_unsubscribe_from_blog_not_logged_in(self, mock_session):
        """测试未登录用户取消订阅"""
        # 执行测试并验证异常
        with pytest.raises(HTTPException) as exc_info:
            await subscription_controller.unsubscribe_from_blog(
                target_project_id=2,
                current_user=None,
                session=mock_session
            )
        
        # 验证异常信息
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "需要登录才能取消订阅"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_unsubscribe_from_blog_not_subscribed(self, mock_session, sample_user):
        """测试取消未订阅的博客"""
        with patch('src.repositories.user_repository.UserRepository') as mock_user_repo_class:
            with patch('src.services.user_service.UserService') as mock_user_service_class:
                mock_user_repo = AsyncMock()
                mock_user_service = AsyncMock()
                mock_user_service.get_user_by_id.return_value = sample_user
                mock_user_repo_class.return_value = mock_user_repo
                mock_user_service_class.return_value = mock_user_service
                
                # 模拟订阅服务返回未订阅
                with patch('src.controllers.subscription.SubscriptionService') as mock_service_class:
                    mock_service = AsyncMock()
                    mock_service.unsubscribe_from_blog.return_value = {
                        "success": False,
                        "message": "未订阅该博客"
                    }
                    mock_service_class.return_value = mock_service
                    
                    # 执行测试并验证异常
                    with pytest.raises(HTTPException) as exc_info:
                        await subscription_controller.unsubscribe_from_blog(
                            target_project_id=2,
                            current_user={"id": 1, "state": 1},
                            session=mock_session
                        )
                    
                    # 验证异常信息
                    assert exc_info.value.status_code == 400
                    assert exc_info.value.detail == "未订阅该博客"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_subscription_status_logged_in_subscribed(self, mock_session, sample_user):
        """测试已登录且已订阅的状态检查"""
        with patch('src.repositories.user_repository.UserRepository') as mock_user_repo_class:
            with patch('src.services.user_service.UserService') as mock_user_service_class:
                mock_user_repo = AsyncMock()
                mock_user_service = AsyncMock()
                mock_user_service.get_user_by_id.return_value = sample_user
                mock_user_repo_class.return_value = mock_user_repo
                mock_user_service_class.return_value = mock_user_service
                
                # 模拟订阅服务
                with patch('src.controllers.subscription.SubscriptionService') as mock_service_class:
                    mock_service = AsyncMock()
                    mock_service.check_subscription_status.return_value = {
                        "is_subscribed": True,
                        "subscriber_project_id": 1,
                        "target_project_id": 2
                    }
                    mock_service_class.return_value = mock_service
                    
                    # 执行测试
                    result = await subscription_controller.get_subscription_status(
                        target_project_id=2,
                        current_user={"id": 1, "state": 1},
                        session=mock_session
                    )
                    
                    # 验证结果
                    assert result["is_subscribed"] is True
                    assert result["can_subscribe"] is True
                    assert result["subscriber_project_id"] == 1
                    assert result["target_project_id"] == 2

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_subscription_status_not_logged_in(self, mock_session):
        """测试未登录用户的状态检查"""
        # 执行测试
        result = await subscription_controller.get_subscription_status(
            target_project_id=2,
            current_user=None,
            session=mock_session
        )
        
        # 验证结果
        assert result["is_subscribed"] is False
        assert result["can_subscribe"] is False
        assert result["message"] == "未登录"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_subscription_status_own_blog(self, mock_session, sample_user):
        """测试查看自己博客的订阅状态"""
        with patch('src.repositories.user_repository.UserRepository') as mock_user_repo_class:
            with patch('src.services.user_service.UserService') as mock_user_service_class:
                mock_user_repo = AsyncMock()
                mock_user_service = AsyncMock()
                mock_user_service.get_user_by_id.return_value = sample_user
                mock_user_repo_class.return_value = mock_user_repo
                mock_user_service_class.return_value = mock_user_service
                
                # 执行测试
                result = await subscription_controller.get_subscription_status(
                    target_project_id=1,  # 自己的博客
                    current_user={"id": 1, "state": 1},
                    session=mock_session
                )
                
                # 验证结果
                assert result["is_subscribed"] is False
                assert result["can_subscribe"] is False
                assert result["message"] == "不能订阅自己的博客"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_subscription_service_subscribe_success(self, mock_session, sample_project):
        """测试订阅服务成功订阅"""
        # 准备测试数据
        with patch('src.services.subscription_service.ProjectRepository') as mock_project_repo_class:
            with patch('src.services.subscription_service.RelationRepository') as mock_relation_repo_class:
                mock_project_repo = AsyncMock()
                mock_relation_repo = AsyncMock()
                mock_project_repo.get_project_by_id.return_value = sample_project
                mock_relation_repo.is_subscribed.return_value = False
                mock_relation_repo.create_relation.return_value = Relation(id=1, projectid=1, objectid=2, acttype=1)
                mock_project_repo_class.return_value = mock_project_repo
                mock_relation_repo_class.return_value = mock_relation_repo
                
                # 创建服务实例
                service = SubscriptionService(mock_session)
                
                # 执行测试
                result = await service.subscribe_to_blog(1, 2)
                
                # 验证结果
                assert result["success"] is True
                assert result["message"] == "订阅成功"
                assert result["relation_id"] == 1
                mock_project_repo.get_project_by_id.assert_called_once_with(2)
                mock_relation_repo.is_subscribed.assert_called_once_with(1, 2)
                mock_relation_repo.create_relation.assert_called_once_with(projectid=1, objectid=2, acttype=1)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_subscription_service_subscribe_target_not_found(self, mock_session):
        """测试订阅服务目标博客不存在"""
        # 准备测试数据
        with patch('src.services.subscription_service.ProjectRepository') as mock_project_repo_class:
            mock_project_repo = AsyncMock()
            mock_project_repo.get_project_by_id.return_value = None
            mock_project_repo_class.return_value = mock_project_repo
            
            # 创建服务实例
            service = SubscriptionService(mock_session)
            
            # 执行测试
            result = await service.subscribe_to_blog(1, 999)
            
            # 验证结果
            assert result["success"] is False
            assert result["message"] == "目标博客不存在"
            mock_project_repo.get_project_by_id.assert_called_once_with(999)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_subscription_service_subscribe_already_subscribed(self, mock_session, sample_project):
        """测试订阅服务已经订阅"""
        # 准备测试数据
        with patch('src.services.subscription_service.ProjectRepository') as mock_project_repo_class:
            with patch('src.services.subscription_service.RelationRepository') as mock_relation_repo_class:
                mock_project_repo = AsyncMock()
                mock_relation_repo = AsyncMock()
                mock_project_repo.get_project_by_id.return_value = sample_project
                mock_relation_repo.is_subscribed.return_value = True
                mock_project_repo_class.return_value = mock_project_repo
                mock_relation_repo_class.return_value = mock_relation_repo
                
                # 创建服务实例
                service = SubscriptionService(mock_session)
                
                # 执行测试
                result = await service.subscribe_to_blog(1, 2)
                
                # 验证结果
                assert result["success"] is False
                assert result["message"] == "已经订阅过该博客"
                mock_project_repo.get_project_by_id.assert_called_once_with(2)
                mock_relation_repo.is_subscribed.assert_called_once_with(1, 2)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_subscription_service_unsubscribe_success(self, mock_session):
        """测试订阅服务成功取消订阅"""
        # 准备测试数据
        with patch('src.services.subscription_service.RelationRepository') as mock_relation_repo_class:
            mock_relation_repo = AsyncMock()
            mock_relation_repo.is_subscribed.return_value = True
            mock_relation_repo.delete_relation.return_value = True
            mock_relation_repo_class.return_value = mock_relation_repo
            
            # 创建服务实例
            service = SubscriptionService(mock_session)
            
            # 执行测试
            result = await service.unsubscribe_from_blog(1, 2)
            
            # 验证结果
            assert result["success"] is True
            assert result["message"] == "取消订阅成功"
            mock_relation_repo.is_subscribed.assert_called_once_with(1, 2)
            mock_relation_repo.delete_relation.assert_called_once_with(projectid=1, objectid=2, acttype=1)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_subscription_service_unsubscribe_not_subscribed(self, mock_session):
        """测试订阅服务取消未订阅的博客"""
        # 准备测试数据
        with patch('src.services.subscription_service.RelationRepository') as mock_relation_repo_class:
            mock_relation_repo = AsyncMock()
            mock_relation_repo.is_subscribed.return_value = False
            mock_relation_repo_class.return_value = mock_relation_repo
            
            # 创建服务实例
            service = SubscriptionService(mock_session)
            
            # 执行测试
            result = await service.unsubscribe_from_blog(1, 2)
            
            # 验证结果
            assert result["success"] is False
            assert result["message"] == "未订阅该博客"
            mock_relation_repo.is_subscribed.assert_called_once_with(1, 2)
            mock_relation_repo.delete_relation.assert_not_called()
