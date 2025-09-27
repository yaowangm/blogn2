"""
评论处理器

提供评论创建、删除等操作的统一处理逻辑。
"""

from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import HTTPException, Request
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models.post import Post
from src.repositories.post_repository import PostRepository
from src.repositories.project_item_repository import ProjectItemRepository
from src.utils.cache import clear_article_detail_cache, clear_article_comments_cache
from src.utils.time_utils import TimeUtils


class CommentHandler:
    """评论处理器类"""
    
    @staticmethod
    async def create_comment(
        article_id: int,
        comment_data: Dict[str, Any],
        request: Request,
        session: AsyncSession,
        current_user: Optional[Dict[str, Any]] = None,
        require_auth: bool = False
    ) -> Dict[str, Any]:
        """
        创建评论的通用方法
        
        Args:
            article_id: 文章ID
            comment_data: 评论数据
            request: 请求对象
            session: 数据库会话
            current_user: 当前用户信息（可选）
            require_auth: 是否要求用户登录
            
        Returns:
            Dict[str, Any]: 创建结果
        """
        post_repo = PostRepository(session)
        project_item_repo = ProjectItemRepository(session)
        
        # 验证文章是否存在
        article = await project_item_repo.get_by_id(article_id)
        if not article:
            raise HTTPException(status_code=404, detail="文章不存在")
        
        # 验证评论权限
        allowpost = article.allowpost or 1
        is_logged_in = current_user is not None
        
        if allowpost == 3:  # 不允许任何评论
            raise HTTPException(status_code=403, detail="此文章已关闭评论功能")
        elif allowpost == 2 and not is_logged_in:  # 只允许登录用户评论
            raise HTTPException(status_code=401, detail="需要登录后才能发表评论")
        elif require_auth and not is_logged_in:  # 要求登录但用户未登录
            raise HTTPException(status_code=401, detail="需要登录后才能发表评论")
        
        # 验证评论数据
        content = comment_data.get("content")
        if not content or not content.strip():
            raise HTTPException(status_code=400, detail="评论内容不能为空")
        
        # 获取用户ID
        user_id = None
        if is_logged_in:
            user_id = current_user.get("id")
        elif allowpost == 1 and not require_auth:  # 允许匿名评论
            user_id = comment_data.get("user_id", 0)
        
        if user_id is None:
            raise HTTPException(status_code=400, detail="用户ID不能为空")
        
        # 获取客户端IP地址
        client_ip = request.client.host if request.client else "127.0.0.1"
        
        # 计算内容大小（字节数）
        content_bytes = content.strip().encode('utf-8')
        content_size = len(content_bytes)
        
        # 创建评论
        comment = Post(
            folderid=0,  # 文件夹ID为0
            projectitemid=article_id,
            userid=user_id,
            subject=comment_data.get("subject", ""),
            content=content.strip(),
            size=content_size,  # 内容大小（字节）
            hits=0,  # 访问次数初始为0
            userip=client_ip,  # 用户IP地址
            posttime=TimeUtils.now_utc(),
            status=1,  # 1表示正常状态
            rootid=0,  # 主评论的rootid为0
            replycount=0  # 新评论的回复数为0
        )
        
        try:
            # 创建评论（包含向量化处理）
            await post_repo.create(comment)
            
            # 更新文章的评论数
            await project_item_repo.increment_comment_count(article_id)
            
            # 提交事务（所有操作在同一个事务中）
            await session.commit()
            
            # 失效相关缓存
            await clear_article_detail_cache(article_id)
            await clear_article_comments_cache(article_id)
            
            return {
                "success": True,
                "message": "评论创建成功",
                "comment_id": comment.id
            }
            
        except Exception as e:
            # 回滚事务
            await session.rollback()
            raise e
    
    @staticmethod
    async def delete_comment(
        article_id: int,
        comment_id: int,
        session: AsyncSession,
        current_user: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        删除评论的通用方法
        
        Args:
            article_id: 文章ID
            comment_id: 评论ID
            session: 数据库会话
            current_user: 当前用户信息（可选）
            
        Returns:
            Dict[str, Any]: 删除结果
        """
        post_repo = PostRepository(session)
        project_item_repo = ProjectItemRepository(session)
        
        # 验证文章是否存在
        article = await project_item_repo.get_by_id(article_id)
        if not article:
            raise HTTPException(status_code=404, detail="文章不存在")
        
        # 验证评论是否存在
        comment = await post_repo.get_by_id(comment_id)
        if not comment:
            raise HTTPException(status_code=404, detail="评论不存在")
        
        # 验证评论是否属于该文章
        if comment.projectitemid != article_id:
            raise HTTPException(status_code=400, detail="评论不属于该文章")
        
        # 权限检查：只有管理员或文章作者可以删除评论
        if not current_user:
            raise HTTPException(status_code=401, detail="需要登录才能删除评论")
        
        current_user_id = current_user.get("id")
        is_admin = current_user.get("state") == 10
        is_article_author = article.userid == current_user_id
        
        if not (is_admin or is_article_author):
            raise HTTPException(status_code=403, detail="无权限删除该评论")
        
        try:
            # 删除评论向量化数据
            try:
                from src.services.vectorization_update_service import get_vectorization_update_service
                vectorization_service = get_vectorization_update_service(session)
                
                # 删除评论向量
                await vectorization_service.delete_comment_vectors(comment_id)
                
            except Exception as e:
                # 向量化删除失败不影响评论删除成功
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"删除评论 {comment_id} 向量化数据失败: {e}")
            
            # 删除评论
            await post_repo.delete(comment_id)
            
            # 更新文章的评论数
            await project_item_repo.decrement_comment_count(article_id)
            
            # 提交事务（所有操作在同一个事务中）
            await session.commit()
            
            # 失效相关缓存
            await clear_article_detail_cache(article_id)
            await clear_article_comments_cache(article_id)
            
            return {
                "success": True,
                "message": "评论删除成功"
            }
            
        except Exception as e:
            # 回滚事务
            await session.rollback()
            raise e

