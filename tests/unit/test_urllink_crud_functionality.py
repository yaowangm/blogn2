"""
友情链接CRUD功能单元测试

测试友情链接的创建、读取、更新、删除功能以及权限检查
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException
from src.controllers.urllink import (
    create_friend_link,
    update_friend_link,
    delete_friend_link,
    _check_friend_link_permission,
    FriendLinkCreate,
    FriendLinkUpdate
)
from src.models.urllink import UrlLink


class TestUrlLinkCrudFunctionality:
    """友情链接CRUD功能测试类"""

    @pytest.fixture
    def mock_session(self):
        """模拟数据库会话"""
        return AsyncMock()

    @pytest.fixture
    def sample_friend_link(self):
        """示例友情链接"""
        return UrlLink(
            id=1,
            subject="测试链接",
            linkstr="https://example.com",
            projectid=1,
            ordernum=1
        )

    @pytest.fixture
    def sample_project(self):
        """示例项目"""
        from src.models.project import Project
        return Project(
            id=1,
            title="测试博客",
            userid=1,
            status=1
        )

    @pytest.fixture
    def friend_link_create_data(self):
        """友情链接创建数据"""
        return FriendLinkCreate(
            subject="新链接",
            linkstr="https://newlink.com",
            ordernum=2
        )

    @pytest.fixture
    def friend_link_update_data(self):
        """友情链接更新数据"""
        return FriendLinkUpdate(
            subject="更新的链接",
            linkstr="https://updatedlink.com",
            ordernum=3
        )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_friend_link_success(self, mock_session, sample_friend_link, friend_link_create_data):
        """测试成功创建友情链接"""
        # 准备测试数据
        with patch('src.controllers.urllink.UrlLinkRepository') as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_friend_links_by_project.return_value = []  # 没有现有链接
            mock_repo.create_friend_link.return_value = sample_friend_link
            mock_repo_class.return_value = mock_repo
            
            # 模拟权限检查
            with patch('src.controllers.urllink._check_friend_link_permission', return_value=True):
                # 执行测试
                result = await create_friend_link(
                    project_id=1,
                    friend_link_data=friend_link_create_data,
                    current_user={"id": 1, "state": 1},
                    session=mock_session
                )
                
                # 验证结果
                assert result == sample_friend_link
                mock_repo.get_friend_links_by_project.assert_called_once_with(1)
                mock_repo.create_friend_link.assert_called_once_with(1, friend_link_create_data)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_friend_link_permission_denied(self, mock_session, friend_link_create_data):
        """测试创建友情链接权限被拒绝"""
        # 模拟权限检查失败
        with patch('src.controllers.urllink._check_friend_link_permission', return_value=False):
            # 执行测试并验证异常
            with pytest.raises(HTTPException) as exc_info:
                await create_friend_link(
                    project_id=1,
                    friend_link_data=friend_link_create_data,
                    current_user={"id": 2, "state": 1},
                    session=mock_session
                )
            
            # 验证异常信息
            assert exc_info.value.status_code == 403
            assert exc_info.value.detail == "无权限管理该博客的友情链接"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_friend_link_limit_exceeded(self, mock_session, friend_link_create_data):
        """测试创建友情链接超过数量限制"""
        # 准备测试数据 - 已有20个链接
        existing_links = [UrlLink(id=i, subject=f"链接{i}", linkstr=f"https://link{i}.com", projectid=1, ordernum=i) 
                         for i in range(1, 21)]
        
        with patch('src.controllers.urllink.UrlLinkRepository') as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_friend_links_by_project.return_value = existing_links
            mock_repo_class.return_value = mock_repo
            
            # 模拟权限检查通过
            with patch('src.controllers.urllink._check_friend_link_permission', return_value=True):
                # 执行测试并验证异常
                with pytest.raises(HTTPException) as exc_info:
                    await create_friend_link(
                        project_id=1,
                        friend_link_data=friend_link_create_data,
                        current_user={"id": 1, "state": 1},
                        session=mock_session
                    )
                
                # 验证异常信息
                assert exc_info.value.status_code == 400
                assert exc_info.value.detail == "友情链接数量不能超过20个"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_update_friend_link_success(self, mock_session, sample_friend_link, friend_link_update_data):
        """测试成功更新友情链接"""
        # 准备测试数据
        updated_link = UrlLink(
            id=1,
            subject="更新的链接",
            linkstr="https://updatedlink.com",
            projectid=1,
            ordernum=3
        )
        
        with patch('src.controllers.urllink.UrlLinkRepository') as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_friend_link_by_id.return_value = sample_friend_link
            mock_repo.update_friend_link.return_value = updated_link
            mock_repo_class.return_value = mock_repo
            
            # 模拟权限检查
            with patch('src.controllers.urllink._check_friend_link_permission', return_value=True):
                # 执行测试
                result = await update_friend_link(
                    link_id=1,
                    friend_link_data=friend_link_update_data,
                    current_user={"id": 1, "state": 1},
                    session=mock_session
                )
                
                # 验证结果
                assert result == updated_link
                mock_repo.get_friend_link_by_id.assert_called_once_with(1)
                mock_repo.update_friend_link.assert_called_once_with(1, friend_link_update_data)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_update_friend_link_not_found(self, mock_session, friend_link_update_data):
        """测试更新不存在的友情链接"""
        # 准备测试数据
        with patch('src.controllers.urllink.UrlLinkRepository') as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_friend_link_by_id.return_value = None
            mock_repo_class.return_value = mock_repo
            
            # 执行测试并验证异常
            with pytest.raises(HTTPException) as exc_info:
                await update_friend_link(
                    link_id=999,
                    friend_link_data=friend_link_update_data,
                    current_user={"id": 1, "state": 1},
                    session=mock_session
                )
            
            # 验证异常信息
            assert exc_info.value.status_code == 404
            assert exc_info.value.detail == "友情链接不存在"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_update_friend_link_permission_denied(self, mock_session, sample_friend_link, friend_link_update_data):
        """测试更新友情链接权限被拒绝"""
        # 准备测试数据
        with patch('src.controllers.urllink.UrlLinkRepository') as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_friend_link_by_id.return_value = sample_friend_link
            mock_repo_class.return_value = mock_repo
            
            # 模拟权限检查失败
            with patch('src.controllers.urllink._check_friend_link_permission', return_value=False):
                # 执行测试并验证异常
                with pytest.raises(HTTPException) as exc_info:
                    await update_friend_link(
                        link_id=1,
                        friend_link_data=friend_link_update_data,
                        current_user={"id": 2, "state": 1},
                        session=mock_session
                    )
                
                # 验证异常信息
                assert exc_info.value.status_code == 403
                assert exc_info.value.detail == "无权限管理该博客的友情链接"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delete_friend_link_success(self, mock_session, sample_friend_link):
        """测试成功删除友情链接"""
        # 准备测试数据
        with patch('src.controllers.urllink.UrlLinkRepository') as mock_repo_class:
            with patch('src.controllers.urllink.require_auth') as mock_require_auth:
                mock_repo = AsyncMock()
                mock_repo.get_friend_link_by_id.return_value = sample_friend_link
                mock_repo.delete_friend_link.return_value = None
                mock_repo_class.return_value = mock_repo
                
                # 模拟权限装饰器，让它直接调用原函数
                def mock_decorator(func):
                    return func
                mock_require_auth.return_value = mock_decorator
                
                # 模拟权限检查
                with patch('src.controllers.urllink._check_friend_link_permission', return_value=True):
                    # 模拟缓存清理
                    with patch('src.utils.cache.cache_manager') as mock_cache:
                        mock_cache.clear_pattern = AsyncMock(return_value=None)
                        
                        # 执行测试
                        result = await delete_friend_link(
                            link_id=1,
                            current_user={"id": 1, "state": 1},
                            session=mock_session
                        )
                        
                        # 验证结果
                        assert result == {"message": "友情链接删除成功"}
                        mock_repo.get_friend_link_by_id.assert_called_once_with(1)
                        mock_repo.delete_friend_link.assert_called_once_with(1)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delete_friend_link_not_found(self, mock_session):
        """测试删除不存在的友情链接"""
        # 准备测试数据
        with patch('src.controllers.urllink.UrlLinkRepository') as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_friend_link_by_id.return_value = None
            mock_repo_class.return_value = mock_repo
            
            # 执行测试并验证异常
            with pytest.raises(HTTPException) as exc_info:
                await delete_friend_link(
                    link_id=999,
                    current_user={"id": 1, "state": 1},
                    session=mock_session
                )
            
            # 验证异常信息
            assert exc_info.value.status_code == 404
            assert exc_info.value.detail == "友情链接不存在"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delete_friend_link_permission_denied(self, mock_session, sample_friend_link):
        """测试删除友情链接权限被拒绝"""
        # 准备测试数据
        with patch('src.controllers.urllink.UrlLinkRepository') as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_friend_link_by_id.return_value = sample_friend_link
            mock_repo_class.return_value = mock_repo
            
            # 模拟权限检查失败
            with patch('src.controllers.urllink._check_friend_link_permission', return_value=False):
                # 执行测试并验证异常
                with pytest.raises(HTTPException) as exc_info:
                    await delete_friend_link(
                        link_id=1,
                        current_user={"id": 2, "state": 1},
                        session=mock_session
                    )
                
                # 验证异常信息
                assert exc_info.value.status_code == 403
                assert exc_info.value.detail == "无权限管理该博客的友情链接"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_check_friend_link_permission_admin(self, mock_session):
        """测试管理员权限检查"""
        # 执行测试
        result = await _check_friend_link_permission(
            session=mock_session,
            project_id=1,
            current_user={"id": 1, "state": 10}  # 管理员
        )
        
        # 验证结果
        assert result is True

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_check_friend_link_permission_owner(self, mock_session, sample_project):
        """测试项目所有者权限检查"""
        # 准备测试数据
        with patch('src.repositories.project_repository.ProjectRepository') as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_project_by_id.return_value = sample_project
            mock_repo_class.return_value = mock_repo
            
            # 执行测试
            result = await _check_friend_link_permission(
                session=mock_session,
                project_id=1,
                current_user={"id": 1, "state": 1}  # 项目所有者
            )
            
            # 验证结果
            assert result is True
            mock_repo.get_project_by_id.assert_called_once_with(1)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_check_friend_link_permission_denied(self, mock_session, sample_project):
        """测试权限被拒绝"""
        # 准备测试数据
        with patch('src.repositories.project_repository.ProjectRepository') as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_project_by_id.return_value = sample_project
            mock_repo_class.return_value = mock_repo
            
            # 执行测试
            result = await _check_friend_link_permission(
                session=mock_session,
                project_id=1,
                current_user={"id": 2, "state": 1}  # 不是项目所有者
            )
            
            # 验证结果
            assert result is False
            mock_repo.get_project_by_id.assert_called_once_with(1)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_check_friend_link_permission_project_not_found(self, mock_session):
        """测试项目不存在时的权限检查"""
        # 准备测试数据
        with patch('src.repositories.project_repository.ProjectRepository') as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_project_by_id.return_value = None
            mock_repo_class.return_value = mock_repo
            
            # 执行测试
            result = await _check_friend_link_permission(
                session=mock_session,
                project_id=999,
                current_user={"id": 1, "state": 1}
            )
            
            # 验证结果
            assert result is False
            mock_repo.get_project_by_id.assert_called_once_with(999)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_friend_link_service_error(self, mock_session, friend_link_create_data):
        """测试创建友情链接时服务错误"""
        # 准备测试数据
        with patch('src.controllers.urllink.UrlLinkRepository') as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_friend_links_by_project.return_value = []
            mock_repo.create_friend_link.side_effect = Exception("数据库错误")
            mock_repo_class.return_value = mock_repo
            
            # 模拟权限检查
            with patch('src.controllers.urllink._check_friend_link_permission', return_value=True):
                # 执行测试并验证异常
                with pytest.raises(HTTPException) as exc_info:
                    await create_friend_link(
                        project_id=1,
                        friend_link_data=friend_link_create_data,
                        current_user={"id": 1, "state": 1},
                        session=mock_session
                    )
                
                # 验证异常信息
                assert exc_info.value.status_code == 500
                assert "数据库错误" in exc_info.value.detail
