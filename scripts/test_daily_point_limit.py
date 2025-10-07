#!/usr/bin/env python3
"""
测试每日积分限制功能
验证用户每日最多只能获得10积分的限制是否正常工作
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime, date

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database import async_engine
from src.repositories.user_repository import UserRepository
from src.models.user import User
from src.models.point_log import PointLog
from sqlmodel import select

async def test_daily_point_limit():
    """测试每日积分限制功能"""
    try:
        print("🧪 开始测试每日积分限制功能...")
        
        from sqlmodel.ext.asyncio.session import AsyncSession
        
        async with AsyncSession(async_engine) as session:
            # 创建测试用户
            test_user = User(
                name="test_point_user",
                password="test_password",
                email="test_point@example.com",
                regtime=datetime.now(),
                point=0
            )
            session.add(test_user)
            await session.flush()  # 获取用户ID
            
            user_id = test_user.id
            print(f"✅ 创建测试用户，ID: {user_id}")
            
            # 创建UserRepository实例
            user_repo = UserRepository(session)
            
            # 测试1: 第一次增加积分（应该成功）
            print("\n📝 测试1: 第一次增加10积分...")
            result1 = await user_repo.increment_point(user_id, 10, "test_article_1")
            print(f"   结果: {'成功' if result1 else '失败'}")
            
            # 检查用户积分
            user_stmt = select(User).where(User.id == user_id)
            user_result = await session.exec(user_stmt)
            user = user_result.first()
            print(f"   用户当前积分: {user.point}")
            
            # 测试2: 第二次增加积分（应该失败，因为已达到每日10分限制）
            print("\n📝 测试2: 第二次增加10积分（应该失败）...")
            result2 = await user_repo.increment_point(user_id, 10, "test_article_2")
            print(f"   结果: {'成功' if result2 else '失败（符合预期）'}")
            
            # 检查用户积分（应该仍然是10）
            user_result = await session.exec(user_stmt)
            user = user_result.first()
            print(f"   用户当前积分: {user.point}")
            
            # 测试3: 检查积分记录
            print("\n📝 测试3: 检查积分记录...")
            today = date.today()
            today_start = datetime.combine(today, datetime.min.time())
            today_end = datetime.combine(today, datetime.max.time())
            
            log_stmt = select(PointLog).where(
                PointLog.user_id == user_id,
                PointLog.log_date >= today_start,
                PointLog.log_date <= today_end
            )
            log_result = await session.exec(log_stmt)
            logs = log_result.all()
            
            print(f"   今日积分记录数量: {len(logs)}")
            total_points = sum(log.points for log in logs)
            print(f"   今日总积分: {total_points}")
            
            for i, log in enumerate(logs, 1):
                print(f"   记录{i}: {log.points}分 (来源: {log.source})")
            
            # 测试4: 尝试增加少量积分（应该失败，因为已达到10分限制）
            print("\n📝 测试4: 尝试增加1积分（应该失败）...")
            result3 = await user_repo.increment_point(user_id, 1, "test_article_3")
            print(f"   结果: {'成功' if result3 else '失败（符合预期）'}")
            
            # 最终检查
            user_result = await session.exec(user_stmt)
            user = user_result.first()
            print(f"   最终用户积分: {user.point}")
            
            # 清理测试数据
            print("\n🧹 清理测试数据...")
            from sqlalchemy import delete
            await session.exec(delete(PointLog).where(PointLog.user_id == user_id))
            await session.exec(delete(User).where(User.id == user_id))
            await session.commit()
            print("✅ 测试数据已清理")
            
            # 验证结果
            if result1 and not result2 and not result3 and user.point == 10:
                print("\n🎉 所有测试通过！每日积分限制功能正常工作")
                return True
            else:
                print("\n❌ 测试失败！功能可能存在问题")
                return False
                
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🧪 BlogN2 每日积分限制功能测试")
    print("=" * 50)
    
    # 运行异步测试
    try:
        result = asyncio.run(test_daily_point_limit())
        if result:
            print("\n✅ 测试完成：每日积分限制功能正常")
        else:
            print("\n❌ 测试失败：功能存在问题")
        return result
    except KeyboardInterrupt:
        print("\n⏹️  测试被用户中断")
        return False
    except Exception as e:
        print(f"\n💥 测试过程中发生错误: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
