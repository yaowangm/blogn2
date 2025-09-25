#!/usr/bin/env python3
"""
存量数据向量化脚本

用于将现有的文章和评论数据批量向量化，填充向量表。
支持多进程、进度显示、中断恢复等功能。

使用方法:
    python scripts/batch_vectorization.py --processes 4 --clear-tables
    python scripts/batch_vectorization.py --processes 8 --resume
"""

import asyncio
import argparse
import logging
import warnings

# 忽略transformers库的弃用警告
warnings.filterwarnings('ignore', category=UserWarning, module='transformers')
import time
import sys
import os
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from multiprocessing import Process, Queue, Value
import signal

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
        logging.FileHandler('batch_vectorization.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BatchVectorization:
    """批量向量化处理器"""
    
    def __init__(self, process_id: int, queue: Queue, progress_counter: Value, 
                 total_count: Value, start_time: Value, clear_tables: bool = False,
                 articles_only: bool = False, comments_only: bool = False, total_processes: int = 1,
                 user_id: int = None, article_id_list: list = None):
        self.process_id = process_id
        self.queue = queue
        self.progress_counter = progress_counter
        self.total_count = total_count
        self.start_time = start_time
        self.clear_tables = clear_tables
        self.articles_only = articles_only
        self.comments_only = comments_only
        self.total_processes = total_processes
        self.user_id = user_id
        self.article_id_list = article_id_list
        self.vectorization_service = None
        self.update_service = None
        
    async def _get_vectorization_service(self) -> BERTVectorizationService:
        """获取向量化服务实例"""
        if self.vectorization_service is None:
            # 确保使用修复后的向量化服务（包含向量归一化）
            self.vectorization_service = BERTVectorizationService()
            await self.vectorization_service.load_model()
            logger.info(f"进程 {self.process_id}: 已加载修复后的向量化服务（包含向量归一化）")
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
            
        logger.info(f"进程 {self.process_id}: 清空向量表...")
        
        # 清空所有向量表
        tables = [
            'content_segment_vectors',
            'article_vectors', 
            'comment_vectors'
        ]
        
        for table in tables:
            try:
                await session.execute(text(f"DELETE FROM {table}"))
                logger.info(f"进程 {self.process_id}: 已清空表 {table}")
            except Exception as e:
                logger.warning(f"进程 {self.process_id}: 清空表 {table} 失败: {e}")
        
        await session.commit()
        logger.info(f"进程 {self.process_id}: 向量表清空完成")
    
    async def _get_resume_point(self, session) -> Tuple[int, int]:
        """获取恢复点（已处理的最大ID）"""
        try:
            # 获取文章向量化的最大ID
            result = await session.execute(text("""
                SELECT COALESCE(MAX(projectitem_id), 0) 
                FROM article_vectors
            """))
            max_article_id = result.fetchone()[0]
            
            # 获取评论向量化的最大ID
            result = await session.execute(text("""
                SELECT COALESCE(MAX(post_id), 0) 
                FROM comment_vectors
            """))
            max_comment_id = result.fetchone()[0]
            
            return max_article_id, max_comment_id
        except Exception as e:
            logger.warning(f"进程 {self.process_id}: 获取恢复点失败: {e}")
            return 0, 0
    
    async def _vectorize_articles(self, session, start_id: int = 0):
        """向量化文章"""
        if self.article_id_list is not None:
            logger.info(f"进程 {self.process_id}: 开始向量化指定文章ID列表: {self.article_id_list}")
        elif self.user_id is not None:
            logger.info(f"进程 {self.process_id}: 开始向量化用户 {self.user_id} 的文章，起始ID: {start_id}")
        else:
            logger.info(f"进程 {self.process_id}: 开始向量化文章，起始ID: {start_id}")
        
        # 构建查询条件
        if self.article_id_list is not None:
            # 如果指定了文章ID列表，只处理这些文章
            # 将文章ID列表分配给不同的进程
            process_articles = [aid for i, aid in enumerate(self.article_id_list) 
                              if i % self.total_processes == self.process_id]
            
            if not process_articles:
                logger.info(f"进程 {self.process_id}: 没有分配给该进程的文章")
                return
            
            query = text("""
                SELECT id, name, comment, userid, createtime
                FROM projectitem 
                WHERE status = 1 AND id = ANY(:article_ids)
                ORDER BY id
            """)
            query_params = {
                "article_ids": process_articles
            }
        elif self.user_id is not None:
            # 如果指定了用户ID，只处理该用户的文章
            query = text("""
                SELECT id, name, comment, userid, createtime
                FROM projectitem 
                WHERE status = 1 AND userid = :user_id AND id > :start_id AND id % :total_processes = :process_id
                ORDER BY id
            """)
            query_params = {
                "user_id": self.user_id,
                "start_id": start_id,
                "total_processes": self.total_processes,
                "process_id": self.process_id
            }
        else:
            # 处理所有用户的文章
            query = text("""
                SELECT id, name, comment, userid, createtime
                FROM projectitem 
                WHERE status = 1 AND id > :start_id AND id % :total_processes = :process_id
                ORDER BY id
            """)
            query_params = {
                "start_id": start_id,
                "total_processes": self.total_processes,
                "process_id": self.process_id
            }
        
        result = await session.execute(query, query_params)
        articles = result.fetchall()
        
        if not articles:
            logger.info(f"进程 {self.process_id}: 没有需要向量化的文章")
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
                    with self.progress_counter.get_lock():
                        self.progress_counter.value += 1
                    
                    # 每5条记录显示进度
                    if processed % 5 == 0:
                        await self._show_progress("文章", processed, article_id)
                else:
                    logger.error(f"进程 {self.process_id}: 文章 {article_id} 向量化失败")
                    
            except Exception as e:
                logger.error(f"进程 {self.process_id}: 处理文章 {article_id} 时出错: {e}")
                continue
    
    async def _vectorize_comments(self, session, start_id: int = 0):
        """向量化评论"""
        # 如果指定了文章ID列表，跳过评论处理（因为只处理指定文章）
        if self.article_id_list is not None:
            logger.info(f"进程 {self.process_id}: 跳过评论处理（指定了文章ID列表）")
            return
            
        logger.info(f"进程 {self.process_id}: 开始向量化评论，起始ID: {start_id}")
        
        # 获取需要向量化的评论，按进程ID分配数据范围
        # 使用模运算确保不同进程处理不同的数据
        query = text("""
            SELECT id, subject, content, userid, posttime, projectitemid
            FROM post 
            WHERE status = 1 AND id > :start_id AND id % :total_processes = :process_id
            ORDER BY id
        """)
        
        result = await session.execute(query, {
            "start_id": start_id,
            "total_processes": self.total_processes,
            "process_id": self.process_id
        })
        comments = result.fetchall()
        
        if not comments:
            logger.info(f"进程 {self.process_id}: 没有需要向量化的评论")
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
                    with self.progress_counter.get_lock():
                        self.progress_counter.value += 1
                    
                    # 每5条记录显示进度
                    if processed % 5 == 0:
                        await self._show_progress("评论", processed, comment_id)
                else:
                    logger.error(f"进程 {self.process_id}: 评论 {comment_id} 向量化失败")
                    
            except Exception as e:
                logger.error(f"进程 {self.process_id}: 处理评论 {comment_id} 时出错: {e}")
                continue
    
    async def _show_progress(self, data_type: str, processed: int, current_id: int):
        """显示进度信息"""
        with self.progress_counter.get_lock():
            completed = self.progress_counter.value
            total = self.total_count.value
        
        if total > 0:
            percentage = (completed / total) * 100
            elapsed_time = time.time() - self.start_time.value
            
            logger.info(
                f"进程 {self.process_id}: {data_type}向量化进度 - "
                f"已完成: {completed}/{total} ({percentage:.1f}%) - "
                f"当前ID: {current_id} - 用时: {elapsed_time:.1f}秒"
            )
    
    async def run(self):
        """运行向量化任务（使用共享连接）"""
        try:
            logger.info(f"进程 {self.process_id}: 开始运行")
            
            # 为每个进程创建独立的数据库连接
            async for session in get_async_session():
                try:
                    # 清空向量表（如果需要）
                    await self._clear_vector_tables(session)
                    
                    # 获取恢复点
                    max_article_id, max_comment_id = await self._get_resume_point(session)
                    
                    # 向量化文章
                    await self._vectorize_articles(session, max_article_id)
                    
                    # 向量化评论
                    await self._vectorize_comments(session, max_comment_id)
                    
                    logger.info(f"进程 {self.process_id}: 完成所有任务")
                    break
                    
                except Exception as e:
                    logger.error(f"进程 {self.process_id}: 数据库操作出错: {e}")
                    # 回滚事务
                    await session.rollback()
                    raise
                finally:
                    # 确保会话正确关闭
                    await session.close()
                
        except Exception as e:
            logger.error(f"进程 {self.process_id}: 运行出错: {e}")
            raise
    
    async def run_with_session(self, session):
        """使用独立会话运行向量化任务"""
        try:
            logger.info(f"进程 {self.process_id}: 开始运行（独立连接）")
            
            # 清空向量表（如果需要）
            await self._clear_vector_tables(session)
            
            # 获取恢复点
            max_article_id, max_comment_id = await self._get_resume_point(session)
            
            # 根据参数决定处理内容
            if not self.comments_only:
                # 向量化文章
                await self._vectorize_articles(session, max_article_id)
            
            if not self.articles_only:
                # 向量化评论
                await self._vectorize_comments(session, max_comment_id)
            
            logger.info(f"进程 {self.process_id}: 完成所有任务")
            
        except Exception as e:
            logger.error(f"进程 {self.process_id}: 运行出错: {e}")
            # 回滚事务
            await session.rollback()
            raise

def worker_process(process_id: int, queue: Queue, progress_counter: Value, 
                  total_count: Value, start_time: Value, clear_tables: bool = False,
                  articles_only: bool = False, comments_only: bool = False, total_processes: int = 1,
                  user_id: int = None, article_id_list: list = None):
    """工作进程函数"""
    try:
        # 设置进程标题
        import setproctitle
        setproctitle.setproctitle(f"vectorization_worker_{process_id}")
    except ImportError:
        pass
    
    # 为每个进程创建独立的数据库连接
    async def run_with_independent_connection():
        # 创建独立的数据库引擎
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        from sqlalchemy.orm import sessionmaker
        
        # 获取数据库URL
        import os
        database_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://blogn:blogn@localhost:5432/blogn")
        
        # 创建独立的引擎
        engine = create_async_engine(database_url, echo=False, future=True)
        
        # 创建独立的会话工厂
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        # 创建批量向量化处理器
        processor = BatchVectorization(
            process_id, queue, progress_counter, total_count, start_time, clear_tables,
            articles_only, comments_only, total_processes, user_id, article_id_list
        )
        
        try:
            # 使用独立的数据库连接运行
            async with async_session() as session:
                await processor.run_with_session(session)
        finally:
            # 关闭引擎
            await engine.dispose()
    
    # 运行异步任务
    asyncio.run(run_with_independent_connection())

def signal_handler(signum, frame):
    """信号处理器"""
    logger.info("收到中断信号，正在安全退出...")
    sys.exit(0)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='存量数据向量化脚本')
    parser.add_argument('--processes', type=int, default=4, 
                       help='进程数量 (默认: 4)')
    parser.add_argument('--clear-tables', action='store_true',
                       help='在向量化前清空所有向量表')
    parser.add_argument('--resume', action='store_true',
                       help='从中断点恢复运行')
    parser.add_argument('--articles-only', action='store_true',
                       help='只向量化文章')
    parser.add_argument('--comments-only', action='store_true',
                       help='只向量化评论')
    parser.add_argument('--user-id', type=int, default=None,
                       help='指定用户ID，只向量化该用户的文章（与--comments-only互斥）')
    parser.add_argument('--article-ids', type=str, default=None,
                       help='指定文章ID列表，格式：1,2,3,4,5（与--comments-only和--user-id互斥）')
    
    args = parser.parse_args()
    
    # 参数验证
    if args.user_id is not None and args.comments_only:
        logger.error("错误: --user-id 和 --comments-only 不能同时使用")
        sys.exit(1)
    
    if args.user_id is not None and args.user_id <= 0:
        logger.error("错误: --user-id 必须是正整数")
        sys.exit(1)
    
    if args.article_ids is not None and args.comments_only:
        logger.error("错误: --article-ids 和 --comments-only 不能同时使用")
        sys.exit(1)
    
    if args.article_ids is not None and args.user_id is not None:
        logger.error("错误: --article-ids 和 --user-id 不能同时使用")
        sys.exit(1)
    
    # 解析文章ID列表
    article_id_list = None
    if args.article_ids is not None:
        try:
            article_id_list = [int(x.strip()) for x in args.article_ids.split(',') if x.strip()]
            if not article_id_list:
                logger.error("错误: --article-ids 不能为空")
                sys.exit(1)
            if any(id <= 0 for id in article_id_list):
                logger.error("错误: 文章ID必须是正整数")
                sys.exit(1)
        except ValueError:
            logger.error("错误: --article-ids 格式不正确，应为：1,2,3,4,5")
            sys.exit(1)
    
    # 设置信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("=" * 60)
    logger.info("存量数据向量化脚本启动")
    logger.info(f"进程数量: {args.processes}")
    logger.info(f"清空向量表: {args.clear_tables}")
    logger.info(f"恢复模式: {args.resume}")
    if args.user_id is not None:
        logger.info(f"指定用户ID: {args.user_id}")
    if args.article_ids is not None:
        logger.info(f"指定文章ID: {article_id_list}")
    logger.info("=" * 60)
    
    # 创建共享变量
    progress_counter = Value('i', 0)
    total_count = Value('i', 0)
    start_time = Value('d', time.time())
    
    # 计算总记录数
    async def count_total_records():
        async for session in get_async_session():
            total = 0
            article_count = 0
            comment_count = 0
            
            # 根据参数计算相应的记录数
            if not args.comments_only:
                # 计算文章数量
                if article_id_list is not None:
                    # 只计算指定文章ID列表的数量
                    result = await session.execute(text("""
                        SELECT COUNT(*) FROM projectitem WHERE status = 1 AND id = ANY(:article_ids)
                    """), {"article_ids": article_id_list})
                elif args.user_id is not None:
                    # 只计算指定用户的文章数量
                    result = await session.execute(text("""
                        SELECT COUNT(*) FROM projectitem WHERE status = 1 AND userid = :user_id
                    """), {"user_id": args.user_id})
                else:
                    # 计算所有用户的文章数量
                    result = await session.execute(text("""
                        SELECT COUNT(*) FROM projectitem WHERE status = 1
                    """))
                article_count = result.fetchone()[0]
                total += article_count
            
            if not args.articles_only:
                # 计算评论数量
                result = await session.execute(text("""
                    SELECT COUNT(*) FROM post WHERE status = 1
                """))
                comment_count = result.fetchone()[0]
                total += comment_count
            
            with total_count.get_lock():
                total_count.value = total
            
            if article_id_list is not None:
                logger.info(f"指定文章ID {article_id_list} 的记录数: {total} (文章: {article_count}, 评论: {comment_count})")
            elif args.user_id is not None:
                logger.info(f"用户 {args.user_id} 的记录数: {total} (文章: {article_count}, 评论: {comment_count})")
            else:
                logger.info(f"总记录数: {total} (文章: {article_count}, 评论: {comment_count})")
            break
    
    # 运行计数任务
    asyncio.run(count_total_records())
    
    # 创建工作进程
    processes = []
    queue = Queue()
    
    for i in range(args.processes):
        p = Process(
            target=worker_process,
            args=(i, queue, progress_counter, total_count, start_time, args.clear_tables,
                  args.articles_only, args.comments_only, args.processes, args.user_id, article_id_list)
        )
        p.start()
        processes.append(p)
        logger.info(f"启动工作进程 {i}")
    
    try:
        # 等待所有进程完成
        for p in processes:
            p.join()
        
        logger.info("所有进程完成")
        
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在停止所有进程...")
        for p in processes:
            p.terminate()
            p.join()
        logger.info("所有进程已停止")
    
    # 显示最终统计
    elapsed_time = time.time() - start_time.value
    with progress_counter.get_lock():
        completed = progress_counter.value
    
    logger.info("=" * 60)
    logger.info("向量化完成统计:")
    logger.info(f"总记录数: {total_count.value}")
    logger.info(f"已完成: {completed}")
    logger.info(f"总用时: {elapsed_time:.1f}秒")
    if completed > 0:
        avg_time = elapsed_time / completed
        logger.info(f"平均每条记录: {avg_time:.2f}秒")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()