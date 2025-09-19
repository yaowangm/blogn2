"""
设为个人介绍功能单元测试
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException
from src.controllers.user import set_user_intro
from src.repositories.user_repository import UserRepository
from src.repositories.project_item_repository import ProjectItemRepository
from src.database import User, ProjectItem
from src.utils.image_utils import ImageProcessor


class TestSetIntroFunctionality:
    """设为个人介绍功能测试类"""

    @pytest.fixture
    def mock_session(self):
        """模拟数据库会话"""
        return AsyncMock()

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

    @pytest.fixture
    def sample_article(self):
        """示例文章数据"""
        return ProjectItem(
            id=100,
            name="测试文章",
            userid=1,
            attachment="test_image.jpg",
            projectid=1
        )

    @pytest.fixture
    def current_user(self):
        """当前用户信息"""
        return {
            "id": 1,
            "name": "testuser",
            "state": 1
        }

    @pytest.fixture
    def request_data(self):
        """请求数据"""
        return {
            "article_id": 100
        }

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_set_user_intro_success(self, mock_session, sample_user, sample_article, current_user, request_data):
        """测试设置个人介绍成功"""
        # 模拟文件系统操作
        with patch('os.path.exists', return_value=True), \
             patch('os.makedirs'), \
             patch('os.path.join') as mock_join, \
             patch('src.utils.image_utils.ImageProcessor') as mock_image_processor_class, \
             patch('src.repositories.project_item_repository.ProjectItemRepository') as mock_project_item_repo_class, \
             patch('src.repositories.user_repository.UserRepository') as mock_user_repo_class:
            
            # 模拟路径拼接
            mock_join.side_effect = lambda *args: "/".join(args)
            
            # 模拟图片处理器
            mock_image_processor = AsyncMock()
            mock_image_processor.resize_and_save_image = AsyncMock()
            mock_image_processor_class.return_value = mock_image_processor
            
            # 模拟仓库
            mock_project_item_repo = AsyncMock()
            mock_project_item_repo.get_by_id = AsyncMock(return_value=sample_article)
            mock_project_item_repo_class.return_value = mock_project_item_repo
            
            mock_user_repo = AsyncMock()
            mock_user_repo.update_intropiid = AsyncMock(return_value=True)
            mock_user_repo_class.return_value = mock_user_repo
            
            # 模拟配置
            with patch('src.config.app.validate_app_config') as mock_config:
                mock_config.return_value = {
                    "upload_dir": "../pic/blogn_img/upload",
                    "avatar_dir": "../pic/blogn_img/userlogo"
                }
                
                # 执行测试
                result = await set_user_intro(
                    request_data=request_data,
                    current_user=current_user,
                    session=mock_session
                )
                
                # 验证结果
                assert result["success"] is True
                assert result["message"] == "个人介绍设置成功"
                assert result["article_id"] == 100
                assert result["article_title"] == "测试文章"
                
                # 验证仓库方法被调用
                mock_project_item_repo.get_by_id.assert_called_once_with(100)
                mock_user_repo.update_intropiid.assert_called_once_with(1, 100)
                
                # 验证图片处理被调用
                assert mock_image_processor.resize_and_save_image.call_count == 2  # 小头像和大头像

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_set_user_intro_article_not_found(self, mock_session, current_user, request_data):
        """测试设置个人介绍失败 - 文章不存在"""
        with patch('src.repositories.project_item_repository.ProjectItemRepository') as mock_project_item_repo_class:
            # 模拟文章不存在
            mock_project_item_repo = AsyncMock()
            mock_project_item_repo.get_by_id = AsyncMock(return_value=None)
            mock_project_item_repo_class.return_value = mock_project_item_repo
            
            # 执行测试并验证异常
            with pytest.raises(HTTPException) as exc_info:
                await set_user_intro(
                    request_data=request_data,
                    current_user=current_user,
                    session=mock_session
                )
            
            # 验证异常信息
            assert exc_info.value.status_code == 404
            assert exc_info.value.detail == "文章不存在"
            mock_project_item_repo.get_by_id.assert_called_once_with(100)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_set_user_intro_unauthorized_user(self, mock_session, sample_article, request_data):
        """测试设置个人介绍失败 - 无权限"""
        # 模拟不同用户
        current_user = {
            "id": 2,  # 不同的用户ID
            "name": "otheruser",
            "state": 1
        }
        
        with patch('src.repositories.project_item_repository.ProjectItemRepository') as mock_project_item_repo_class:
            # 模拟文章属于用户1
            mock_project_item_repo = AsyncMock()
            mock_project_item_repo.get_by_id = AsyncMock(return_value=sample_article)
            mock_project_item_repo_class.return_value = mock_project_item_repo
            
            # 执行测试并验证异常
            with pytest.raises(HTTPException) as exc_info:
                await set_user_intro(
                    request_data=request_data,
                    current_user=current_user,
                    session=mock_session
                )
            
            # 验证异常信息
            assert exc_info.value.status_code == 403
            assert exc_info.value.detail == "无权限设置此文章为个人介绍"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_set_user_intro_no_attachment(self, mock_session, current_user, request_data):
        """测试设置个人介绍失败 - 文章无附件"""
        # 模拟无附件的文章
        article_no_attachment = ProjectItem(
            id=100,
            name="测试文章",
            userid=1,
            attachment=None,  # 无附件
            projectid=1
        )
        
        with patch('src.repositories.project_item_repository.ProjectItemRepository') as mock_project_item_repo_class:
            # 模拟文章查询
            mock_project_item_repo = AsyncMock()
            mock_project_item_repo.get_by_id = AsyncMock(return_value=article_no_attachment)
            mock_project_item_repo_class.return_value = mock_project_item_repo
            
            # 执行测试并验证异常
            with pytest.raises(HTTPException) as exc_info:
                await set_user_intro(
                    request_data=request_data,
                    current_user=current_user,
                    session=mock_session
                )
            
            # 验证异常信息
            assert exc_info.value.status_code == 400
            assert exc_info.value.detail == "此文章没有附件图片，无法设为个人介绍"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_set_user_intro_missing_article_id(self, mock_session, current_user):
        """测试设置个人介绍失败 - 缺少文章ID"""
        # 模拟缺少article_id的请求
        request_data = {}
        
        # 执行测试并验证异常
        with pytest.raises(HTTPException) as exc_info:
            await set_user_intro(
                request_data=request_data,
                current_user=current_user,
                session=mock_session
            )
        
        # 验证异常信息
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "文章ID不能为空"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_set_user_intro_attachment_file_not_exists(self, mock_session, sample_article, current_user, request_data):
        """测试设置个人介绍 - 附件文件不存在但intropiid设置成功"""
        with patch('os.path.exists', return_value=False), \
             patch('os.makedirs'), \
             patch('os.path.join') as mock_join, \
             patch('src.utils.image_utils.ImageProcessor') as mock_image_processor_class, \
             patch('src.repositories.project_item_repository.ProjectItemRepository') as mock_project_item_repo_class, \
             patch('src.repositories.user_repository.UserRepository') as mock_user_repo_class:
            
            # 模拟路径拼接
            mock_join.side_effect = lambda *args: "/".join(args)
            
            # 模拟图片处理器
            mock_image_processor = AsyncMock()
            mock_image_processor.resize_and_save_image = AsyncMock()
            mock_image_processor_class.return_value = mock_image_processor
            
            # 模拟仓库
            mock_project_item_repo = AsyncMock()
            mock_project_item_repo.get_by_id = AsyncMock(return_value=sample_article)
            mock_project_item_repo_class.return_value = mock_project_item_repo
            
            mock_user_repo = AsyncMock()
            mock_user_repo.update_intropiid = AsyncMock(return_value=True)
            mock_user_repo_class.return_value = mock_user_repo
            
            # 模拟配置
            with patch('src.config.app.validate_app_config') as mock_config:
                mock_config.return_value = {
                    "upload_dir": "../pic/blogn_img/upload",
                    "avatar_dir": "../pic/blogn_img/userlogo"
                }
                
                # 执行测试
                result = await set_user_intro(
                    request_data=request_data,
                    current_user=current_user,
                    session=mock_session
                )
                
                # 验证结果 - 即使文件不存在，intropiid设置仍然成功
                assert result["success"] is True
                assert result["message"] == "个人介绍设置成功"
                assert result["article_id"] == 100
                assert result["article_title"] == "测试文章"
                
                # 验证仓库方法被调用
                mock_project_item_repo.get_by_id.assert_called_once_with(100)
                mock_user_repo.update_intropiid.assert_called_once_with(1, 100)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_set_user_intro_image_processing_failure(self, mock_session, sample_article, current_user, request_data):
        """测试设置个人介绍 - 图片处理失败但不影响intropiid设置"""
        with patch('os.path.exists', return_value=True), \
             patch('os.makedirs'), \
             patch('os.path.join') as mock_join, \
             patch('src.utils.image_utils.ImageProcessor') as mock_image_processor_class, \
             patch('src.repositories.project_item_repository.ProjectItemRepository') as mock_project_item_repo_class, \
             patch('src.repositories.user_repository.UserRepository') as mock_user_repo_class:
            
            # 模拟路径拼接
            mock_join.side_effect = lambda *args: "/".join(args)
            
            # 模拟图片处理器抛出异常
            mock_image_processor = AsyncMock()
            mock_image_processor.resize_and_save_image.side_effect = Exception("图片处理失败")
            mock_image_processor_class.return_value = mock_image_processor
            
            # 模拟仓库
            mock_project_item_repo = AsyncMock()
            mock_project_item_repo.get_by_id = AsyncMock(return_value=sample_article)
            mock_project_item_repo_class.return_value = mock_project_item_repo
            
            mock_user_repo = AsyncMock()
            mock_user_repo.update_intropiid = AsyncMock(return_value=True)
            mock_user_repo_class.return_value = mock_user_repo
            
            # 模拟配置
            with patch('src.config.app.validate_app_config') as mock_config:
                mock_config.return_value = {
                    "upload_dir": "../pic/blogn_img/upload",
                    "avatar_dir": "../pic/blogn_img/userlogo"
                }
                
                # 执行测试
                result = await set_user_intro(
                    request_data=request_data,
                    current_user=current_user,
                    session=mock_session
                )
                
                # 验证结果 - 即使图片处理失败，intropiid设置仍然成功
                assert result["success"] is True
                assert result["message"] == "个人介绍设置成功"
                assert result["article_id"] == 100
                assert result["article_title"] == "测试文章"
                
                # 验证仓库方法被调用
                mock_project_item_repo.get_by_id.assert_called_once_with(100)
                mock_user_repo.update_intropiid.assert_called_once_with(1, 100)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_set_user_intro_database_error(self, mock_session, sample_article, current_user, request_data):
        """测试设置个人介绍失败 - 数据库错误"""
        with patch('os.path.exists', return_value=True), \
             patch('os.makedirs'), \
             patch('os.path.join') as mock_join, \
             patch('src.utils.image_utils.ImageProcessor') as mock_image_processor_class, \
             patch('src.repositories.project_item_repository.ProjectItemRepository') as mock_project_item_repo_class, \
             patch('src.repositories.user_repository.UserRepository') as mock_user_repo_class:
            
            # 模拟路径拼接
            mock_join.side_effect = lambda *args: "/".join(args)
            
            # 模拟图片处理器
            mock_image_processor = AsyncMock()
            mock_image_processor.resize_and_save_image = AsyncMock()
            mock_image_processor_class.return_value = mock_image_processor
            
            # 模拟文章查询
            mock_project_item_repo = AsyncMock()
            mock_project_item_repo.get_by_id = AsyncMock(return_value=sample_article)
            mock_project_item_repo_class.return_value = mock_project_item_repo
            
            # 模拟用户更新失败
            mock_user_repo = AsyncMock()
            mock_user_repo.update_intropiid = AsyncMock(return_value=False)
            mock_user_repo_class.return_value = mock_user_repo
            
            # 模拟配置
            with patch('src.config.app.validate_app_config') as mock_config:
                mock_config.return_value = {
                    "upload_dir": "../pic/blogn_img/upload",
                    "avatar_dir": "../pic/blogn_img/userlogo"
                }
                
                # 执行测试并验证异常
                with pytest.raises(HTTPException) as exc_info:
                    await set_user_intro(
                        request_data=request_data,
                        current_user=current_user,
                        session=mock_session
                    )
                
                # 验证异常信息
                assert exc_info.value.status_code == 500
                assert exc_info.value.detail == "更新用户intropiid失败"