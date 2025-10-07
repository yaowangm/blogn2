#!/usr/bin/env python3
"""
搜索诊断脚本

用于诊断搜索性能问题，检查是否使用了正确的向量搜索。
"""

import asyncio
import sys
import os
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database import get_async_session
from src.services.vectorization_service import BERTVectorizationService
from src.services.search_service import HierarchicalSearchService
from sqlalchemy import text

async def test_vector_tables():
    """测试向量表是否存在"""
    print("🔍 检查向量表...")
    
    try:
        async for session in get_async_session():
            # 检查所有向量表
            tables = ['article_vectors', 'content_segment_vectors', 'comment_vectors']
            
            for table in tables:
                try:
                    result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.fetchone()[0]
                    print(f"  ✅ {table}: {count:,} 条记录")
                except Exception as e:
                    print(f"  ❌ {table}: 不存在或查询失败 - {e}")
            
            # 检查IVFFlat索引
            print("\n🔍 检查IVFFlat索引...")
            result = await session.execute(text("""
                SELECT indexname, tablename 
                FROM pg_indexes 
                WHERE indexname LIKE '%ivfflat%'
                ORDER BY tablename, indexname
            """))
            indexes = result.fetchall()
            
            if indexes:
                print(f"  ✅ 找到 {len(indexes)} 个IVFFlat索引:")
                for idx in indexes:
                    print(f"    - {idx.indexname} (表: {idx.tablename})")
            else:
                print("  ❌ 未找到IVFFlat索引")
            
            break
            
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")

async def test_search_service():
    """测试搜索服务"""
    print("\n🧪 测试搜索服务...")
    
    try:
        # 初始化服务
        vectorization_service = BERTVectorizationService()
        
        async for session in get_async_session():
            search_service = HierarchicalSearchService(vectorization_service, session)
            
            # 测试搜索
            test_query = "机器学习"
            print(f"  🔍 测试查询: '{test_query}'")
            
            start_time = time.time()
            results = await search_service.search(
                query=test_query,
                search_type="articles",
                sort_by="relevance",
                page=1,
                limit=5
            )
            search_time = time.time() - start_time
            
            print(f"  ⏱️  搜索时间: {search_time:.3f}秒")
            print(f"  📊 结果数量: {results.get('total', 0)}")
            print(f"  🔧 搜索方法: {results.get('search_method', 'unknown')}")
            print(f"  📈 动态阈值: {results.get('dynamic_threshold', 0.6)}")
            
            if results.get('items'):
                print(f"  📝 前3个结果:")
                for i, item in enumerate(results['items'][:3]):
                    print(f"    {i+1}. {item.get('title', 'N/A')} (相似度: {item.get('relevance_score', 0):.3f})")
            
            break
            
    except Exception as e:
        print(f"❌ 搜索服务测试失败: {e}")
        import traceback
        traceback.print_exc()

async def test_direct_vector_query():
    """测试直接向量查询"""
    print("\n🔬 测试直接向量查询...")
    
    try:
        async for session in get_async_session():
            # 生成测试向量
            test_vector = [0.1] * 384
            test_vector_json = str(test_vector).replace("'", '"')
            
            # 测试片段向量查询
            print("  🔍 测试片段向量查询...")
            start_time = time.time()
            
            query = text(f"""
                SELECT 
                    csv.article_vector_id,
                    (1 - (csv.segment_vector <=> '{test_vector_json}'::vector)) as similarity
                FROM content_segment_vectors csv
                WHERE csv.segment_vector IS NOT NULL
                ORDER BY csv.segment_vector <=> '{test_vector_json}'::vector
                LIMIT 10
            """)
            
            result = await session.execute(query)
            rows = result.fetchall()
            
            query_time = time.time() - start_time
            print(f"    ⏱️  查询时间: {query_time:.3f}秒")
            print(f"    📊 结果数量: {len(rows)}")
            
            if rows:
                print(f"    📈 最高相似度: {max(row[1] for row in rows):.3f}")
            
            # 测试文章标题查询
            print("  🔍 测试文章标题查询...")
            start_time = time.time()
            
            query = text(f"""
                SELECT 
                    av.projectitem_id,
                    (1 - (av.title_vector <=> '{test_vector_json}'::vector)) as similarity
                FROM article_vectors av
                WHERE av.title_vector IS NOT NULL
                ORDER BY av.title_vector <=> '{test_vector_json}'::vector
                LIMIT 10
            """)
            
            result = await session.execute(query)
            rows = result.fetchall()
            
            query_time = time.time() - start_time
            print(f"    ⏱️  查询时间: {query_time:.3f}秒")
            print(f"    📊 结果数量: {len(rows)}")
            
            if rows:
                print(f"    📈 最高相似度: {max(row[1] for row in rows):.3f}")
            
            break
            
    except Exception as e:
        print(f"❌ 直接向量查询测试失败: {e}")
        import traceback
        traceback.print_exc()

async def test_fallback_query():
    """测试fallback查询（LIKE查询）"""
    print("\n⚠️  测试fallback查询（LIKE查询）...")
    
    try:
        async for session in get_async_session():
            test_query = "机器学习"
            
            # 测试LIKE查询性能
            print(f"  🔍 测试LIKE查询: '{test_query}'")
            start_time = time.time()
            
            query = text(f"""
                SELECT 
                    pi.id,
                    pi.name as title,
                    pi.comment as content,
                    u.name as author,
                    pi.createtime,
                    1.0 as relevance_score
                FROM projectitem pi
                LEFT JOIN users u ON pi.userid = u.id
                WHERE pi.status = 1 AND (pi.name ILIKE '%{test_query}%' OR pi.comment ILIKE '%{test_query}%')
                ORDER BY 
                    CASE 
                        WHEN pi.name ILIKE '%{test_query}%' THEN 3
                        WHEN pi.comment ILIKE '%{test_query}%' THEN 2
                        ELSE 1
                    END DESC
                LIMIT 10
            """)
            
            result = await session.execute(query)
            rows = result.fetchall()
            
            query_time = time.time() - start_time
            print(f"    ⏱️  查询时间: {query_time:.3f}秒")
            print(f"    📊 结果数量: {len(rows)}")
            
            if rows:
                print(f"    📝 前3个结果:")
                for i, row in enumerate(rows[:3]):
                    print(f"      {i+1}. {row[1]} (作者: {row[3]})")
            
            break
            
    except Exception as e:
        print(f"❌ fallback查询测试失败: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """主函数"""
    print("🔧 搜索诊断脚本")
    print("=" * 50)
    
    # 1. 检查向量表
    await test_vector_tables()
    
    # 2. 测试搜索服务
    await test_search_service()
    
    # 3. 测试直接向量查询
    await test_direct_vector_query()
    
    # 4. 测试fallback查询
    await test_fallback_query()
    
    print("\n" + "=" * 50)
    print("✅ 诊断完成！")

if __name__ == "__main__":
    asyncio.run(main())
