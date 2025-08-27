#!/usr/bin/env python3
"""
用户密码重置脚本
通过命令行参数传入用户ID来重置密码
使用与登录系统相同的双重加密方式（MD5 + bcrypt）

使用方法:
    python scripts/reset_user_password.py <用户ID>
    
示例:
    python scripts/reset_user_password.py 1
"""

import sys
import os
import hashlib
import getpass
import argparse
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from passlib.context import CryptContext
from sqlmodel import create_engine, Session, select
from src.models.user import User

# 加载环境变量
load_dotenv()

# 创建密码上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_database_connection():
    """获取数据库连接"""
    try:
        # 从环境变量获取数据库URL
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            print("❌ 错误: 未设置 DATABASE_URL 环境变量")
            print("请在 .env 文件中配置数据库连接信息")
            sys.exit(1)
        
        # 创建同步引擎（用于密码重置操作）
        sync_engine = create_engine(
            database_url.replace("+asyncpg", "+psycopg2"),
            echo=False  # 不显示SQL语句
        )
        
        return sync_engine
        
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        sys.exit(1)

def find_user_by_id(session: Session, user_id: int) -> User:
    """通过用户ID查找用户"""
    try:
        user = session.exec(select(User).where(User.id == user_id)).first()
        return user
        
    except Exception as e:
        print(f"❌ 查找用户时出错: {e}")
        return None

def hash_password(password: str) -> str:
    """
    哈希密码：password → MD5 → bcrypt
    与登录系统使用相同的加密方式
    """
    md5_hash = hashlib.md5(password.encode()).hexdigest()
    return pwd_context.hash(md5_hash)

def verify_password(plain_password: str, stored_hash: str) -> bool:
    """
    验证密码，支持两种格式：
    1. 直接bcrypt哈希（旧格式）
    2. MD5+bcrypt双重哈希（新格式）
    """
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

def reset_user_password(session: Session, user: User, new_password: str) -> bool:
    """重置用户密码"""
    try:
        # 生成新的密码哈希
        new_hash = hash_password(new_password)
        
        # 更新用户密码
        user.password = new_hash
        user.lastupdate = datetime.now()
        
        # 保存到数据库
        session.add(user)
        session.commit()
        
        return True
        
    except Exception as e:
        print(f"❌ 重置密码失败: {e}")
        session.rollback()
        return False

def display_user_info(user: User):
    """显示用户信息"""
    print(f"\n📋 用户信息:")
    print(f"  ID: {user.id}")
    print(f"  用户名: {user.name}")
    print(f"  邮箱: {user.email}")
    print(f"  状态: {'正常' if user.state == 1 else '冻结' if user.state == 0 else f'未知({user.state})'}")
    print(f"  注册时间: {user.regtime}")
    print(f"  最后更新: {user.lastupdate or '从未'}")
    print(f"  最后登录IP: {user.iplog or '从未'}")
    print(f"  积分: {user.point}")

def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="用户密码重置工具")
    parser.add_argument("user_id", type=int, help="要重置密码的用户ID")
    parser.add_argument("--force", "-f", action="store_true", help="跳过确认提示，直接重置密码")
    parser.add_argument("--password", "-p", help="直接指定新密码（不推荐，密码会显示在命令行历史中）")
    
    args = parser.parse_args()
    
    print("🔐 用户密码重置工具")
    print("=" * 50)
    print(f"目标用户ID: {args.user_id}")
    
    # 获取数据库连接
    engine = get_database_connection()
    
    # 创建数据库会话
    with Session(engine) as session:
        try:
            # 查找用户
            print(f"\n🔍 正在查找用户ID: {args.user_id}")
            user = find_user_by_id(session, args.user_id)
            
            if not user:
                print(f"❌ 未找到用户ID: {args.user_id}")
                sys.exit(1)
            
            # 显示用户信息
            display_user_info(user)
            
            # 确认操作
            if not args.force:
                print(f"\n⚠️  即将重置用户 '{user.name}' 的密码")
                confirm = input("是否继续？(y/N): ")
                if confirm.lower() != 'y':
                    print("❌ 操作已取消")
                    return
            
            # 获取新密码
            if args.password:
                new_password = args.password
                print(f"\n使用命令行指定的密码")
            else:
                print("\n请输入新密码:")
                new_password = getpass.getpass("> ")
                
                if not new_password:
                    print("❌ 新密码不能为空")
                    return
                
                # 确认新密码
                print("\n请再次输入新密码:")
                confirm_password = getpass.getpass("> ")
                
                if new_password != confirm_password:
                    print("❌ 两次输入的密码不一致")
                    return
            
            # 检查密码强度
            if len(new_password) < 6:
                print("⚠️  警告: 密码长度少于6位，建议使用更强的密码")
                if not args.force:
                    continue_anyway = input("是否继续？(y/N): ")
                    if continue_anyway.lower() != 'y':
                        print("❌ 操作已取消")
                        return
            
            # 重置密码
            print(f"\n🔄 正在重置用户 '{user.name}' 的密码...")
            
            if reset_user_password(session, user, new_password):
                print("✅ 密码重置成功！")
                
                # 验证新密码
                print("\n🧪 验证新密码...")
                if verify_password(new_password, user.password):
                    print("✅ 新密码验证成功！")
                else:
                    print("❌ 新密码验证失败！")
                    
            else:
                print("❌ 密码重置失败！")
                sys.exit(1)
                
        except KeyboardInterrupt:
            print("\n\n❌ 操作被用户中断")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ 发生错误: {e}")
            sys.exit(1)
        finally:
            session.close()

if __name__ == "__main__":
    main()
