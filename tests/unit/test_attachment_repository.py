"""
AttachmentRepository单元测试
测试附件仓库的数据访问方法
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlmodel.ext.asyncio.session import AsyncSession
from src.repositories.attachment_repository import AttachmentRepository
from src.models.attachment import Attachment
from datetime import datetime


class TestAttachmentRepository:
    """AttachmentRepository测试类"""
    
    @pytest.fixture
    def mock_session(self):
        """创建模拟的数据库会话"""
        session = AsyncMock(spec=AsyncSession)
        return session
    
    @pytest.fixture
    def sample_attachments(self):
        """创建示例附件数据"""
        return [
            Attachment(
                id=1,
                parentid=123,
                amtype="image",
                comment="测试图片1",
                linkstr="/upload/test1.jpg",
                createtime=datetime(2024, 1, 1, 10, 0, 0),
                updatetime=datetime(2024, 1, 1, 10, 0, 0)
            ),
            Attachment(
                id=2,
                parentid=123,
                amtype="image",
                comment="测试图片2",
                linkstr="/upload/test2.jpg",
                createtime=datetime(2024, 1, 2, 10, 0, 0),
                updatetime=datetime(2024, 1, 2, 10, 0, 0)
            )
        ]
    
    async def test_get_by_project_item_id(self, mock_session, sample_attachments):
        """测试根据项目项ID获取附件"""
        # 模拟查询结果
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = sample_attachments
        mock_session.execute.return_value = mock_result
        
        # 创建仓库实例
        repo = AttachmentRepository(mock_session)
        
        # 执行测试
        result = await repo.get_by_project_item_id(123)
        
        # 验证结果
        assert len(result) == 2
        assert result[0].id == 1
        assert result[1].id == 2
        
        # 验证查询被调用
        mock_session.execute.assert_called_once()
    
    async def test_get_by_id(self, mock_session, sample_attachments):
        """测试根据ID获取单个附件"""
        # 模拟查询结果
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_attachments[0]
        mock_session.execute.return_value = mock_result
        
        # 创建仓库实例
        repo = AttachmentRepository(mock_session)
        
        # 执行测试
        result = await repo.get_by_id(1)
        
        # 验证结果
        assert result is not None
        assert result.id == 1
        assert result.parentid == 123
        
        # 验证查询被调用
        mock_session.execute.assert_called_once()
    
    async def test_get_by_id_not_found(self, mock_session):
        """测试根据ID获取附件时未找到"""
        # 模拟查询结果为空
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        
        # 创建仓库实例
        repo = AttachmentRepository(mock_session)
        
        # 执行测试
        result = await repo.get_by_id(999)
        
        # 验证结果
        assert result is None
        mock_session.execute.assert_called_once()
    
    async def test_create(self, mock_session, sample_attachments):
        """测试创建附件"""
        new_attachment = Attachment(
            id=3,
            parentid=123,
            amtype="image",
            comment="新图片",
            linkstr="/upload/new.jpg"
        )
        
        # 创建仓库实例
        repo = AttachmentRepository(mock_session)
        
        # 执行测试
        result = await repo.create(new_attachment)
        
        # 验证结果
        assert result == new_attachment
        
        # 验证会话操作
        mock_session.add.assert_called_once_with(new_attachment)
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(new_attachment)
    
    async def test_delete_success(self, mock_session, sample_attachments):
        """测试成功删除附件"""
        # 模拟get_by_id返回附件
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_attachments[0]
        mock_session.execute.return_value = mock_result
        
        # 创建仓库实例
        repo = AttachmentRepository(mock_session)
        
        # 执行测试
        result = await repo.delete(1)
        
        # 验证结果
        assert result is True
        
        # 验证会话操作
        mock_session.delete.assert_called_once_with(sample_attachments[0])
        mock_session.commit.assert_called_once()
    
    async def test_delete_not_found(self, mock_session):
        """测试删除不存在的附件"""
        # 模拟get_by_id返回None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        
        # 创建仓库实例
        repo = AttachmentRepository(mock_session)
        
        # 执行测试
        result = await repo.delete(999)
        
        # 验证结果
        assert result is False
        
        # 验证没有删除操作
        mock_session.delete.assert_not_called()
        mock_session.commit.assert_not_called()
    
    async def test_update_success(self, mock_session, sample_attachments):
        """测试成功更新附件"""
        # 模拟get_by_id返回附件
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_attachments[0]
        mock_session.execute.return_value = mock_result
        
        # 创建仓库实例
        repo = AttachmentRepository(mock_session)
        
        # 执行测试
        result = await repo.update(1, comment="更新后的描述")
        
        # 验证结果
        assert result is not None
        assert result.comment == "更新后的描述"
        
        # 验证会话操作
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(sample_attachments[0])
    
    async def test_update_not_found(self, mock_session):
        """测试更新不存在的附件"""
        # 模拟get_by_id返回None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        
        # 创建仓库实例
        repo = AttachmentRepository(mock_session)
        
        # 执行测试
        result = await repo.update(999, comment="新描述")
        
        # 验证结果
        assert result is None
        
        # 验证没有更新操作
        mock_session.commit.assert_not_called()
        mock_session.refresh.assert_not_called()
    
    async def test_get_by_project_item_id_ordering(self, mock_session, sample_attachments):
        """测试根据项目项ID获取附件时的排序"""
        # 模拟查询结果
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = sample_attachments
        mock_session.execute.return_value = mock_result
        
        # 创建仓库实例
        repo = AttachmentRepository(mock_session)
        
        # 执行测试
        await repo.get_by_project_item_id(123)
        
        # 验证查询被调用
        mock_session.execute.assert_called_once()
        call_args = mock_session.execute.call_args[0][0]
        
        # 验证查询包含排序
        assert "createtime" in str(call_args)
