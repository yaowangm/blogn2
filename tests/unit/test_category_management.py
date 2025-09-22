"""
分类管理功能单元测试

测试分类的创建、读取、更新、删除功能以及权限检查
"""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException
from src.controllers.project import (
    get_project_categories,
    create_category,
    update_category,
    delete_category
)
from src.models.project import Project
from src.models.folder import Folder


class TestCategoryManagement:
    """分类管理功能测试类"""

    @pytest.fixture
    def mock_session(self):
        """模拟数据库会话"""
        return AsyncMock()

    @pytest.fixture
    def sample_project(self):
        """示例项目"""
        return Project(
            id=1,
            title="测试博客",
            userid=1,
            status=1
        )

    @pytest.fixture
    def sample_folder(self):
        """示例分类"""
        return Folder(
            id=1,
            name="测试分类",
            projectid=1,
            recordcount=5,
            postcount=3
        )

    @pytest.fixture
    def sample_categories_data(self):
        """示例分类数据"""
        return [
            {
                "id": 1,
                "name": "技术",
                "recordcount": 10,
                "color": "#3b82f6"
            },
            {
                "id": 2,
                "name": "生活",
                "recordcount": 5,
                "color": "#10b981"
            }
        ]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_project_categories_success(self, mock_session, sample_categories_data):
        """测试成功获取项目分类列表"""
        with patch('src.controllers.project.FolderRepository') as mock_folder_repo_class:
            with patch('src.repositories.project_item_repository.ProjectItemRepository') as mock_project_item_repo_class:
                # 模拟文件夹仓库
                mock_folder_repo = AsyncMock()
                mock_folder_repo.get_by_project_id_with_count.return_value = [
                    {"id": 1, "name": "技术", "recordcount": 10},
                    {"id": 2, "name": "生活", "recordcount": 5}
                ]
                mock_folder_repo_class.return_value = mock_folder_repo
                
                # 模拟项目项仓库
                mock_project_item_repo = AsyncMock()
                # 模拟异步方法，直接返回结果
                async def mock_count_by_project_id_and_folder(project_id, folder_id):
                    return 3  # 未分类文章数
                mock_project_item_repo.count_by_project_id_and_folder = mock_count_by_project_id_and_folder
                mock_project_item_repo_class.return_value = mock_project_item_repo
                
                # 模拟缓存装饰器
                with patch('src.controllers.project.cache_project_categories') as mock_cache:
                    mock_cache.return_value = lambda func: func  # 直接返回原函数
                    
                    # 执行测试
                    result = await get_project_categories(project_id=1, session=mock_session)
                    
                    # 验证结果
                    assert len(result) == 3  # 未分类 + 2个分类
                    assert result[0]["id"] == 0
                    assert result[0]["name"] == "未分类"
                    assert result[0]["count"] == 3
                    assert result[1]["id"] == 1
                    assert result[1]["name"] == "技术"
                    assert result[1]["count"] == 10
                    assert result[2]["id"] == 2
                    assert result[2]["name"] == "生活"
                    assert result[2]["count"] == 5

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_project_categories_empty(self, mock_session):
        """测试获取空分类列表"""
        # 准备测试数据
        with patch('src.controllers.project.FolderRepository') as mock_folder_repo_class:
            with patch('src.repositories.project_item_repository.ProjectItemRepository') as mock_item_repo_class:
                mock_folder_repo = AsyncMock()
                mock_item_repo = AsyncMock()
                
                # 模拟异步方法，直接返回结果
                async def mock_get_by_project_id_with_count(project_id):
                    return []
                async def mock_count_by_project_id_and_folder(project_id, folder_id):
                    return 0
                
                mock_folder_repo.get_by_project_id_with_count = mock_get_by_project_id_with_count
                mock_item_repo.count_by_project_id_and_folder = mock_count_by_project_id_and_folder
                
                mock_folder_repo_class.return_value = mock_folder_repo
                mock_item_repo_class.return_value = mock_item_repo
                
                # 执行测试
                result = await get_project_categories(project_id=1, session=mock_session)
                
                # 验证结果
                assert len(result) == 1  # 只有未分类
                assert result[0]["id"] == 0
                assert result[0]["name"] == "未分类"
                assert result[0]["count"] == 0

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_project_categories_error(self, mock_session):
        """测试获取分类列表时发生错误"""
        # 准备测试数据
        with patch('src.controllers.project.FolderRepository') as mock_folder_repo_class:
            mock_folder_repo = AsyncMock()
            mock_folder_repo.get_by_project_id_with_count.side_effect = Exception("数据库错误")
            mock_folder_repo_class.return_value = mock_folder_repo
            
            # 执行测试并验证异常
            with pytest.raises(HTTPException) as exc_info:
                await get_project_categories(project_id=1, session=mock_session)
            
            # 验证异常信息
            assert exc_info.value.status_code == 500
            assert "获取分类列表失败" in exc_info.value.detail

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_category_success(self, mock_session, sample_project, sample_folder):
        """测试成功创建分类"""
        # 准备测试数据
        with patch('src.controllers.project.ProjectRepository') as mock_project_repo_class:
            with patch('src.controllers.project.FolderRepository') as mock_folder_repo_class:
                mock_project_repo = AsyncMock()
                mock_folder_repo = AsyncMock()
                
                mock_project_repo.get_project_by_id.return_value = sample_project
                mock_folder_repo_class.return_value = mock_folder_repo
                mock_project_repo_class.return_value = mock_project_repo
                
                # 模拟数据库操作
                mock_session.add.return_value = None
                mock_session.commit.return_value = None
                mock_session.refresh.return_value = None
                
                # 执行测试
                result = await create_category(
                    project_id=1,
                    category_data={"name": "新分类"},
                    current_user={"id": 1, "state": 1},
                    session=mock_session
                )
                
                # 验证结果
                assert result["name"] == "新分类"
                assert result["count"] == 0
                assert result["color"] == "#3b82f6"
                mock_project_repo.get_project_by_id.assert_called_once_with(1)
                mock_session.add.assert_called_once()
                mock_session.commit.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_category_project_not_found(self, mock_session):
        """测试创建分类时项目不存在"""
        # 准备测试数据
        with patch('src.controllers.project.ProjectRepository') as mock_project_repo_class:
            mock_project_repo = AsyncMock()
            mock_project_repo.get_project_by_id.return_value = None
            mock_project_repo_class.return_value = mock_project_repo
            
            # 执行测试并验证异常
            with pytest.raises(HTTPException) as exc_info:
                await create_category(
                    project_id=999,
                    category_data={"name": "新分类"},
                    current_user={"id": 1, "state": 1},
                    session=mock_session
                )
            
            # 验证异常信息
            assert exc_info.value.status_code == 404
            assert exc_info.value.detail == "项目不存在"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_category_permission_denied(self, mock_session, sample_project):
        """测试创建分类权限被拒绝"""
        # 准备测试数据
        with patch('src.controllers.project.ProjectRepository') as mock_project_repo_class:
            mock_project_repo = AsyncMock()
            mock_project_repo.get_project_by_id.return_value = sample_project
            mock_project_repo_class.return_value = mock_project_repo
            
            # 执行测试并验证异常
            with pytest.raises(HTTPException) as exc_info:
                await create_category(
                    project_id=1,
                    category_data={"name": "新分类"},
                    current_user={"id": 2, "state": 1},  # 不是项目所有者
                    session=mock_session
                )
            
            # 验证异常信息
            assert exc_info.value.status_code == 403
            assert exc_info.value.detail == "没有权限创建分类"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_category_trim_name(self, mock_session, sample_project):
        """测试创建分类时自动去除名称前后空格"""
        # 准备测试数据
        with patch('src.controllers.project.ProjectRepository') as mock_project_repo_class:
            with patch('src.controllers.project.FolderRepository') as mock_folder_repo_class:
                mock_project_repo = AsyncMock()
                mock_folder_repo = AsyncMock()
                
                mock_project_repo.get_project_by_id.return_value = sample_project
                mock_folder_repo_class.return_value = mock_folder_repo
                mock_project_repo_class.return_value = mock_project_repo
                
                # 模拟数据库操作
                mock_session.add.return_value = None
                mock_session.commit.return_value = None
                mock_session.refresh.return_value = None
                
                # 执行测试
                result = await create_category(
                    project_id=1,
                    category_data={"name": "  新分类  "},  # 前后有空格
                    current_user={"id": 1, "state": 1},
                    session=mock_session
                )
                
                # 验证结果 - 名称应该被trim
                assert result["name"] == "新分类"
                mock_session.add.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_update_category_success(self, mock_session, sample_project, sample_folder):
        """测试成功更新分类"""
        # 准备测试数据
        with patch('src.controllers.project.ProjectRepository') as mock_project_repo_class:
            with patch('src.controllers.project.FolderRepository') as mock_folder_repo_class:
                mock_project_repo = AsyncMock()
                mock_folder_repo = AsyncMock()
                
                mock_project_repo.get_project_by_id.return_value = sample_project
                mock_folder_repo.get_by_id.return_value = sample_folder
                mock_project_repo_class.return_value = mock_project_repo
                mock_folder_repo_class.return_value = mock_folder_repo
                
                # 模拟数据库操作
                mock_session.commit.return_value = None
                mock_session.refresh.return_value = None
                
                # 执行测试
                result = await update_category(
                    project_id=1,
                    category_id=1,
                    category_data={"name": "更新的分类"},
                    current_user={"id": 1, "state": 1},
                    session=mock_session
                )
                
                # 验证结果
                assert result["name"] == "更新的分类"
                assert result["count"] == 5
                mock_project_repo.get_project_by_id.assert_called_once_with(1)
                mock_folder_repo.get_by_id.assert_called_once_with(1)
                mock_session.commit.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_update_category_not_found(self, mock_session, sample_project):
        """测试更新不存在的分类"""
        # 准备测试数据
        with patch('src.controllers.project.ProjectRepository') as mock_project_repo_class:
            with patch('src.controllers.project.FolderRepository') as mock_folder_repo_class:
                mock_project_repo = AsyncMock()
                mock_folder_repo = AsyncMock()
                
                mock_project_repo.get_project_by_id.return_value = sample_project
                mock_folder_repo.get_by_id.return_value = None
                mock_project_repo_class.return_value = mock_project_repo
                mock_folder_repo_class.return_value = mock_folder_repo
                
                # 执行测试并验证异常
                with pytest.raises(HTTPException) as exc_info:
                    await update_category(
                        project_id=1,
                        category_id=999,
                        category_data={"name": "更新的分类"},
                        current_user={"id": 1, "state": 1},
                        session=mock_session
                    )
                
                # 验证异常信息
                assert exc_info.value.status_code == 404
                assert exc_info.value.detail == "分类不存在"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_update_category_wrong_project(self, mock_session, sample_project):
        """测试更新其他项目的分类"""
        # 准备测试数据 - 分类属于其他项目
        other_folder = Folder(
            id=1,
            name="其他分类",
            projectid=2,  # 属于其他项目
            recordcount=0,
            postcount=0
        )
        
        with patch('src.controllers.project.ProjectRepository') as mock_project_repo_class:
            with patch('src.controllers.project.FolderRepository') as mock_folder_repo_class:
                mock_project_repo = AsyncMock()
                mock_folder_repo = AsyncMock()
                
                mock_project_repo.get_project_by_id.return_value = sample_project
                mock_folder_repo.get_by_id.return_value = other_folder
                mock_project_repo_class.return_value = mock_project_repo
                mock_folder_repo_class.return_value = mock_folder_repo
                
                # 执行测试并验证异常
                with pytest.raises(HTTPException) as exc_info:
                    await update_category(
                        project_id=1,
                        category_id=1,
                        category_data={"name": "更新的分类"},
                        current_user={"id": 1, "state": 1},
                        session=mock_session
                    )
                
                # 验证异常信息
                assert exc_info.value.status_code == 404
                assert exc_info.value.detail == "分类不存在"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delete_category_success(self, mock_session, sample_project, sample_folder):
        """测试成功删除分类"""
        # 准备测试数据
        with patch('src.controllers.project.ProjectRepository') as mock_project_repo_class:
            with patch('src.controllers.project.FolderRepository') as mock_folder_repo_class:
                with patch('src.repositories.post_repository.PostRepository') as mock_post_repo_class:
                    mock_project_repo = AsyncMock()
                    mock_folder_repo = AsyncMock()
                    mock_post_repo = AsyncMock()
                    
                    mock_project_repo.get_project_by_id = AsyncMock(return_value=sample_project)
                    mock_folder_repo.get_by_id = AsyncMock(return_value=sample_folder)
                    # 模拟异步方法
                    mock_post_repo.update_articles_folder_to_uncategorized = AsyncMock(return_value=3)
                    
                    mock_project_repo_class.return_value = mock_project_repo
                    mock_folder_repo_class.return_value = mock_folder_repo
                    mock_post_repo_class.return_value = mock_post_repo
                    
                    # 模拟数据库操作
                    mock_session.delete.return_value = None
                    mock_session.commit.return_value = None
                    
                    # 执行测试
                    result = await delete_category(
                        project_id=1,
                        category_id=1,
                        current_user={"id": 1, "state": 1},
                        session=mock_session
                    )
                    
                    # 验证结果
                    assert "分类删除成功" in result["message"]
                    assert "，已将3篇文章设置为未分类" in result["message"]
                    assert result["updated_articles_count"] == 3
                    mock_project_repo.get_project_by_id.assert_called_once_with(1)
                    mock_folder_repo.get_by_id.assert_called_once_with(1)
                    mock_post_repo.update_articles_folder_to_uncategorized.assert_called_once_with(1)
                    mock_session.delete.assert_called_once_with(sample_folder)
                    mock_session.commit.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delete_category_no_articles(self, mock_session, sample_project, sample_folder):
        """测试删除没有文章的分类"""
        # 准备测试数据
        with patch('src.controllers.project.ProjectRepository') as mock_project_repo_class:
            with patch('src.controllers.project.FolderRepository') as mock_folder_repo_class:
                with patch('src.controllers.project.PostRepository') as mock_post_repo_class:
                    mock_project_repo = AsyncMock()
                    mock_folder_repo = AsyncMock()
                    mock_post_repo = AsyncMock()
                    
                    mock_project_repo.get_project_by_id.return_value = sample_project
                    mock_folder_repo.get_by_id.return_value = sample_folder
                    mock_post_repo.update_articles_folder_to_uncategorized.return_value = 0  # 没有文章
                    
                    mock_project_repo_class.return_value = mock_project_repo
                    mock_folder_repo_class.return_value = mock_folder_repo
                    mock_post_repo_class.return_value = mock_post_repo
                    
                    # 模拟数据库操作
                    mock_session.delete.return_value = None
                    mock_session.commit.return_value = None
                    
                    # 执行测试
                    result = await delete_category(
                        project_id=1,
                        category_id=1,
                        current_user={"id": 1, "state": 1},
                        session=mock_session
                    )
                    
                    # 验证结果
                    assert result["message"] == "分类删除成功"
                    assert result["updated_articles_count"] == 0

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delete_category_permission_denied(self, mock_session, sample_project):
        """测试删除分类权限被拒绝"""
        # 准备测试数据
        with patch('src.controllers.project.ProjectRepository') as mock_project_repo_class:
            mock_project_repo = AsyncMock()
            mock_project_repo.get_project_by_id.return_value = sample_project
            mock_project_repo_class.return_value = mock_project_repo
            
            # 执行测试并验证异常
            with pytest.raises(HTTPException) as exc_info:
                await delete_category(
                    project_id=1,
                    category_id=1,
                    current_user={"id": 2, "state": 1},  # 不是项目所有者
                    session=mock_session
                )
            
            # 验证异常信息
            assert exc_info.value.status_code == 403
            assert exc_info.value.detail == "没有权限删除分类"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_category_service_error(self, mock_session, sample_project):
        """测试创建分类时服务错误"""
        # 准备测试数据
        with patch('src.controllers.project.ProjectRepository') as mock_project_repo_class:
            with patch('src.controllers.project.FolderRepository') as mock_folder_repo_class:
                mock_project_repo = AsyncMock()
                mock_folder_repo = AsyncMock()
                
                mock_project_repo.get_project_by_id.return_value = sample_project
                mock_folder_repo_class.return_value = mock_folder_repo
                mock_project_repo_class.return_value = mock_project_repo
                
                # 模拟数据库操作失败
                mock_session.add.return_value = None
                mock_session.commit.side_effect = Exception("数据库错误")
                mock_session.rollback.return_value = None
                
                # 执行测试并验证异常
                with pytest.raises(HTTPException) as exc_info:
                    await create_category(
                        project_id=1,
                        category_data={"name": "新分类"},
                        current_user={"id": 1, "state": 1},
                        session=mock_session
                    )
                
                # 验证异常信息
                assert exc_info.value.status_code == 500
                assert "创建分类失败" in exc_info.value.detail
                mock_session.rollback.assert_called_once()
