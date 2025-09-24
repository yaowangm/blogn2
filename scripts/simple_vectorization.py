#!/usr/bin/env python3
"""
简化版存量数据向量化脚本

用于将现有的文章和评论数据批量向量化，填充向量表。
支持进度显示、中断恢复等功能。

使用方法:
    python scripts/simple_vectorization.py --clear-tables
    python scripts/simple_vectorization.py --resume
"""

import asyncio
import argparse
import logging
import time
import sys
import os
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import get_async_session
from src.services.vectorization_service import BERTVectorizationService
from src.services.vectorization_update_service import VectorizationUpdateService
from sqlalchemy import text

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('simple_vectorization.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SimpleVectorization:
    """简化版批量向量化处理器"""
    
    def __init__(self, clear_tables: bool = False):
        self.clear_tables = clear_tables
        self.vectorization_service = None
        self.update_service = None
        self.start_time = time.time()
        self.processed_count = 0
        
    async def _get_vectorization_service(self) -> BERTVectorizationService:
        """获取向量化服务实例"""
        if self.vectorization_service is None:
            self.vectorization_service = BERTVectorizationService()
            await self.vectorization_service.load_model()
        return self.vectorization_service
    
    async def _get_update_service(self, session) -> VectorizationUpdateService:
        """获取向量化更新服务实例"""
        if self.update_service is None:
            self.update_service = VectorizationUpdateService(session)
        return self.update_service
    
    async def _clear_vector_tables(self, session):
        """清空向量表"""
        if not self.clear_tables:
            return
            
        logger.info("清空向量表...")
        
        # 清空所有向量表
        tables = [
            'content_segment_vectors',
            'article_vectors', 
            'comment_vectors'
        ]
        
        for table in tables:
            try:
                await session.exec(text(f"DELETE FROM {table}"))
                logger.info(f"已清空表 {table}")
            except Exception as e:
                logger.warning(f"清空表 {table} 失败: {e}")
        
        await session.commit()
        logger.info("向量表清空完成")
    
    async def _get_resume_point(self, session) -> Tuple[int, int]:
        """获取恢复点（已处理的最大ID）"""
        try:
            # 获取文章向量化的最大ID
            result = await session.exec(text("""
                SELECT COALESCE(MAX(projectitem_id), 0) 
                FROM article_vectors
            """))
            max_article_id = result.fetchone()[0]
            
            # 获取评论向量化的最大ID
            result = await session.exec(text("""
                SELECT COALESCE(MAX(post_id), 0) 
                FROM comment_vectors
            """))
            max_comment_id = result.fetchone()[0]
            
            logger.info(f"恢复点: 文章ID {max_article_id}, 评论ID {max_comment_id}")
            return max_article_id, max_comment_id
        except Exception as e:
            logger.warning(f"获取恢复点失败: {e}")
            return 0, 0
    
    async def _count_total_records(self, session) -> Tuple[int, int]:
        """计算总记录数"""
        # 计算文章数量
        result = await session.exec(text("""
            SELECT COUNT(*) FROM projectitem WHERE status = 1
        """))
        article_count = result.fetchone()[0]
        
        # 计算评论数量
        result = await session.exec(text("""
            SELECT COUNT(*) FROM post WHERE status = 1
        """))
        comment_count = result.fetchone()[0]
        
        return article_count, comment_count
    
    async def _vectorize_articles(self, session, start_id: int = 0, total_articles: int = 0):
        """向量化文章"""
        logger.info(f"开始向量化文章，起始ID: {start_id}")
        
        # 获取需要向量化的文章
        query = text("""
            SELECT id, name, comment, userid, createtime
            FROM projectitem 
            WHERE status = 1 AND id > :start_id
            ORDER BY id
        """)
        
        result = await session.exec(query, {"start_id": start_id})
        articles = result.fetchall()
        
        if not articles:
            logger.info("没有需要向量化的文章")
            return
        
        update_service = await self._get_update_service(session)
        processed = 0
        
        for article in articles:
            try:
                article_id, title, content, user_id, create_time = article
                
                # 向量化文章
                success = await update_service.update_article_vectors(
                    article_id, title, content
                )
                
                if success:
                    processed += 1
                    self.processed_count += 1
                    
                    # 每5条记录显示进度
                    if processed % 5 == 0:
                        await self._show_progress("文章", processed, article_id, total_articles)
                else:
                    logger.error(f"文章 {article_id} 向量化失败")
                    
            except Exception as e:
                logger.error(f"处理文章 {article_id} 时出错: {e}")
                continue
        
        logger.info(f"文章向量化完成，处理了 {processed} 条记录")
    
    async def _vectorize_comments(self, session, start_id: int = 0, total_comments: int = 0):
        """向量化评论"""
        logger.info(f"开始向量化评论，起始ID: {start_id}")
        
        # 获取需要向量化的评论
        query = text("""
            SELECT id, subject, comment, userid, posttime, projectitem_id
            FROM post 
            WHERE status = 1 AND id > :start_id
            ORDER BY id
        """)
        
        result = await session.exec(query, {"start_id": start_id})
        comments = result.fetchall()
        
        if not comments:
            logger.info("没有需要向量化的评论")
            return
        
        update_service = await self._get_update_service(session)
        processed = 0
        
        for comment in comments:
            try:
                comment_id, subject, content, user_id, post_time, article_id = comment
                
                # 向量化评论
                success = await update_service.update_comment_vectors(
                    comment_id, subject, content, article_id
                )
                
                if success:
                    processed += 1
                    self.processed_count += 1
                    
                    # 每5条记录显示进度
                    if processed % 5 == 0:
                        await self._show_progress("评论", processed, comment_id, total_comments)
                else:
                    logger.error(f"评论 {comment_id} 向量化失败")
                    
            except Exception as e:
                logger.error(f"处理评论 {comment_id} 时出错: {e}")
                continue
        
        logger.info(f"评论向量化完成，处理了 {processed} 条记录")
    
    async def _show_progress(self, data_type: str, processed: int, current_id: int, total: int):
        """显示进度信息"""
        if total > 0:
            percentage = (processed / total) * 100
            elapsed_time = time.time() - self.start_time
            
            logger.info(
                f"{data_type}向量化进度 - "
                f"已完成: {processed}/{total} ({percentage:.1f}%) - "
                f"当前ID: {current_id} - 用时: {elapsed_time:.1f}秒"
            )
    
    async def run(self):
        """运行向量化任务"""
        try:
            logger.info("开始运行向量化任务")
            
            async for session in get_async_session():
                try:
                    # 清空向量表（如果需要）
                    await self._clear_vector_tables(session)
                    
                    # 计算总记录数
                    article_count, comment_count = await self._count_total_records(session)
                    total_records = article_count + comment_count
                    logger.info(f"总记录数: {total_records} (文章: {article_count}, 评论: {comment_count})")
                    
                    # 获取恢复点
                    max_article_id, max_comment_id = await self._get_resume_point(session)
                    
                    # 向量化文章
                    await self._vectorize_articles(session, max_article_id, article_count)
                    
                    # 向量化评论
                    await self._vectorize_comments(session, max_comment_id, comment_count)
                    
                    logger.info("完成所有任务")
                    break
                    
                except Exception as e:
                    logger.error(f"数据库操作出错: {e}")
                    # 回滚事务
                    await session.rollback()
                    raise
                finally:
                    # 确保会话正确关闭
                    await session.close()
                
        except Exception as e:
            logger.error(f"运行出错: {e}")
            raise

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='简化版存量数据向量化脚本')
    parser.add_argument('--clear-tables', action='store_true',
                       help='在向量化前清空所有向量表')
    parser.add_argument('--resume', action='store_true',
                       help='从中断点恢复运行')
    parser.add_argument('--articles-only', action='store_true',
                       help='只向量化文章')
    parser.add_argument('--comments-only', action='store_true',
                       help='只向量化评论')
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("简化版存量数据向量化脚本启动")
    logger.info(f"清空向量表: {args.clear_tables}")
    logger.info(f"恢复模式: {args.resume}")
    logger.info("=" * 60)
    
    # 创建向量化处理器
    processor = SimpleVectorization(clear_tables=args.clear_tables)
    
    try:
        # 运行异步任务
        asyncio.run(processor.run())
        
        # 显示最终统计
        elapsed_time = time.time() - processor.start_time
        logger.info("=" * 60)
        logger.info("向量化完成统计:")
        logger.info(f"已完成: {processor.processed_count}")
        logger.info(f"总用时: {elapsed_time:.1f}秒")
        if processor.processed_count > 0:
            avg_time = elapsed_time / processor.processed_count
            logger.info(f"平均每条记录: {avg_time:.2f}秒")
        logger.info("=" * 60)
        
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在安全退出...")
        logger.info(f"已处理 {processor.processed_count} 条记录")
    except Exception as e:
        logger.error(f"运行出错: {e}")
        raise

if __name__ == "__main__":
    main()
