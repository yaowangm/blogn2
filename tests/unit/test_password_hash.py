"""password_hash 工具单元测试。"""

import hashlib

from src.utils.password_hash import hash_user_password, verify_user_password


class TestPasswordHash:
    def test_hash_and_verify_double_hash(self):
        plain = "password123"
        stored = hash_user_password(plain)
        assert stored.startswith("$2b$")
        assert verify_user_password(plain, stored) is True
        assert verify_user_password("wrong", stored) is False

    def test_verify_direct_bcrypt_legacy(self):
        plain = "legacy"
        from src.utils.password_hash import bcrypt_hash

        stored = bcrypt_hash(plain)
        assert verify_user_password(plain, stored) is True

    def test_verify_non_bcrypt_stored_hash(self):
        plain = "password123"
        md5_only = hashlib.md5(plain.encode()).hexdigest()
        assert verify_user_password(plain, md5_only) is False
