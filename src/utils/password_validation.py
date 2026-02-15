"""
密码字符串校验：注册与重置密码共用规则。
- 长度 8–30 个字符
- 至少包含大写字母、小写字母、数字
- 仅允许可打印 ASCII（0x20–0x7E）
"""

# 可打印 ASCII 范围
_PRINTABLE_ASCII_MIN = 0x20
_PRINTABLE_ASCII_MAX = 0x7E

PASSWORD_MIN_LEN = 8
PASSWORD_MAX_LEN = 30


def validate_password(password: str) -> None:
    """
    校验密码是否符合规则。不符合时抛出 ValueError，消息为中文说明。
    """
    if not password:
        raise ValueError("密码不能为空")
    if len(password) < PASSWORD_MIN_LEN:
        raise ValueError("密码至少需要8个字符")
    if len(password) > PASSWORD_MAX_LEN:
        raise ValueError("密码不能超过30个字符")
    if not all(_PRINTABLE_ASCII_MIN <= ord(c) <= _PRINTABLE_ASCII_MAX for c in password):
        raise ValueError("密码只能包含可打印 ASCII 字符（空格到波浪号 ~）")
    if not any(c.isupper() for c in password):
        raise ValueError("密码至少需要包含一个大写字母")
    if not any(c.islower() for c in password):
        raise ValueError("密码至少需要包含一个小写字母")
    if not any(c.isdigit() for c in password):
        raise ValueError("密码至少需要包含一个数字")
