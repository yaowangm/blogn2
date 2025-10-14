#!/usr/bin/env python3
"""
创建管理员用户脚本
用于在数据库中创建或更新admin用户

使用方法:
    python scripts/create_admin_user.py [选项]
    
选项:
    --username, -u    管理员用户名 (默认: admin)
    --password, -p    管理员密码 (默认: testpasswd)
    --email, -e       管理员邮箱 (可选)
    --database, -d    目标数据库 (默认: blogn_example)
    --force, -f       强制更新已存在的用户
    --dry-run         仅显示将要执行的操作，不实际执行
    --help, -h        显示帮助信息

示例:
    # 使用默认参数创建admin用户
    python scripts/create_admin_user.py
    
    # 创建自定义管理员用户
    python scripts/create_admin_user.py -u myadmin -p mypassword123 -e admin@example.com
    
    # 强制更新已存在的admin用户
    python scripts/create_admin_user.py -f
    
    # 预览操作（不实际执行）
    python scripts/create_admin_user.py --dry-run
"""

import sys
import os
import hashlib
import getpass
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  dotenv 模块未安装，将使用环境变量或默认配置")

from passlib.context import CryptContext
from sqlmodel import create_engine, Session, select
from src.models.user import User

# 创建密码上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_database_connection(database_name: str = "blogn_example"):
    """获取数据库连接"""
    try:
        # 从环境变量获取数据库URL
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            # 如果没有设置环境变量，使用默认的PostgreSQL连接
            print(f"⚠️  DATABASE_URL 环境变量未设置，使用默认配置连接到数据库: {database_name}")
            database_url = f"postgresql+psycopg2://wy:passw0rd@localhost:5432/{database_name}"
        else:
            # 解析现有URL并替换数据库名称
            if "postgresql://" in database_url or "postgresql+psycopg2://" in database_url or "postgresql+asyncpg://" in database_url:
                # 提取基础URL（去掉数据库名部分）
                if "/" in database_url.split("://")[1]:
                    # 找到最后一个斜杠，替换后面的数据库名
                    parts = database_url.split("/")
                    base_url = "/".join(parts[:-1])
                    database_url = f"{base_url}/{database_name}"
                else:
                    # 如果URL中没有数据库名，直接添加
                    database_url = f"{database_url.rstrip('/')}/{database_name}"
            else:
                # 如果URL格式不正确，使用默认格式
                database_url = f"postgresql+psycopg2://wy:passw0rd@localhost:5432/{database_name}"
        
        # 确保使用同步驱动
        if "+asyncpg" in database_url:
            database_url = database_url.replace("+asyncpg", "+psycopg2")
        elif "postgresql://" in database_url and "+psycopg2" not in database_url:
            database_url = database_url.replace("postgresql://", "postgresql+psycopg2://")
        
        print(f"🔗 连接数据库: {database_url}")
        
        # 创建同步引擎（用于用户创建操作）
        sync_engine = create_engine(
            database_url,
            echo=False  # 不显示SQL语句
        )
        
        return sync_engine
        
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        sys.exit(1)

def find_user_by_name(session: Session, username: str) -> Optional[User]:
    """通过用户名查找用户"""
    try:
        user = session.exec(select(User).where(User.name == username)).first()
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

def create_admin_user(session: Session, username: str, password: str, email: str = "") -> bool:
    """创建管理员用户"""
    try:
        # 生成密码哈希
        password_hash = hash_password(password)
        
        # 创建新用户
        new_user = User(
            name=username,
            password=password_hash,
            state=10,  # 管理员状态
            email=email,
            regtime=datetime.now(),
            iplog="127.0.0.1",  # 本地IP
            point=0,  # 初始积分
            lastupdate=datetime.now(),
            intropiid=0
        )
        
        # 保存到数据库
        session.add(new_user)
        session.commit()
        
        return True
        
    except Exception as e:
        print(f"❌ 创建用户失败: {e}")
        session.rollback()
        return False

def update_admin_user(session: Session, user: User, password: str, email: str = "") -> bool:
    """更新管理员用户"""
    try:
        # 生成新的密码哈希
        password_hash = hash_password(password)
        
        # 更新用户信息
        user.password = password_hash
        user.state = 10  # 确保是管理员状态
        if email:
            user.email = email
        user.lastupdate = datetime.now()
        
        # 保存到数据库
        session.add(user)
        session.commit()
        
        return True
        
    except Exception as e:
        print(f"❌ 更新用户失败: {e}")
        session.rollback()
        return False

def display_user_info(user: User):
    """显示用户信息"""
    print(f"\n📋 用户信息:")
    print(f"  ID: {user.id}")
    print(f"  用户名: {user.name}")
    print(f"  邮箱: {user.email or '未设置'}")
    print(f"  状态: {'管理员' if user.state == 10 else '普通用户' if user.state == 1 else '冻结' if user.state == 0 else f'未知({user.state})'}")
    print(f"  注册时间: {user.regtime}")
    print(f"  最后更新: {user.lastupdate or '从未'}")
    print(f"  最后登录IP: {user.iplog or '从未'}")
    print(f"  积分: {user.point}")

