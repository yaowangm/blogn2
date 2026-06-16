#!/usr/bin/env python3
"""
MD5到bcrypt双重哈希迁移脚本
将现有的MD5哈希值转换为MD5+bcrypt双重哈希
"""

import sys
import os
import hashlib
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from src.utils.password_hash import bcrypt_hash, hash_user_password, verify_user_password
from sqlmodel import create_engine, Session, select
from src.models.user import User

# 加载环境变量
load_dotenv()

def is_md5_hash(hash_value: str) -> bool:
    """判断是否为MD5哈希"""
    return len(hash_value) == 32 and all(c in '0123456789abcdef' for c in hash_value)

def is_bcrypt_hash(hash_value: str) -> bool:
    """判断是否为bcrypt哈希"""
    return hash_value.startswith('$2b$') and len(hash_value) == 60

def convert_md5_to_bcrypt(md5_hash: str) -> str:
    """将MD5哈希转换为bcrypt哈希"""
    return bcrypt_hash(md5_hash)

def verify_double_hash(plain_password: str, stored_hash: str) -> bool:
    """验证双重哈希密码"""
    return verify_user_password(plain_password, stored_hash)

def migrate_to_double_hash():
    """执行双重哈希迁移"""
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        print("❌ DATABASE_URL 环境变量未设置")
        return False
    
    # 创建同步引擎
    sync_engine = create_engine(
        DATABASE_URL.replace("+asyncpg", "+psycopg2"),
        echo=False
    )
    
    print("   开始MD5到bcrypt双重哈希迁移...")
    
    with Session(sync_engine) as session:
        try:
            # 获取所有用户
            statement = select(User)
            users = session.exec(statement).all()
            
            if not users:
                print("ℹ️  没有找到用户数据")
                return True
            
            print(f"📊 找到 {len(users)} 个用户，开始迁移...")
            
            migrated_count = 0
            skipped_count = 0
            failed_count = 0
            
            for user in users:
                try:
                    current_password = user.password
                    
                    # 检查当前密码格式
                    if is_bcrypt_hash(current_password):
                        print(f"  ✅ 用户 {user.name} 已经是bcrypt格式，跳过")
                        skipped_count += 1
                        continue
                    
                    if is_md5_hash(current_password):
                        print(f"     用户 {user.name} 密码是MD5格式，转换为双重哈希...")
                        
                        # 转换为bcrypt哈希
                        new_hash = convert_md5_to_bcrypt(current_password)
                        
                        # 更新密码字段
                        user.password = new_hash
                        user.lastupdate = datetime.now()
                        
                        session.add(user)
                        migrated_count += 1
                        
                        print(f"    ✅ 转换完成")
                    else:
                        print(f"  ⚠️  用户 {user.name} 密码格式未知: {current_password[:10]}...")
                        failed_count += 1
                        
                except Exception as e:
                    print(f"  ❌ 用户 {user.name} 迁移失败: {e}")
                    failed_count += 1
            
            # 提交更改
            session.commit()
            
            print(f"\n🎉 双重哈希迁移完成！")
            print(f"  ✅ 成功迁移: {migrated_count} 个用户")
            print(f"  ⏭️  跳过(已是bcrypt): {skipped_count} 个用户")
            print(f"  ❌ 迁移失败: {failed_count} 个用户")
            
            return True
            
        except Exception as e:
            print(f"❌ 迁移失败: {e}")
            session.rollback()
            return False

def test_migration():
    """测试迁移后的密码验证"""
    print("\n🧪 测试迁移后的密码验证...")
    
    # 测试用例
    test_password = "test123"
    test_md5 = hashlib.md5(test_password.encode()).hexdigest()
    test_bcrypt = convert_md5_to_bcrypt(test_md5)
    
    print(f"测试密码: {test_password}")
    print(f"MD5哈希: {test_md5}")
    print(f"bcrypt哈希: {test_bcrypt}")
    
    # 验证
    is_valid = verify_double_hash(test_password, test_bcrypt)
    print(f"验证结果: {'✅ 成功' if is_valid else '❌ 失败'}")
    
    return is_valid

def main():
    """主函数"""
    print("   MD5到bcrypt双重哈希迁移工具")
    print("=" * 60)
    
    # 确认操作
    print("⚠️  此操作将:")
    print("  1. 将现有MD5哈希转换为bcrypt哈希")
    print("  2. 形成MD5→bcrypt的双重哈希链")
    print("  3. 保持现有用户登录功能")
    print("  4. 提升密码存储安全性")
    
    confirm = input("\n是否继续？(y/N): ")
    if confirm.lower() != 'y':
        print("❌ 操作已取消")
        return
    
    # 执行迁移
    if migrate_to_double_hash():
        print("\n✅ 迁移成功完成！")
        
        # 测试验证
        if test_migration():
            print("✅ 密码验证测试通过！")
        else:
            print("❌ 密码验证测试失败！")
            
    else:
        print("❌ 迁移失败")
        sys.exit(1)

if __name__ == "__main__":
    main()
