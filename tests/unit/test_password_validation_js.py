"""
前端共享密码校验 JS 模块的静态检查

验证 src/static/js/utils/password-validation.js 存在且导出约定 API，
与后端 password_validation.py 规则一致（8–30 字符、大小写+数字、可打印 ASCII）。
"""

import pytest
from pathlib import Path


# 项目根目录（tests/unit/ -> 项目根）
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PASSWORD_VALIDATION_JS = PROJECT_ROOT / "src" / "static" / "js" / "utils" / "password-validation.js"


class TestPasswordValidationJs:
    """共享密码校验 JS 文件存在性与契约检查"""

    def test_password_validation_js_file_exists(self):
        """共享密码校验脚本文件存在"""
        assert PASSWORD_VALIDATION_JS.exists(), (
            f"Expected shared script at {PASSWORD_VALIDATION_JS}"
        )

    def test_exports_window_password_rule_error(self):
        """脚本向 window 导出 passwordRuleError，供各页与组件复用"""
        content = PASSWORD_VALIDATION_JS.read_text(encoding="utf-8")
        assert "passwordRuleError" in content, "Script should define passwordRuleError"
        assert "window.passwordRuleError" in content, (
            "Script should attach passwordRuleError to window for shared use"
        )

    def test_contains_rule_messages_aligned_with_backend(self):
        """脚本包含与后端一致的校验提示文案"""
        content = PASSWORD_VALIDATION_JS.read_text(encoding="utf-8")
        expected_messages = [
            "密码不能为空",
            "密码至少需要8个字符",
            "密码不能超过30个字符",
            "密码只能包含可打印 ASCII",
            "密码至少需要包含一个大写字母",
            "密码至少需要包含一个小写字母",
            "密码至少需要包含一个数字",
        ]
        for msg in expected_messages:
            assert msg in content, f"Expected rule message in shared script: {msg!r}"
