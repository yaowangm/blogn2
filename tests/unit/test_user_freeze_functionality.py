"""
用户冻结功能单元测试

测试用户冻结和恢复功能的API端点、服务方法和权限检查
"""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException
from src.controllers.user import freeze_user, restore_user
from src.services.user_service import UserService
from src.database import User


class TestUserFreezeFunctionality:
    """用户冻结功能测试类"""

    @pytest.fixture
    def mock_user_service(self):
        """模拟用户服务"""
        return AsyncMock(spec=UserService)

    @pytest.fixture
    def normal_user(self):
        """普通用户"""
        return User(
            id=2,
            name="normaluser",
            email="normal@example.com",
            state=1,  # 正常状态
            regtime=None,
            projectid=None,
            intropiid=None,
            lastupdate=None
        )

    @pytest.fixture
    def admin_user(self):
        """管理员用户"""
        return User(
            id=1,
            name="admin",
            email="admin@example.com",
            state=10,  # 管理员状态
            regtime=None,
            projectid=None,
            intropiid=None,
            lastupdate=None
        )

    @pytest.fixture
    def frozen_user(self):
        """冻结用户"""
        return User(
            id=3,
            name="frozenuser",
            email="frozen@example.com",
            state=2,  # 冻结状态
            regtime=None,
            projectid=None,
            intropiid=None,
            lastupdate=None
        )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_freeze_user_success(self, mock_user_service, normal_user):
        """测试成功冻结普通用户"""
        # 准备测试数据
        mock_user_service.get_user_by_id.return_value = normal_user
        mock_user_service.freeze_user.return_value = None
        
        # 执行测试
        result = await freeze_user(
            user_id=2,
            user_service=mock_user_service,
            current_user={"id": 1, "state": 10}  # 管理员用户
        )
        
        # 验证结果
        assert result == {"message": "用户冻结成功"}
        mock_user_service.get_user_by_id.assert_called_once_with(2)
        mock_user_service.freeze_user.assert_called_once_with(2)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_freeze_user_not_found(self, mock_user_service):
        """测试冻结不存在的用户"""
        # 准备测试数据
        mock_user_service.get_user_by_id.return_value = None
        
        # 执行测试并验证异常
        with pytest.raises(HTTPException) as exc_info:
            await freeze_user(
                user_id=999,
                user_service=mock_user_service,
                current_user={"id": 1, "state": 10}
            )
        
        # 验证异常信息
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "用户不存在"
        mock_user_service.get_user_by_id.assert_called_once_with(999)
        mock_user_service.freeze_user.assert_not_called()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_freeze_admin_user_forbidden(self, mock_user_service, admin_user):
        """测试冻结管理员用户被禁止"""
        # 准备测试数据
        mock_user_service.get_user_by_id.return_value = admin_user
        
        # 执行测试并验证异常
        with pytest.raises(HTTPException) as exc_info:
            await freeze_user(
                user_id=1,
                user_service=mock_user_service,
                current_user={"id": 2, "state": 10}  # 另一个管理员
            )
        
        # 验证异常信息
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "不能冻结管理员用户"
        mock_user_service.get_user_by_id.assert_called_once_with(1)
        mock_user_service.freeze_user.assert_not_called()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_restore_user_success(self, mock_user_service, frozen_user):
        """测试成功恢复冻结用户"""
        # 准备测试数据
        mock_user_service.get_user_by_id.return_value = frozen_user
        mock_user_service.restore_user.return_value = None
        
        # 执行测试
        result = await restore_user(
            user_id=3,
            user_service=mock_user_service,
            current_user={"id": 1, "state": 10}  # 管理员用户
        )
        
        # 验证结果
        assert result == {"message": "用户恢复成功"}
        mock_user_service.get_user_by_id.assert_called_once_with(3)
        mock_user_service.restore_user.assert_called_once_with(3)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_restore_user_not_found(self, mock_user_service):
        """测试恢复不存在的用户"""
        # 准备测试数据
        mock_user_service.get_user_by_id.return_value = None
        
        # 执行测试并验证异常
        with pytest.raises(HTTPException) as exc_info:
            await restore_user(
                user_id=999,
                user_service=mock_user_service,
                current_user={"id": 1, "state": 10}
            )
        
        # 验证异常信息
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "用户不存在"
        mock_user_service.get_user_by_id.assert_called_once_with(999)
        mock_user_service.restore_user.assert_not_called()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_freeze_user_service_error(self, mock_user_service, normal_user):
        """测试冻结用户时服务错误"""
        # 准备测试数据
        mock_user_service.get_user_by_id.return_value = normal_user
        mock_user_service.freeze_user.side_effect = Exception("数据库错误")
        
        # 执行测试并验证异常
        with pytest.raises(HTTPException) as exc_info:
            await freeze_user(
                user_id=2,
                user_service=mock_user_service,
                current_user={"id": 1, "state": 10}
            )
        
        # 验证异常信息
        assert exc_info.value.status_code == 500
        assert "数据库错误" in exc_info.value.detail
        mock_user_service.get_user_by_id.assert_called_once_with(2)
        mock_user_service.freeze_user.assert_called_once_with(2)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_restore_user_service_error(self, mock_user_service, frozen_user):
        """测试恢复用户时服务错误"""
        # 准备测试数据
        mock_user_service.get_user_by_id.return_value = frozen_user
        mock_user_service.restore_user.side_effect = Exception("数据库错误")
        
        # 执行测试并验证异常
        with pytest.raises(HTTPException) as exc_info:
            await restore_user(
                user_id=3,
                user_service=mock_user_service,
                current_user={"id": 1, "state": 10}
            )
        
        # 验证异常信息
        assert exc_info.value.status_code == 500
        assert "数据库错误" in exc_info.value.detail
        mock_user_service.get_user_by_id.assert_called_once_with(3)
        mock_user_service.restore_user.assert_called_once_with(3)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_freeze_already_frozen_user(self, mock_user_service):
        """测试冻结已经冻结的用户"""
        # 准备测试数据 - 已经是冻结状态
        already_frozen_user = User(
            id=4,
            name="alreadyfrozen",
            email="alreadyfrozen@example.com",
            state=2,  # 已经是冻结状态
            regtime=None,
            projectid=None,
            intropiid=None,
            lastupdate=None
        )
        mock_user_service.get_user_by_id.return_value = already_frozen_user
        mock_user_service.freeze_user.return_value = None
        
        # 执行测试 - 应该成功，因为可以重复冻结
        result = await freeze_user(
            user_id=4,
            user_service=mock_user_service,
            current_user={"id": 1, "state": 10}
        )
        
        # 验证结果
        assert result == {"message": "用户冻结成功"}
        mock_user_service.get_user_by_id.assert_called_once_with(4)
        mock_user_service.freeze_user.assert_called_once_with(4)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_restore_normal_user(self, mock_user_service, normal_user):
        """测试恢复正常用户"""
        # 准备测试数据 - 已经是正常状态
        mock_user_service.get_user_by_id.return_value = normal_user
        mock_user_service.restore_user.return_value = None
        
        # 执行测试 - 应该成功，因为可以重复恢复
        result = await restore_user(
            user_id=2,
            user_service=mock_user_service,
            current_user={"id": 1, "state": 10}
        )
        
        # 验证结果
        assert result == {"message": "用户恢复成功"}
        mock_user_service.get_user_by_id.assert_called_once_with(2)
        mock_user_service.restore_user.assert_called_once_with(2)
