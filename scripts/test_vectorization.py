#!/usr/bin/env python3
"""
测试向量化脚本的基本功能

用于验证脚本是否能正常启动和连接数据库。
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import get_async_session
from sqlalchemy import text

async def test_database_connection():
    """测试数据库连接"""
    print("测试数据库连接...")
    
    try:
        async for session in get_async_session():
            # 测试基本查询
            result = await session.exec(text("SELECT 1"))
            print("✅ 数据库连接成功")
            
            # 检查向量表是否存在
            tables = ['article_vectors', 'comment_vectors', 'content_segment_vectors']
            for table in tables:
                try:
                    result = await session.exec(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.fetchone()[0]
                    print(f"✅ 表 {table} 存在，记录数: {count}")
                except Exception as e:
                    print(f"❌ 表 {table} 不存在或查询失败: {e}")
            
            # 检查源表
            source_tables = ['projectitem', 'post']
            for table in source_tables:
                try:
                    result = await session.exec(text(f"SELECT COUNT(*) FROM {table} WHERE status = 1"))
                    count = result.fetchone()[0]
                    print(f"✅ 源表 {table} 存在，有效记录数: {count}")
                except Exception as e:
                    print(f"❌ 源表 {table} 查询失败: {e}")
            
            break
            
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False
    
    return True

async def test_vectorization_service():
    """测试向量化服务"""
    print("\n测试向量化服务...")
    
    try:
        from src.services.vectorization_service import BERTVectorizationService
        
        # 创建向量化服务
        service = BERTVectorizationService()
        print("✅ 向量化服务创建成功")
        
        # 测试文本向量化
        test_text = "这是一个测试文本"
        vector = await service.vectorize_text(test_text)
        print(f"✅ 文本向量化成功，向量维度: {len(vector)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 向量化服务测试失败: {e}")
        return False

async def main():
    """主测试函数"""
    print("=" * 50)
    print("向量化脚本测试")
    print("=" * 50)
    
    # 测试数据库连接
    db_ok = await test_database_connection()
    
    # 测试向量化服务
    vector_ok = await test_vectorization_service()
    
    print("\n" + "=" * 50)
    if db_ok and vector_ok:
        print("✅ 所有测试通过，脚本可以正常运行")
    else:
        print("❌ 部分测试失败，请检查配置")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())
