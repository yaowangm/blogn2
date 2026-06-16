#!/usr/bin/env python3
"""
密码重置功能测试脚本
用于验证密码重置和验证功能是否正常工作
"""

import sys
import hashlib
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.password_hash import (
    bcrypt_hash,
    hash_user_password,
    verify_user_password,
)


def test_password_hashing():
    """测试密码哈希功能"""
    print("🧪 测试密码哈希功能")
    print("=" * 40)

    test_password = "test123"
    print(f"测试密码: {test_password}")

    md5_hash = hashlib.md5(test_password.encode()).hexdigest()
    stored_hash = hash_user_password(test_password)

    print(f"MD5哈希: {md5_hash}")
    print(f"bcrypt哈希: {stored_hash}")
    print(f"哈希长度: {len(stored_hash)}")
    print(f"哈希前缀: {stored_hash[:7]}")

    is_valid = verify_user_password(test_password, stored_hash)
    print(f"验证结果: {'✅ 成功' if is_valid else '❌ 失败'}")

    return is_valid


def test_password_verification():
    """测试密码验证功能"""
    print("\n🔐 测试密码验证功能")
    print("=" * 40)

    test_password = "test123"
    stored_hash = hash_user_password(test_password)

    print(f"测试密码: {test_password}")
    print(f"存储的哈希: {stored_hash}")

    result1 = verify_user_password(test_password, stored_hash)
    print(f"正确密码验证: {'✅ 成功' if result1 else '❌ 失败'}")

    result2 = verify_user_password("wrong_password", stored_hash)
    print(f"错误密码验证: {'✅ 成功' if result2 else '❌ 失败'}")

    result3 = verify_user_password("", stored_hash)
    print(f"空密码验证: {'✅ 成功' if result3 else '❌ 失败'}")

    return result1 and not result2 and not result3


def test_compatibility():
    """测试兼容性"""
    print("\n🔄 测试兼容性")
    print("=" * 40)

    test_password = "test123"

    direct_hash = bcrypt_hash(test_password)
    print(f"直接bcrypt哈希: {direct_hash[:20]}...")

    double_hash = hash_user_password(test_password)
    print(f"双重哈希: {double_hash[:20]}...")

    old_compatible = verify_user_password(test_password, direct_hash)
    print(f"旧格式兼容性: {'✅ 支持' if old_compatible else '❌ 不支持'}")

    new_compatible = verify_user_password(test_password, double_hash)
    print(f"新格式兼容性: {'✅ 支持' if new_compatible else '❌ 不支持'}")

    return old_compatible and new_compatible


def main():
    """主函数"""
    print("🔐 密码重置功能测试")
    print("=" * 50)

    tests = [
        ("密码哈希", test_password_hashing),
        ("密码验证", test_password_verification),
        ("兼容性", test_compatibility),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}测试失败: {e}")
            results.append((test_name, False))

    print("\n📊 测试结果汇总")
    print("=" * 50)

    all_passed = True
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False

    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 所有测试通过！密码重置功能正常工作")
    else:
        print("❌ 部分测试失败，请检查相关功能")

    return all_passed


if __name__ == "__main__":
    main()
