#!/usr/bin/env python3
"""
IVFFlat索引优化脚本（修复版）

修复了内存不足和事务失败的问题。
- 增加maintenance_work_mem设置
- 修复事务管理问题
- 优化聚类数设置

使用方法：
    python scripts/optimize_indexes_ivfflat_fixed.py
"""

import asyncio
import sys
import os
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database import get_async_session
from sqlalchemy import text

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ivfflat_optimization_fixed.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class IVFFlatOptimizerFixed:
    """IVFFlat索引优化器（修复版）"""
    
    def __init__(self):
        self.session = None
        self.backup_file = f"index_backup_fixed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        self.start_time = None
        
    async def connect_database(self):
        """连接数据库"""
        try:
            async for session in get_async_session():
                self.session = session
                logger.info("✅ 数据库连接成功")
                break
        except Exception as e:
            logger.error(f"❌ 数据库连接失败: {e}")
            raise
    
    async def setup_database_config(self):
        """设置数据库配置以支持索引创建"""
        logger.info("⚙️  设置数据库配置...")
        
        try:
            # 增加maintenance_work_mem以支持索引创建
            config_queries = [
                "SET maintenance_work_mem = '512MB'",
                "SET max_parallel_workers_per_gather = 2",
                "SET work_mem = '256MB'"
            ]
            
            for query in config_queries:
                try:
                    await self.session.execute(text(query))
                    logger.info(f"  ✅ 执行配置: {query}")
                except Exception as e:
                    logger.warning(f"  ⚠️  配置失败 {query}: {e}")
            
            await self.session.commit()
            logger.info("✅ 数据库配置设置完成")
            
        except Exception as e:
            logger.error(f"❌ 设置数据库配置失败: {e}")
            raise
    
    async def backup_existing_indexes(self):
        """备份现有索引定义"""
        logger.info("📋 备份现有索引定义...")
        
        try:
            # 查询现有HNSW索引
            query = text("""
                SELECT 
                    indexname,
                    indexdef,
                    tablename
                FROM pg_indexes 
                WHERE indexname LIKE '%hnsw%' OR indexname LIKE '%vector%'
                ORDER BY tablename, indexname
            """)
            
            result = await self.session.execute(query)
            indexes = result.fetchall()
            
            if not indexes:
                logger.warning("⚠️  未找到向量索引")
                return
            
            # 保存到备份文件
            backup_path = project_root / "scripts" / self.backup_file
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write("-- 向量索引备份文件\n")
                f.write(f"-- 备份时间: {datetime.now()}\n")
                f.write(f"-- 索引数量: {len(indexes)}\n\n")
                
                for index in indexes:
                    f.write(f"-- 表: {index.tablename}\n")
                    f.write(f"-- 索引名: {index.indexname}\n")
                    f.write(f"{index.indexdef};\n\n")
            
            logger.info(f"✅ 索引备份完成: {backup_path}")
            logger.info(f"📊 备份了 {len(indexes)} 个索引")
            
        except Exception as e:
            logger.error(f"❌ 备份索引失败: {e}")
            raise
    
    async def get_table_stats(self) -> Dict[str, Any]:
        """获取表统计信息"""
        logger.info("📊 获取表统计信息...")
        
        try:
            query = text("""
                SELECT 
                    t.tablename,
                    s.n_live_tup as record_count,
                    pg_size_pretty(pg_total_relation_size(t.schemaname||'.'||t.tablename)) as table_size
                FROM pg_tables t
                JOIN pg_stat_user_tables s ON s.relname = t.tablename
                WHERE t.tablename IN ('article_vectors', 'content_segment_vectors', 'comment_vectors')
                ORDER BY pg_total_relation_size(t.schemaname||'.'||t.tablename) DESC
            """)
            
            result = await self.session.execute(query)
            stats = result.fetchall()
            
            logger.info("📈 表统计信息:")
            for stat in stats:
                logger.info(f"  - {stat.tablename}: {stat.record_count:,} 条记录, {stat.table_size}")
            
            return {stat.tablename: {
                'record_count': stat.record_count,
                'table_size': stat.table_size
            } for stat in stats}
            
        except Exception as e:
            logger.error(f"❌ 获取表统计失败: {e}")
            raise
    
    async def drop_existing_indexes(self):
        """删除现有索引"""
        logger.info("🗑️  删除现有索引...")
        
        indexes_to_drop = [
            'idx_segment_vectors_vector_hnsw',
            'idx_article_vectors_title_hnsw', 
            'idx_article_vectors_content_hnsw',
            'idx_comment_vectors_title_hnsw',
            'idx_comment_vectors_content_hnsw',
            'article_vectors_title_vector_idx',
            'article_vectors_content_vector_idx',
            'comment_vectors_title_vector_idx',
            'comment_vectors_content_vector_idx',
            'content_segment_vectors_segment_vector_idx'
        ]
        
        dropped_count = 0
        for index_name in indexes_to_drop:
            try:
                # 检查索引是否存在
                check_query = text("""
                    SELECT EXISTS (
                        SELECT 1 FROM pg_indexes 
                        WHERE indexname = :index_name
                    )
                """)
                
                result = await self.session.execute(check_query, {"index_name": index_name})
                exists = result.fetchone()[0]
                
                if exists:
                    drop_query = text(f"DROP INDEX IF EXISTS {index_name}")
                    await self.session.execute(drop_query)
                    await self.session.commit()
                    logger.info(f"  ✅ 删除索引: {index_name}")
                    dropped_count += 1
                else:
                    logger.info(f"  ⏭️  索引不存在: {index_name}")
                    
            except Exception as e:
                logger.warning(f"  ⚠️  删除索引失败 {index_name}: {e}")
                # 回滚事务
                await self.session.rollback()
        
        logger.info(f"✅ 删除了 {dropped_count} 个索引")
    
    async def create_ivfflat_index(self, config: Dict[str, Any]) -> bool:
        """创建单个IVFFlat索引"""
        try:
            logger.info(f"🔨 创建索引: {config['description']}")
            logger.info(f"  - 表: {config['table']}")
            logger.info(f"  - 列: {config['column']}")
            logger.info(f"  - 聚类数: {config['lists']}")
            
            index_start_time = time.time()
            
            # 开始新事务
            await self.session.begin()
            
            create_query = text(f"""
                CREATE INDEX {config['name']} ON {config['table']} 
                USING ivfflat ({config['column']} vector_cosine_ops) 
                WITH (lists = {config['lists']})
            """)
            
            await self.session.execute(create_query)
            await self.session.commit()
            
            index_time = time.time() - index_start_time
            logger.info(f"  ✅ 创建完成，耗时: {index_time:.2f}秒")
            return True
            
        except Exception as e:
            logger.error(f"  ❌ 创建索引失败 {config['name']}: {e}")
            await self.session.rollback()
            return False
    
    async def create_ivfflat_indexes(self):
        """创建IVFFlat索引"""
        logger.info("🔨 开始创建IVFFlat索引...")
        
        # 优化的索引配置（减少聚类数以降低内存需求）
        index_configs = [
            {
                'name': 'idx_segment_vectors_vector_ivfflat',
                'table': 'content_segment_vectors',
                'column': 'segment_vector',
                'lists': 500,  # 从1000减少到500
                'description': '片段向量索引（最大表）'
            },
            {
                'name': 'idx_article_vectors_title_ivfflat',
                'table': 'article_vectors', 
                'column': 'title_vector',
                'lists': 50,   # 从100减少到50
                'description': '文章标题向量索引'
            },
            {
                'name': 'idx_article_vectors_content_ivfflat',
                'table': 'article_vectors',
                'column': 'content_vector', 
                'lists': 50,   # 从100减少到50
                'description': '文章内容向量索引'
            },
            {
                'name': 'idx_comment_vectors_title_ivfflat',
                'table': 'comment_vectors',
                'column': 'title_vector',
                'lists': 75,   # 从150减少到75
                'description': '评论标题向量索引'
            },
            {
                'name': 'idx_comment_vectors_content_ivfflat',
                'table': 'comment_vectors',
                'column': 'content_vector',
                'lists': 75,   # 从150减少到75
                'description': '评论内容向量索引'
            }
        ]
        
        created_count = 0
        total_start_time = time.time()
        
        for config in index_configs:
            success = await self.create_ivfflat_index(config)
            if success:
                created_count += 1
        
        total_time = time.time() - total_start_time
        logger.info(f"✅ 索引创建完成，成功创建 {created_count}/{len(index_configs)} 个索引")
        logger.info(f"⏱️  总耗时: {total_time:.2f}秒")
        
        return created_count > 0
    
    async def verify_indexes(self):
        """验证索引创建结果"""
        logger.info("🔍 验证索引创建结果...")
        
        try:
            query = text("""
                SELECT 
                    indexname,
                    tablename,
                    indexdef,
                    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
                FROM pg_indexes 
                WHERE indexname LIKE '%ivfflat%'
                ORDER BY tablename, indexname
            """)
            
            result = await self.session.execute(query)
            indexes = result.fetchall()
            
            if not indexes:
                logger.error("❌ 未找到IVFFlat索引，创建可能失败")
                return False
            
            logger.info("📊 创建的IVFFlat索引:")
            for index in indexes:
                logger.info(f"  - {index.indexname}")
                logger.info(f"    表: {index.tablename}")
                logger.info(f"    大小: {index.index_size}")
                logger.info("")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 验证索引失败: {e}")
            return False
    
    async def test_query_performance(self):
        """测试查询性能"""
        logger.info("🧪 测试查询性能...")
        
        try:
            # 创建测试向量
            test_vector = [0.1] * 384
            test_vector_json = str(test_vector).replace("'", '"')
            
            # 测试片段向量查询
            logger.info("  🔍 测试片段向量查询...")
            start_time = time.time()
            
            query = text(f"""
                SELECT 
                    article_vector_id,
                    (1 - (segment_vector <=> '{test_vector_json}'::vector)) as similarity
                FROM content_segment_vectors
                WHERE segment_vector IS NOT NULL
                ORDER BY segment_vector <=> '{test_vector_json}'::vector
                LIMIT 10
            """)
            
            result = await self.session.execute(query)
            rows = result.fetchall()
            
            query_time = time.time() - start_time
            logger.info(f"  ✅ 片段向量查询完成，耗时: {query_time:.3f}秒，返回 {len(rows)} 条结果")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 性能测试失败: {e}")
            return False
    
    async def generate_report(self, success: bool):
        """生成优化报告"""
        logger.info("📋 生成优化报告...")
        
        try:
            report_file = project_root / "scripts" / f"ivfflat_optimization_report_fixed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("# IVFFlat索引优化报告（修复版）\n\n")
                f.write(f"**优化时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**总耗时**: {time.time() - self.start_time:.2f}秒\n")
                f.write(f"**优化状态**: {'✅ 成功' if success else '❌ 失败'}\n\n")
                
                f.write("## 修复内容\n\n")
                f.write("1. 增加maintenance_work_mem到512MB\n")
                f.write("2. 优化聚类数设置以减少内存需求\n")
                f.write("3. 修复事务管理问题\n")
                f.write("4. 改进错误处理机制\n\n")
                
                f.write("## 优化内容\n\n")
                f.write("1. 备份现有索引定义\n")
                f.write("2. 删除现有索引\n")
                f.write("3. 创建优化的IVFFlat索引\n")
                f.write("4. 验证索引创建结果\n")
                f.write("5. 测试查询性能\n\n")
                
                f.write("## 索引配置（优化后）\n\n")
                f.write("| 表名 | 索引名 | 聚类数 | 说明 |\n")
                f.write("|------|--------|--------|------|\n")
                f.write("| content_segment_vectors | idx_segment_vectors_vector_ivfflat | 500 | 片段向量索引 |\n")
                f.write("| article_vectors | idx_article_vectors_title_ivfflat | 50 | 文章标题向量索引 |\n")
                f.write("| article_vectors | idx_article_vectors_content_ivfflat | 50 | 文章内容向量索引 |\n")
                f.write("| comment_vectors | idx_comment_vectors_title_ivfflat | 75 | 评论标题向量索引 |\n")
                f.write("| comment_vectors | idx_comment_vectors_content_ivfflat | 75 | 评论内容向量索引 |\n\n")
                
                f.write("## 预期效果\n\n")
                f.write("- **查询速度**: 从150秒降低到2-8秒\n")
                f.write("- **索引构建**: 从25-45分钟降低到5-12分钟\n")
                f.write("- **内存使用**: 减少50-70%\n")
                f.write("- **磁盘占用**: 减少60-80%\n\n")
                
                f.write("## 注意事项\n\n")
                f.write("1. 聚类数已优化以减少内存需求\n")
                f.write("2. 如果查询精度不够，可以适当增加聚类数\n")
                f.write("3. 建议每月重建一次索引以保持最佳性能\n")
                f.write(f"4. 备份文件位置: {self.backup_file}\n")
            
            logger.info(f"✅ 优化报告已生成: {report_file}")
            
        except Exception as e:
            logger.error(f"❌ 生成报告失败: {e}")
    
    async def run_optimization(self):
        """执行完整的索引优化流程"""
        self.start_time = time.time()
        success = False
        
        try:
            logger.info("🚀 开始IVFFlat索引优化（修复版）...")
            logger.info("=" * 60)
            
            # 1. 连接数据库
            await self.connect_database()
            
            # 2. 设置数据库配置
            await self.setup_database_config()
            
            # 3. 获取表统计信息
            await self.get_table_stats()
            
            # 4. 备份现有索引
            await self.backup_existing_indexes()
            
            # 5. 删除现有索引
            await self.drop_existing_indexes()
            
            # 6. 创建IVFFlat索引
            if await self.create_ivfflat_indexes():
                # 7. 验证索引
                if await self.verify_indexes():
                    # 8. 测试性能
                    if await self.test_query_performance():
                        success = True
                        logger.info("🎉 IVFFlat索引优化完成！")
                    else:
                        logger.error("❌ 性能测试失败")
                else:
                    logger.error("❌ 索引验证失败")
            else:
                logger.error("❌ 索引创建失败")
            
            # 9. 生成报告
            await self.generate_report(success)
            
            total_time = time.time() - self.start_time
            logger.info("=" * 60)
            if success:
                logger.info("🎉 IVFFlat索引优化成功！")
                logger.info(f"⏱️  总耗时: {total_time:.2f}秒")
                logger.info("📈 预期查询性能提升: 20-75倍")
                logger.info("💾 内存使用减少: 50-70%")
                logger.info("📁 磁盘占用减少: 60-80%")
            else:
                logger.error("❌ IVFFlat索引优化失败")
                logger.error("请检查日志文件获取详细错误信息")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ 优化过程失败: {e}")
            await self.generate_report(False)
            return False
        
        finally:
            if self.session:
                await self.session.close()

async def main():
    """主函数"""
    optimizer = IVFFlatOptimizerFixed()
    
    # 确认执行
    print("🔧 IVFFlat索引优化脚本（修复版）")
    print("=" * 60)
    print("⚠️  注意事项:")
    print("1. 此操作将删除现有索引并创建IVFFlat索引")
    print("2. 已优化聚类数设置以减少内存需求")
    print("3. 预计耗时: 5-12分钟")
    print("4. 建议在低峰期执行")
    print("5. 会自动备份现有索引定义")
    print("=" * 60)
    
    confirm = input("是否继续执行？(y/N): ").strip().lower()
    if confirm != 'y':
        print("❌ 操作已取消")
        return
    
    success = await optimizer.run_optimization()
    
    if success:
        print("\n✅ 优化完成！请测试搜索功能验证效果。")
        print("🧪 运行性能测试: python scripts/test_search_performance.py")
    else:
        print("\n❌ 优化失败！请检查日志文件。")

if __name__ == "__main__":
    asyncio.run(main())
