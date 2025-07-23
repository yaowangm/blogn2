"""
元数据控制器单元测试
"""

import pytest
from unittest.mock import AsyncMock, patch
from src.controllers.metadata import get_site_metadata
from src.services.metadata_service import MetadataService


class TestMetadataController:
    """元数据控制器测试类"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_site_metadata_success(self, mock_async_session):
        """测试获取网站元数据成功"""
        # 准备测试数据
        expected_metadata = {
            "site_name": "BlogN2",
            "description": "一个基于FastAPI的博客系统",
            "version": "1.0.0",
            "total_users": 100,
            "total_projects": 50,
            "total_blogs": 200
        }
        
        # 模拟服务方法
        mock_service = AsyncMock(spec=MetadataService)
        mock_service.get_metadata_dict.return_value = expected_metadata
        
        # 执行测试
        result = await get_site_metadata(metadata_service=mock_service)
        
        # 验证结果
        assert result == expected_metadata
        mock_service.get_metadata_dict.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_site_metadata_empty_data(self, mock_async_session):
        """测试获取网站元数据返回空数据"""
        # 准备测试数据
        expected_metadata = {
            "site_name": "",
            "description": "",
            "version": "",
            "total_users": 0,
            "total_projects": 0,
            "total_blogs": 0
        }
        
        # 模拟服务方法
        mock_service = AsyncMock(spec=MetadataService)
        mock_service.get_metadata_dict.return_value = expected_metadata
        
        # 执行测试
        result = await get_site_metadata(metadata_service=mock_service)
        
        # 验证结果
        assert result == expected_metadata
        assert result["total_users"] == 0
        assert result["total_projects"] == 0

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_site_metadata_service_error(self, mock_async_session):
        """测试获取网站元数据服务错误"""
        # 模拟服务方法抛出异常
        mock_service = AsyncMock(spec=MetadataService)
        mock_service.get_metadata_dict.side_effect = Exception("配置读取错误")
        
        # 执行测试并验证异常
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await get_site_metadata(metadata_service=mock_service)
        
        # 验证异常信息
        assert exc_info.value.status_code == 500
        assert "配置读取错误" in exc_info.value.detail

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_site_metadata_partial_data(self, mock_async_session):
        """测试获取网站元数据部分数据"""
        # 准备测试数据（部分字段为空）
        expected_metadata = {
            "site_name": "BlogN2",
            "description": None,
            "version": "1.0.0",
            "total_users": 100,
            "total_projects": None,
            "total_blogs": 200
        }
        
        # 模拟服务方法
        mock_service = AsyncMock(spec=MetadataService)
        mock_service.get_metadata_dict.return_value = expected_metadata
        
        # 执行测试
        result = await get_site_metadata(metadata_service=mock_service)
        
        # 验证结果
        assert result == expected_metadata
        assert result["site_name"] == "BlogN2"
        assert result["description"] is None
        assert result["total_projects"] is None 