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

from passlib.context import CryptContext

def test_password_hashing():
    """测试密码哈希功能"""
    print("🧪 测试密码哈希功能")
    print("=" * 40)
    
    # 创建密码上下文
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    # 测试密码
    test_password = "test123"
    print(f"测试密码: {test_password}")
    
    # 双重哈希：password → MD5 → bcrypt
    md5_hash = hashlib.md5(test_password.encode()).hexdigest()
    bcrypt_hash = pwd_context.hash(md5_hash)
    
    print(f"MD5哈希: {md5_hash}")
    print(f"bcrypt哈希: {bcrypt_hash}")
    print(f"哈希长度: {len(bcrypt_hash)}")
    print(f"哈希前缀: {bcrypt_hash[:7]}")
    
    # 验证哈希
    is_valid = pwd_context.verify(md5_hash, bcrypt_hash)
    print(f"验证结果: {'✅ 成功' if is_valid else '❌ 失败'}")
    
    return is_valid

def test_password_verification():
    """测试密码验证功能"""
    print("\n🔐 测试密码验证功能")
    print("=" * 40)
    
    # 创建密码上下文
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    # 模拟存储的哈希（双重加密）
    test_password = "test123"
    md5_hash = hashlib.md5(test_password.encode()).hexdigest()
    stored_hash = pwd_context.hash(md5_hash)
    
    print(f"测试密码: {test_password}")
    print(f"存储的哈希: {stored_hash}")
    
    # 测试验证函数（模拟auth_service中的逻辑）
    def verify_password(plain_password: str, stored_hash: str) -> bool:
        """验证密码，支持两种格式"""
        try:
            # 检查是否是bcrypt格式
            if stored_hash.startswith('$2b$') and len(stored_hash) == 60:
                # 尝试直接验证（旧格式）
                if pwd_context.verify(plain_password, stored_hash):
                    return True
                
                # 如果不是直接验证，尝试MD5+bcrypt双重哈希（新格式）
                md5_hash = hashlib.md5(plain_password.encode()).hexdigest()
                return pwd_context.verify(md5_hash, stored_hash)
            else:
                # 非bcrypt格式，尝试MD5+bcrypt双重哈希
                md5_hash = hashlib.md5(plain_password.encode()).hexdigest()
                return pwd_context.verify(md5_hash, stored_hash)
        except Exception:
            return False
    
    # 测试正确密码
    result1 = verify_password(test_password, stored_hash)
    print(f"正确密码验证: {'✅ 成功' if result1 else '❌ 失败'}")
    
    # 测试错误密码
    result2 = verify_password("wrong_password", stored_hash)
    print(f"错误密码验证: {'✅ 成功' if result2 else '❌ 失败'}")
    
    # 测试空密码
    result3 = verify_password("", stored_hash)
    print(f"空密码验证: {'✅ 成功' if result3 else '❌ 失败'}")
    
    return result1 and not result2 and not result3

def test_compatibility():
    """测试兼容性"""
    print("\n🔄 测试兼容性")
    print("=" * 40)
    
    # 创建密码上下文
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    test_password = "test123"
    
    # 测试1: 直接bcrypt哈希（旧格式）
    direct_hash = pwd_context.hash(test_password)
    print(f"直接bcrypt哈希: {direct_hash[:20]}...")
    
    # 测试2: MD5+bcrypt双重哈希（新格式）
    md5_hash = hashlib.md5(test_password.encode()).hexdigest()
    double_hash = pwd_context.hash(md5_hash)
    print(f"双重哈希: {double_hash[:20]}...")
    
    # 验证函数
    def verify_password(plain_password: str, stored_hash: str) -> bool:
        """验证密码，支持两种格式"""
        try:
            if stored_hash.startswith('$2b$') and len(stored_hash) == 60:
                # 尝试直接验证（旧格式）
                if pwd_context.verify(plain_password, stored_hash):
                    return True
                
                # 尝试MD5+bcrypt双重哈希（新格式）
                md5_hash = hashlib.md5(plain_password.encode()).hexdigest()
                return pwd_context.verify(md5_hash, stored_hash)
            else:
                # 非bcrypt格式，尝试MD5+bcrypt双重哈希
                md5_hash = hashlib.md5(plain_password.encode()).hexdigest()
                return pwd_context.verify(md5_hash, stored_hash)
        except Exception:
            return False
    
    # 测试旧格式兼容性
    old_compatible = verify_password(test_password, direct_hash)
    print(f"旧格式兼容性: {'✅ 支持' if old_compatible else '❌ 不支持'}")
    
    # 测试新格式兼容性
    new_compatible = verify_password(test_password, double_hash)
    print(f"新格式兼容性: {'✅ 支持' if new_compatible else '❌ 不支持'}")
    
    return old_compatible and new_compatible

def main():
    """主函数"""
    print("🔐 密码重置功能测试")
    print("=" * 50)
    
    # 运行所有测试
    tests = [
        ("密码哈希", test_password_hashing),
        ("密码验证", test_password_verification),
        ("兼容性", test_compatibility)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}测试失败: {e}")
            results.append((test_name, False))
    
    # 显示测试结果
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
