#!/usr/bin/env python3
"""
测试令牌刷新功能的脚本
用于验证JWT令牌的生成、验证和刷新是否正常工作
"""

import asyncio
import sys
import os
from pathlib import Path
import jwt
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.auth_service import AuthService
from src.repositories.user_repository import UserRepository
from src.database import async_engine
from sqlmodel import select
from src.models.user import User

async def test_token_refresh():
    """测试令牌刷新功能"""
    print("🔐 测试JWT令牌刷新功能")
    print("=" * 50)
    
    try:
        # 创建用户仓库
        async with async_engine.begin() as conn:
            # 获取一个测试用户
            result = await conn.execute(select(User).limit(1))
            user = result.first()
            
            if not user:
                print("❌ 没有找到测试用户")
                return False
            
            print(f"✅ 找到测试用户: {user.name} (ID: {user.id})")
            
            # 创建认证服务
            secret_key = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
            auth_service = AuthService(UserRepository(), secret_key)
            
            # 准备用户数据
            user_data = {
                "user_id": user.id,
                "username": user.name,
                "role": "admin" if user.state == 10 else "user"
            }
            
            # 创建访问令牌和刷新令牌
            print("\n📝 创建令牌...")
            access_token = auth_service.create_access_token(user_data)
            refresh_token = auth_service.create_refresh_token(user_data)
            
            print(f"✅ 访问令牌创建成功")
            print(f"✅ 刷新令牌创建成功")
            
            # 解码令牌查看过期时间
            access_payload = jwt.decode(access_token, secret_key, algorithms=["HS256"])
            refresh_payload = jwt.decode(refresh_token, secret_key, algorithms=["HS256"])
            
            access_exp = datetime.fromtimestamp(access_payload["exp"])
            refresh_exp = datetime.fromtimestamp(refresh_payload["exp"])
            now = datetime.utcnow()
            
            print(f"\n⏰ 令牌过期时间:")
            print(f"   当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')} UTC")
            print(f"   访问令牌过期: {access_exp.strftime('%Y-%m-%d %H:%M:%S')} UTC")
            print(f"   刷新令牌过期: {refresh_exp.strftime('%Y-%m-%d %H:%M:%S')} UTC")
            
            access_expires_in = (access_exp - now).total_seconds() / 60
            refresh_expires_in = (refresh_exp - now).total_seconds() / 3600
            
            print(f"\n⏱️  剩余时间:")
            print(f"   访问令牌: {access_expires_in:.1f} 分钟")
            print(f"   刷新令牌: {refresh_expires_in:.1f} 小时")
            
            # 测试令牌验证
            print(f"\n🔍 测试令牌验证...")
            access_valid = auth_service.verify_token(access_token)
            refresh_valid = auth_service.verify_token(refresh_token)
            
            print(f"   访问令牌验证: {'✅ 有效' if access_valid else '❌ 无效'}")
            print(f"   刷新令牌验证: {'✅ 有效' if refresh_valid else '❌ 无效'}")
            
            # 测试令牌刷新
            print(f"\n🔄 测试令牌刷新...")
            new_access_token = auth_service.refresh_access_token(refresh_token)
            
            if new_access_token:
                print(f"✅ 令牌刷新成功")
                
                # 验证新令牌
                new_payload = jwt.decode(new_access_token, secret_key, algorithms=["HS256"])
                new_exp = datetime.fromtimestamp(new_payload["exp"])
                new_expires_in = (new_exp - now).total_seconds() / 60
                
                print(f"   新访问令牌过期: {new_exp.strftime('%Y-%m-%d %H:%M:%S')} UTC")
                print(f"   新访问令牌剩余: {new_expires_in:.1f} 分钟")
            else:
                print(f"❌ 令牌刷新失败")
                return False
            
            print(f"\n🎉 所有测试通过！")
            return True
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主函数"""
    print("🚀 JWT令牌刷新功能测试")
    print("=" * 50)
    
    try:
        success = await test_token_refresh()
        if success:
            print("\n✅ 测试完成，令牌刷新功能正常")
        else:
            print("\n❌ 测试失败，请检查配置")
        return success
    except Exception as e:
        print(f"\n💥 测试过程中发生错误: {e}")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 执行过程中发生错误: {e}")
        sys.exit(1)
