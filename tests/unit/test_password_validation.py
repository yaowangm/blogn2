"""
密码校验工具单元测试：8–30 字符、大小写+数字、可打印 ASCII
"""

import pytest
from src.utils.password_validation import validate_password, PASSWORD_MIN_LEN, PASSWORD_MAX_LEN


class TestValidatePassword:
    """validate_password 规则测试"""

    def test_accept_valid_password(self):
        validate_password("Abcd1234")
        validate_password("Password1")
        validate_password("aB3" + "x" * 24)  # 27 chars

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="密码不能为空"):
            validate_password("")

    def test_too_short_raises(self):
        with pytest.raises(ValueError, match="至少需要8个字符"):
            validate_password("Abc1234")  # 7

    def test_too_long_raises(self):
        with pytest.raises(ValueError, match="不能超过30个字符"):
            validate_password("Abcd1234" + "x" * 23)  # 31

    def test_no_uppercase_raises(self):
        with pytest.raises(ValueError, match="至少需要包含一个大写字母"):
            validate_password("abcd1234")

    def test_no_lowercase_raises(self):
        with pytest.raises(ValueError, match="至少需要包含一个小写字母"):
            validate_password("ABCD1234")

    def test_no_digit_raises(self):
        with pytest.raises(ValueError, match="至少需要包含一个数字"):
            validate_password("Abcdefgh")

    def test_non_printable_ascii_raises(self):
        with pytest.raises(ValueError, match="只能包含可打印 ASCII"):
            validate_password("Abcd123\x00")
        with pytest.raises(ValueError, match="只能包含可打印 ASCII"):
            validate_password("Abcd123\n")

    def test_printable_ascii_boundaries_accept(self):
        validate_password("Abcd123 ")   # 0x20 space
        validate_password("Abcd123~")   # 0x7E tilde
