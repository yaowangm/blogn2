"""
权限管理器简化测试
只测试实际存在且工作正常的方法
"""

import pytest

from src.utils.permission_manager import PermissionManager


class TestPermissionManagerSimple:
    """权限管理器简化测试类"""
    
    @pytest.fixture
    def permission_manager(self):
        """创建权限管理器实例"""
        return PermissionManager()
    
    @pytest.fixture
    def admin_user(self):
        """创建管理员用户"""
        return {
            "id": 1,
            "name": "admin",
            "state": 10,
            "role": "admin"
        }
    
    @pytest.fixture
    def regular_user(self):
        """创建普通用户"""
        return {
            "id": 2,
            "name": "user",
            "state": 1,
            "role": "user"
        }
    
    @pytest.fixture
    def frozen_user(self):
        """创建冻结用户"""
        return {
            "id": 3,
            "name": "frozen",
            "state": 0,
            "role": "frozen"
        }

    def test_get_user_role_admin(self, permission_manager):
        """测试获取管理员角色"""
        role = permission_manager.get_user_role(10)
        assert role == "admin"

    def test_get_user_role_user(self, permission_manager):
        """测试获取普通用户角色"""
        role = permission_manager.get_user_role(1)
        assert role == "user"

    def test_get_user_role_frozen(self, permission_manager):
        """测试获取冻结用户角色"""
        role = permission_manager.get_user_role(0)
        assert role == "frozen"

    def test_get_user_role_unknown(self, permission_manager):
        """测试获取未知用户角色"""
        role = permission_manager.get_user_role(5)
        assert role == "unknown"

    def test_is_admin_true(self, permission_manager):
        """测试管理员判断 - 是管理员"""
        assert permission_manager.is_admin(10) is True

    def test_is_admin_false(self, permission_manager):
        """测试管理员判断 - 不是管理员"""
        assert permission_manager.is_admin(1) is False
        assert permission_manager.is_admin(0) is False
        assert permission_manager.is_admin(5) is False

    def test_is_frozen_true(self, permission_manager):
        """测试冻结用户判断 - 是冻结用户"""
        assert permission_manager.is_frozen(0) is True

    def test_is_frozen_false(self, permission_manager):
        """测试冻结用户判断 - 不是冻结用户"""
        assert permission_manager.is_frozen(10) is False
        assert permission_manager.is_frozen(1) is False
        assert permission_manager.is_frozen(5) is False

    def test_can_manage_users_admin(self, permission_manager, admin_user):
        """测试管理员管理用户权限"""
        assert permission_manager.can_manage_users(admin_user) is True

    def test_can_manage_users_user(self, permission_manager, regular_user):
        """测试普通用户管理用户权限"""
        assert permission_manager.can_manage_users(regular_user) is False

    def test_can_manage_users_frozen(self, permission_manager, frozen_user):
        """测试冻结用户管理用户权限"""
        assert permission_manager.can_manage_users(frozen_user) is False

    def test_can_manage_system_admin(self, permission_manager, admin_user):
        """测试管理员管理系统权限"""
        assert permission_manager.can_manage_system(admin_user) is True

    def test_can_manage_system_user(self, permission_manager, regular_user):
        """测试普通用户管理系统权限"""
        assert permission_manager.can_manage_system(regular_user) is False

    def test_can_manage_system_frozen(self, permission_manager, frozen_user):
        """测试冻结用户管理系统权限"""
        assert permission_manager.can_manage_system(frozen_user) is False