def validate_password(password: str) -> tuple[bool, str]:
    """验证密码强度"""
    if len(password) < 6:
        return False, "密码长度至少需要6位"
    
    if len(password) > 50:
        return False, "密码长度不能超过50位"
    
    # 检查是否包含常见弱密码
    weak_passwords = ['123456', 'password', 'admin', 'test', '1234567890']
    if password.lower() in weak_passwords:
        return False, "密码过于简单，请使用更复杂的密码"
    
    return True, "密码强度良好"

def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description="创建或更新管理员用户",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument("--username", "-u", default="admin", help="管理员用户名 (默认: admin)")
    parser.add_argument("--password", "-p", help="管理员密码 (默认: testpasswd)")
    parser.add_argument("--email", "-e", default="", help="管理员邮箱 (可选)")
    parser.add_argument("--database", "-d", default="blogn_example", help="目标数据库 (默认: blogn_example)")
    parser.add_argument("--force", "-f", action="store_true", help="强制更新已存在的用户")
    parser.add_argument("--dry-run", action="store_true", help="仅显示将要执行的操作，不实际执行")
    
    args = parser.parse_args()
    
    print("👤 管理员用户创建工具")
    print("=" * 50)
    print(f"目标数据库: {args.database}")
    print(f"用户名: {args.username}")
    
    # 获取密码
    if args.password:
        password = args.password
        print("使用命令行指定的密码")
    else:
        print("\n请输入管理员密码:")
        password = getpass.getpass("> ")
        
        if not password:
            password = "testpasswd"  # 使用默认密码
            print("使用默认密码: testpasswd")
        else:
            # 确认密码
            print("\n请再次输入密码:")
            confirm_password = getpass.getpass("> ")
            
            if password != confirm_password:
                print("❌ 两次输入的密码不一致")
                return
    
    # 验证密码强度
    is_valid, message = validate_password(password)
    if not is_valid:
        print(f"⚠️  密码验证失败: {message}")
        if not args.force:
            continue_anyway = input("是否继续？(y/N): ")
            if continue_anyway.lower() != 'y':
                print("❌ 操作已取消")
                return
    
    # 获取数据库连接
    engine = get_database_connection(args.database)
    
    # 创建数据库会话
    with Session(engine) as session:
        try:
            # 查找是否已存在用户
            print(f"\n🔍 正在查找用户: {args.username}")
            existing_user = find_user_by_name(session, args.username)
            
            if existing_user:
                print(f"✅ 找到已存在的用户: {args.username}")
                display_user_info(existing_user)
                
                if not args.force and not args.dry_run:
                    print(f"\n⚠️  用户 '{args.username}' 已存在")
                    print("使用 --force 参数强制更新，或选择其他用户名")
                    return
                
                if args.dry_run:
                    print(f"\n🔍 预览操作: 将更新用户 '{args.username}' 的密码和状态")
                    print(f"  新密码: {'*' * len(password)}")
                    print(f"  新状态: 管理员 (10)")
                    if args.email:
                        print(f"  新邮箱: {args.email}")
                    return
                
                # 更新用户
                print(f"\n🔄 正在更新用户 '{args.username}'...")
                if update_admin_user(session, existing_user, password, args.email):
                    print("✅ 用户更新成功！")
                    
                    # 验证新密码
                    print("\n🧪 验证新密码...")
                    if verify_password(password, existing_user.password):
                        print("✅ 新密码验证成功！")
                    else:
                        print("❌ 新密码验证失败！")
                else:
                    print("❌ 用户更新失败！")
                    return
            else:
                if args.dry_run:
                    print(f"\n🔍 预览操作: 将创建新用户 '{args.username}'")
                    print(f"  密码: {'*' * len(password)}")
                    print(f"  状态: 管理员 (10)")
                    print(f"  邮箱: {args.email or '未设置'}")
                    return
                
                # 创建新用户
                print(f"\n🆕 正在创建新用户 '{args.username}'...")
                if create_admin_user(session, args.username, password, args.email):
                    print("✅ 用户创建成功！")
                    
                    # 验证新密码
                    print("\n🧪 验证新密码...")
                    if verify_password(password, hash_password(password)):
                        print("✅ 新密码验证成功！")
                    else:
                        print("❌ 新密码验证失败！")
                else:
                    print("❌ 用户创建失败！")
                    return
            
            # 显示最终用户信息
            print(f"\n📋 最终用户信息:")
            final_user = find_user_by_name(session, args.username)
            if final_user:
                display_user_info(final_user)
            
            print(f"\n🎉 操作完成！")
            print(f"现在可以使用以下凭据登录:")
            print(f"  用户名: {args.username}")
            print(f"  密码: {password}")
                
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
