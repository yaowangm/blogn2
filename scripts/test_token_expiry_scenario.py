#!/usr/bin/env python3
"""
测试用户超过30分钟无活动后的令牌刷新场景
模拟实际使用中的令牌过期和刷新情况
"""

import asyncio
import sys
import os
from pathlib import Path
import jwt
from datetime import datetime, timedelta
import time

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.auth_service import AuthService
from src.repositories.user_repository import UserRepository
from src.database import async_engine
from sqlmodel import select
from src.models.user import User

async def test_token_expiry_scenario():
    """测试令牌过期场景"""
    print("测试用户超过30分钟无活动后的令牌刷新场景")
    print("=" * 70)
    
    try:
        # 创建用户仓库
        async with async_engine.begin() as conn:
            # 获取一个测试用户
            result = await conn.execute(select(User).limit(1))
            user = result.first()
            
            if not user:
                print("没有找到测试用户")
                return False
            
            print(f"找到测试用户: {user.name} (ID: {user.id})")
            
            # 创建认证服务
            secret_key = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
            auth_service = AuthService(UserRepository(), secret_key)
            
            # 准备用户数据
            user_data = {
                "user_id": user.id,
                "username": user.name,
                "role": "admin" if user.state == 10 else "user"
            }
            
            print(f"\n创建初始令牌...")
            access_token = auth_service.create_access_token(user_data)
            refresh_token = auth_service.create_refresh_token(user_data)
            
            print(f"访问令牌创建成功")
            print(f"刷新令牌创建成功")
            
            # 测试场景1：访问令牌过期前验证
            print(f"\n测试场景1: 访问令牌过期前验证")
            access_valid = auth_service.verify_token(access_token)
            print(f"访问令牌验证: {'有效' if access_valid else '无效'}")
            
            # 测试场景2：使用刷新令牌获取新访问令牌
            print(f"\n测试场景2: 使用刷新令牌获取新访问令牌")
            new_access_token = auth_service.refresh_access_token(refresh_token)
            
            if new_access_token:
                print(f"令牌刷新成功")
            else:
                print(f"令牌刷新失败")
                return False
            
            # 测试场景3：模拟访问令牌过期后的情况
            print(f"\n测试场景3: 模拟访问令牌过期后的情况")
            
            # 创建一个即将过期的访问令牌（1分钟后过期）
            expired_soon_token = auth_service.create_access_token(
                user_data, 
                expires_delta=timedelta(minutes=1)
            )
            
            print(f"创建1分钟后过期的访问令牌...")
            print(f"等待65秒让令牌过期...")
            
            # 模拟等待
            for i in range(65):
                time.sleep(1)
                if i % 10 == 0:
                    print(f"等待中... {i+1}/65 秒")
            
            print(f"等待完成，现在测试过期令牌...")
            
            # 测试过期令牌
            expired_token_valid = auth_service.verify_token(expired_soon_token)
            print(f"过期令牌验证: {'有效' if expired_token_valid else '无效'}")
            
            if not expired_token_valid:
                print(f"过期令牌正确被拒绝")
                
                # 测试使用刷新令牌获取新访问令牌
                print(f"\n测试场景4: 访问令牌过期后使用刷新令牌刷新")
                new_token_after_expiry = auth_service.refresh_access_token(refresh_token)
                
                if new_token_after_expiry:
                    print(f"过期后令牌刷新成功！")
                else:
                    print(f"过期后令牌刷新失败")
                    return False
            else:
                print(f"过期令牌仍然有效，这是错误的")
                return False
            
            print(f"\n所有测试场景通过！")
            return True
            
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主函数"""
    print("JWT令牌过期场景测试")
    print("=" * 70)
    print("注意：此测试会等待65秒来模拟令牌过期")
    print("=" * 70)
    
    try:
        success = await test_token_expiry_scenario()
        if success:
            print("\n测试完成，令牌过期场景处理正常")
        else:
            print("\n测试失败，请检查配置")
        return success
    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n执行过程中发生错误: {e}")
        sys.exit(1)
