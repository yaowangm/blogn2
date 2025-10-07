#!/usr/bin/env python3
"""
搜索性能测试脚本

用于测试IVFFlat索引优化后的搜索性能。
对比优化前后的查询速度。

使用方法：
    python scripts/test_search_performance.py
"""

import asyncio
import sys
import os
import time
import json
import numpy as np
from pathlib import Path
from typing import Dict, Any, List

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database import get_async_session
from sqlalchemy import text

class SearchPerformanceTester:
    """搜索性能测试器"""
    
    def __init__(self):
        self.session = None
        self.test_queries = [
            "机器学习",
            "深度学习", 
            "人工智能",
            "数据库优化",
            "Python编程",
            "Web开发",
            "算法设计",
            "系统架构"
        ]
    
    async def connect_database(self):
        """连接数据库"""
        try:
            async for session in get_async_session():
                self.session = session
                print("✅ 数据库连接成功")
                break
        except Exception as e:
            print(f"❌ 数据库连接失败: {e}")
            raise
    
    def generate_test_vector(self) -> str:
        """生成测试向量"""
        # 生成随机向量用于测试
        vector = np.random.random(384).tolist()
        return json.dumps(vector)
    
    async def test_simple_vector_query(self, limit: int = 10) -> Dict[str, Any]:
        """测试简单向量查询"""
        print(f"🔍 测试简单向量查询 (LIMIT {limit})...")
        
        test_vector = self.generate_test_vector()
        
        # 测试片段向量查询
        start_time = time.time()
        
        query = text(f"""
            SELECT 
                csv.article_vector_id,
                (1 - (csv.segment_vector <=> '{test_vector}'::vector)) as similarity,
                csv.segment_text
            FROM content_segment_vectors csv
            WHERE csv.segment_vector IS NOT NULL
            ORDER BY csv.segment_vector <=> '{test_vector}'::vector
            LIMIT {limit}
        """)
        
        result = await self.session.execute(query)
        rows = result.fetchall()
        
        query_time = time.time() - start_time
        
        return {
            'query_type': 'simple_vector',
            'table': 'content_segment_vectors',
            'limit': limit,
            'execution_time': query_time,
            'result_count': len(rows),
            'avg_similarity': sum(row[1] for row in rows) / len(rows) if rows else 0
        }
    
    async def test_article_title_query(self, limit: int = 10) -> Dict[str, Any]:
        """测试文章标题查询"""
        print(f"🔍 测试文章标题查询 (LIMIT {limit})...")
        
        test_vector = self.generate_test_vector()
        
        start_time = time.time()
        
        query = text(f"""
            SELECT 
                av.projectitem_id,
                (1 - (av.title_vector <=> '{test_vector}'::vector)) as similarity,
                av.title_text
            FROM article_vectors av
            WHERE av.title_vector IS NOT NULL
            ORDER BY av.title_vector <=> '{test_vector}'::vector
            LIMIT {limit}
        """)
        
        result = await self.session.execute(query)
        rows = result.fetchall()
        
        query_time = time.time() - start_time
        
        return {
            'query_type': 'article_title',
            'table': 'article_vectors',
            'limit': limit,
            'execution_time': query_time,
            'result_count': len(rows),
            'avg_similarity': sum(row[1] for row in rows) / len(rows) if rows else 0
        }
    
    async def test_complex_search_query(self, limit: int = 10) -> Dict[str, Any]:
        """测试复杂搜索查询（模拟实际搜索场景）"""
        print(f"🔍 测试复杂搜索查询 (LIMIT {limit})...")
        
        test_vector = self.generate_test_vector()
        
        start_time = time.time()
        
        # 模拟实际的搜索查询，包含JOIN操作
        query = text(f"""
            WITH title_scores AS (
                SELECT 
                    av.projectitem_id,
                    pi.name,
                    pi.comment,
                    u.name as author,
                    pi.createtime,
                    (1 - (av.title_vector <=> '{test_vector}'::vector)) * 0.7 as similarity
                FROM article_vectors av
                LEFT JOIN projectitem pi ON av.projectitem_id = pi.id
                LEFT JOIN users u ON pi.userid = u.id
                WHERE pi.status = 1 AND av.title_vector IS NOT NULL
                ORDER BY av.title_vector <=> '{test_vector}'::vector
                LIMIT 1000
            ),
            segment_scores AS (
                SELECT 
                    av.projectitem_id,
                    pi.name,
                    pi.comment,
                    u.name as author,
                    pi.createtime,
                    (1 - (csv.segment_vector <=> '{test_vector}'::vector)) as similarity
                FROM article_vectors av
                LEFT JOIN projectitem pi ON av.projectitem_id = pi.id
                LEFT JOIN users u ON pi.userid = u.id
                LEFT JOIN content_segment_vectors csv ON av.id = csv.article_vector_id
                WHERE pi.status = 1 AND csv.segment_vector IS NOT NULL
                ORDER BY csv.segment_vector <=> '{test_vector}'::vector
                LIMIT 1000
            ),
            combined_scores AS (
                SELECT * FROM title_scores
                UNION ALL
                SELECT * FROM segment_scores
            ),
            max_similarities AS (
                SELECT 
                    projectitem_id,
                    name,
                    comment,
                    author,
                    createtime,
                    MAX(similarity) as relevance_score
                FROM combined_scores
                GROUP BY projectitem_id, name, comment, author, createtime
            )
            SELECT 
                projectitem_id as id,
                name as title,
                comment as content,
                author,
                createtime,
                relevance_score
            FROM max_similarities
            WHERE relevance_score > 0.5
            ORDER BY relevance_score DESC
            LIMIT {limit}
        """)
        
        result = await self.session.execute(query)
        rows = result.fetchall()
        
        query_time = time.time() - start_time
        
        return {
            'query_type': 'complex_search',
            'description': '模拟实际搜索场景',
            'limit': limit,
            'execution_time': query_time,
            'result_count': len(rows),
            'avg_similarity': sum(row[5] for row in rows) / len(rows) if rows else 0
        }
    
    async def test_index_usage(self) -> Dict[str, Any]:
        """测试索引使用情况"""
        print("🔍 检查索引使用情况...")
        
        try:
            # 检查IVFFlat索引
            query = text("""
                SELECT 
                    indexname,
                    tablename,
                    pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
                    indexdef
                FROM pg_indexes 
                WHERE indexname LIKE '%ivfflat%'
                ORDER BY tablename, indexname
            """)
            
            result = await self.session.execute(query)
            indexes = result.fetchall()
            
            return {
                'index_count': len(indexes),
                'indexes': [
                    {
                        'name': idx.indexname,
                        'table': idx.tablename,
                        'size': idx.index_size,
                        'definition': idx.indexdef
                    } for idx in indexes
                ]
            }
            
        except Exception as e:
            print(f"❌ 检查索引失败: {e}")
            return {'error': str(e)}
    
    async def run_performance_tests(self) -> List[Dict[str, Any]]:
        """运行性能测试"""
        print("🚀 开始性能测试...")
        print("=" * 60)
        
        results = []
        
        # 1. 检查索引
        index_info = await self.test_index_usage()
        results.append({
            'test_name': 'index_check',
            'data': index_info
        })
        
        # 2. 简单向量查询测试
        for limit in [10, 50, 100]:
            result = await self.test_simple_vector_query(limit)
            results.append({
                'test_name': 'simple_vector_query',
                'data': result
            })
        
        # 3. 文章标题查询测试
        for limit in [10, 50, 100]:
            result = await self.test_article_title_query(limit)
            results.append({
                'test_name': 'article_title_query',
                'data': result
            })
        
        # 4. 复杂搜索查询测试
        for limit in [10, 20]:
            result = await self.test_complex_search_query(limit)
            results.append({
                'test_name': 'complex_search_query',
                'data': result
            })
        
        return results
    
    def print_results(self, results: List[Dict[str, Any]]):
        """打印测试结果"""
        print("\n" + "=" * 60)
        print("📊 性能测试结果")
        print("=" * 60)
        
        # 索引信息
        index_check = next((r for r in results if r['test_name'] == 'index_check'), None)
        if index_check and 'error' not in index_check['data']:
            print(f"📋 索引数量: {index_check['data']['index_count']}")
            for idx in index_check['data']['indexes']:
                print(f"  - {idx['name']}: {idx['size']}")
        
        # 查询性能
        print("\n🔍 查询性能:")
        
        # 简单向量查询
        simple_queries = [r for r in results if r['test_name'] == 'simple_vector_query']
        if simple_queries:
            print("\n  片段向量查询:")
            for query in simple_queries:
                data = query['data']
                print(f"    LIMIT {data['limit']:3d}: {data['execution_time']:.3f}秒, {data['result_count']}条结果, 平均相似度: {data['avg_similarity']:.3f}")
        
        # 文章标题查询
        title_queries = [r for r in results if r['test_name'] == 'article_title_query']
        if title_queries:
            print("\n  文章标题查询:")
            for query in title_queries:
                data = query['data']
                print(f"    LIMIT {data['limit']:3d}: {data['execution_time']:.3f}秒, {data['result_count']}条结果, 平均相似度: {data['avg_similarity']:.3f}")
        
        # 复杂搜索查询
        complex_queries = [r for r in results if r['test_name'] == 'complex_search_query']
        if complex_queries:
            print("\n  复杂搜索查询:")
            for query in complex_queries:
                data = query['data']
                print(f"    LIMIT {data['limit']:3d}: {data['execution_time']:.3f}秒, {data['result_count']}条结果, 平均相似度: {data['avg_similarity']:.3f}")
        
        # 性能评估
        print("\n📈 性能评估:")
        if simple_queries:
            avg_simple_time = sum(q['data']['execution_time'] for q in simple_queries) / len(simple_queries)
            print(f"  平均简单查询时间: {avg_simple_time:.3f}秒")
        
        if complex_queries:
            avg_complex_time = sum(q['data']['execution_time'] for q in complex_queries) / len(complex_queries)
            print(f"  平均复杂查询时间: {avg_complex_time:.3f}秒")
            
            if avg_complex_time < 5:
                print("  ✅ 性能优秀 (< 5秒)")
            elif avg_complex_time < 15:
                print("  ✅ 性能良好 (5-15秒)")
            elif avg_complex_time < 30:
                print("  ⚠️  性能一般 (15-30秒)")
            else:
                print("  ❌ 性能较差 (> 30秒)")
        
        print("\n💡 建议:")
        print("  - 如果查询时间 > 10秒，考虑调整IVFFlat的lists参数")
        print("  - 如果召回率不够，可以增加聚类数量")
        print("  - 定期重建索引以保持最佳性能")
    
    async def run_tests(self):
        """运行所有测试"""
        try:
            await self.connect_database()
            results = await self.run_performance_tests()
            self.print_results(results)
            
            # 保存结果到文件
            import json
            with open('search_performance_test_results.json', 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False, default=str)
            print(f"\n📁 详细结果已保存到: search_performance_test_results.json")
            
        except Exception as e:
            print(f"❌ 测试失败: {e}")
        finally:
            if self.session:
                await self.session.close()

async def main():
    """主函数"""
    print("🧪 搜索性能测试脚本")
    print("=" * 60)
    print("此脚本将测试IVFFlat索引优化后的搜索性能")
    print("=" * 60)
    
    tester = SearchPerformanceTester()
    await tester.run_tests()

if __name__ == "__main__":
    asyncio.run(main())
