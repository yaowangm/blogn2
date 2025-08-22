"""
文件夹仓库单元测试

测试FolderRepository的各种方法
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlmodel import select
from src.repositories.folder_repository import FolderRepository
from src.models.folder import Folder


class TestFolderRepository:
    """文件夹仓库测试类"""

    @pytest.fixture
    def mock_session(self):
        """模拟数据库会话"""
        session = AsyncMock()
        session.exec = AsyncMock()
        return session

    @pytest.fixture
    def repository(self, mock_session):
        """创建仓库实例"""
        return FolderRepository(mock_session)

    @pytest.fixture
    def mock_folder(self):
        """模拟文件夹"""
        return Folder(
            id=1,
            name="测试文件夹",
            parent=None,
            projectid=1,
            recordcount=5,
            postcount=3
        )

    @pytest.fixture
    def mock_folders(self):
        """模拟文件夹列表"""
        return [
            Folder(id=1, name="文件夹1", projectid=1, recordcount=5),
            Folder(id=2, name="文件夹2", projectid=1, recordcount=3),
            Folder(id=3, name="文件夹3", projectid=1, recordcount=0)
        ]

    @pytest.mark.asyncio
    async def test_get_by_id_success(self, repository, mock_session, mock_folder):
        """测试根据ID成功获取文件夹"""
        # 模拟查询结果
        mock_result = MagicMock()
        mock_result.first.return_value = mock_folder
        mock_session.exec.return_value = mock_result

        # 执行测试
        result = await repository.get_by_id(1)

        # 验证结果
        assert result is not None
        assert result.id == 1
        assert result.name == "测试文件夹"
        assert result.projectid == 1

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repository, mock_session):
        """测试根据ID获取不存在的文件夹"""
        # 模拟空结果
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result

        # 执行测试
        result = await repository.get_by_id(999)

        # 验证结果
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_project_id_success(self, repository, mock_session, mock_folders):
        """测试根据项目ID成功获取文件夹列表"""
        # 模拟查询结果
        mock_result = MagicMock()
        mock_result.all.return_value = mock_folders
        mock_session.exec.return_value = mock_result

        # 执行测试
        result = await repository.get_by_project_id(1)

        # 验证结果
        assert len(result) == 3
        assert result[0].name == "文件夹1"
        assert result[1].name == "文件夹2"
        assert result[2].name == "文件夹3"

    @pytest.mark.asyncio
    async def test_get_by_project_id_empty(self, repository, mock_session):
        """测试根据项目ID获取空文件夹列表"""
        # 模拟空结果
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.exec.return_value = mock_result

        # 执行测试
        result = await repository.get_by_project_id(999)

        # 验证结果
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_get_by_project_id_with_count_success(self, repository, mock_session, mock_folders):
        """测试根据项目ID获取文件夹及其文章数量"""
        # 模拟查询结果
        mock_result = MagicMock()
        mock_result.all.return_value = mock_folders
        mock_session.exec.return_value = mock_result

        # 执行测试
        result = await repository.get_by_project_id_with_count(1)

        # 验证结果
        assert len(result) == 3
        assert result[0]["id"] == 1
        assert result[0]["name"] == "文件夹1"
        assert result[0]["recordcount"] == 5
        assert result[1]["id"] == 2
        assert result[1]["recordcount"] == 3

    @pytest.mark.asyncio
    async def test_count_by_project_id_success(self, repository, mock_session, mock_folders):
        """测试统计项目下的文件夹数量"""
        # 模拟查询结果
        mock_result = MagicMock()
        mock_result.all.return_value = mock_folders
        mock_session.exec.return_value = mock_result

        # 执行测试
        count = await repository.count_by_project_id(1)

        # 验证结果
        assert count == 3

    @pytest.mark.asyncio
    async def test_count_by_project_id_zero(self, repository, mock_session):
        """测试统计项目下的文件夹数量为零"""
        # 模拟空结果
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.exec.return_value = mock_result

        # 执行测试
        count = await repository.count_by_project_id(999)

        # 验证结果
        assert count == 0
