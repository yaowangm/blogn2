"""
统计服务
提供实时统计计算功能，确保统计数据始终准确
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func
from typing import Optional
from src.models.post import Post
from src.models.project_item import ProjectItem
from src.models.project import Project
from src.models.folder import Folder
from src.models.user import User
from src.models.glovar import Glovar
from src.utils.time_utils import TimeUtils


class StatsService:
    """统计服务类"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    # ==============================================
    # 评论相关统计
    # ==============================================
    
    async def increment_post_reply_count(self, root_post_id: int) -> bool:
        """
        增加评论的回复数
        
        Args:
            root_post_id: 根评论ID
            
        Returns:
            bool: 更新是否成功
        """
        try:
            statement = select(Post).where(Post.id == root_post_id)
            result = await self.session.exec(statement)
            post = result.first()
            
            if post:
                post.replycount = (post.replycount or 0) + 1
                post.lastreplytime = TimeUtils.now_utc()
                await self.session.commit()
                await self.session.refresh(post)
                return True
            return False
        except Exception as e:
            await self.session.rollback()
            return False
    
    async def decrement_post_reply_count(self, root_post_id: int) -> bool:
        """
        减少评论的回复数
        
        Args:
            root_post_id: 根评论ID
            
        Returns:
            bool: 更新是否成功
        """
        try:
            statement = select(Post).where(Post.id == root_post_id)
            result = await self.session.exec(statement)
            post = result.first()
            
            if post and post.replycount and post.replycount > 0:
                post.replycount -= 1
                # 重新计算最后回复时间
                if post.replycount > 0:
                    latest_reply = await self._get_latest_reply(root_post_id)
                    if latest_reply:
                        post.lastreplytime = latest_reply.posttime
                        post.lastreplyid = latest_reply.userid
                else:
                    post.lastreplytime = None
                    post.lastreplyid = None
                
                await self.session.commit()
                await self.session.refresh(post)
                return True
            return False
        except Exception as e:
            await self.session.rollback()
            return False
    
    async def _get_latest_reply(self, root_post_id: int) -> Optional[Post]:
        """获取最新的回复"""
        statement = (
            select(Post)
            .where(Post.rootid == root_post_id)
            .order_by(Post.posttime.desc())
            .limit(1)
        )
        result = await self.session.exec(statement)
        return result.first()
    
    # ==============================================
    # 文章评论统计
    # ==============================================
    
    async def increment_article_comment_count(self, article_id: int) -> bool:
        """
        增加文章的评论数
        
        Args:
            article_id: 文章ID
            
        Returns:
            bool: 更新是否成功
        """
        try:
            statement = select(ProjectItem).where(ProjectItem.id == article_id)
            result = await self.session.exec(statement)
            article = result.first()
            
            if article:
                article.commentcount = (article.commentcount or 0) + 1
                article.updatetime = TimeUtils.now_utc()
                await self.session.commit()
                await self.session.refresh(article)
                return True
            return False
        except Exception as e:
            await self.session.rollback()
            return False
    
    async def decrement_article_comment_count(self, article_id: int) -> bool:
        """
        减少文章的评论数
        
        Args:
            article_id: 文章ID
            
        Returns:
            bool: 更新是否成功
        """
        try:
            statement = select(ProjectItem).where(ProjectItem.id == article_id)
            result = await self.session.exec(statement)
            article = result.first()
            
            if article and article.commentcount and article.commentcount > 0:
                article.commentcount -= 1
                article.updatetime = TimeUtils.now_utc()
                await self.session.commit()
                await self.session.refresh(article)
                return True
            return False
        except Exception as e:
            await self.session.rollback()
            return False
    
    # ==============================================
    # 分类文章统计
    # ==============================================
    
    async def increment_folder_record_count(self, folder_id: int) -> bool:
        """
        增加分类的文章数
        
        Args:
            folder_id: 分类ID
            
        Returns:
            bool: 更新是否成功
        """
        try:
            statement = select(Folder).where(Folder.id == folder_id)
            result = await self.session.exec(statement)
            folder = result.first()
            
            if folder:
                folder.recordcount = (folder.recordcount or 0) + 1
                await self.session.commit()
                await self.session.refresh(folder)
                return True
            return False
        except Exception as e:
            await self.session.rollback()
            return False
    
    async def decrement_folder_record_count(self, folder_id: int) -> bool:
        """
        减少分类的文章数
        
        Args:
            folder_id: 分类ID
            
        Returns:
            bool: 更新是否成功
        """
        try:
            statement = select(Folder).where(Folder.id == folder_id)
            result = await self.session.exec(statement)
            folder = result.first()
            
            if folder and folder.recordcount and folder.recordcount > 0:
                folder.recordcount -= 1
                await self.session.commit()
                await self.session.refresh(folder)
                return True
            return False
        except Exception as e:
            await self.session.rollback()
            return False
    
    # ==============================================
    # 分类评论统计
    # ==============================================
    
    async def increment_folder_post_count(self, folder_id: int) -> bool:
        """
        增加分类的评论数
        
        Args:
            folder_id: 分类ID
            
        Returns:
            bool: 更新是否成功
        """
        try:
            statement = select(Folder).where(Folder.id == folder_id)
            result = await self.session.exec(statement)
            folder = result.first()
            
            if folder:
                folder.postcount = (folder.postcount or 0) + 1
                await self.session.commit()
                await self.session.refresh(folder)
                return True
            return False
        except Exception as e:
            await self.session.rollback()
            return False
    
    async def decrement_folder_post_count(self, folder_id: int) -> bool:
        """
        减少分类的评论数
        
        Args:
            folder_id: 分类ID
            
        Returns:
            bool: 更新是否成功
        """
        try:
            statement = select(Folder).where(Folder.id == folder_id)
            result = await self.session.exec(statement)
            folder = result.first()
            
            if folder and folder.postcount and folder.postcount > 0:
                folder.postcount -= 1
                await self.session.commit()
                await self.session.refresh(folder)
                return True
            return False
        except Exception as e:
            await self.session.rollback()
            return False
    
    # ==============================================
    # 项目统计
    # ==============================================
    
    async def increment_project_record_count(self, project_id: int) -> bool:
        """
        增加项目的文章数
        
        Args:
            project_id: 项目ID
            
        Returns:
            bool: 更新是否成功
        """
        try:
            statement = select(Project).where(Project.id == project_id)
            result = await self.session.exec(statement)
            project = result.first()
            
            if project:
                project.recordcount = (project.recordcount or 0) + 1
                project.updatetime = TimeUtils.now_utc()
                await self.session.commit()
                await self.session.refresh(project)
                return True
            return False
        except Exception as e:
            await self.session.rollback()
            return False
    
    async def decrement_project_record_count(self, project_id: int) -> bool:
        """
        减少项目的文章数
        
        Args:
            project_id: 项目ID
            
        Returns:
            bool: 更新是否成功
        """
        try:
            statement = select(Project).where(Project.id == project_id)
            result = await self.session.exec(statement)
            project = result.first()
            
            if project and project.recordcount and project.recordcount > 0:
                project.recordcount -= 1
                project.updatetime = TimeUtils.now_utc()
                await self.session.commit()
                await self.session.refresh(project)
                return True
            return False
        except Exception as e:
            await self.session.rollback()
            return False
    
    async def increment_project_comment_count(self, project_id: int) -> bool:
        """
        增加项目的评论数
        
        Args:
            project_id: 项目ID
            
        Returns:
            bool: 更新是否成功
        """
        try:
            statement = select(Project).where(Project.id == project_id)
            result = await self.session.exec(statement)
            project = result.first()
            
            if project:
                project.commentcount = (project.commentcount or 0) + 1
                project.updatetime = TimeUtils.now_utc()
                await self.session.commit()
                await self.session.refresh(project)
                return True
            return False
        except Exception as e:
            await self.session.rollback()
            return False
    
    async def decrement_project_comment_count(self, project_id: int) -> bool:
        """
        减少项目的评论数
        
        Args:
            project_id: 项目ID
            
        Returns:
            bool: 更新是否成功
        """
        try:
            statement = select(Project).where(Project.id == project_id)
            result = await self.session.exec(statement)
            project = result.first()
            
            if project and project.commentcount and project.commentcount > 0:
                project.commentcount -= 1
                project.updatetime = TimeUtils.now_utc()
                await self.session.commit()
                await self.session.refresh(project)
                return True
            return False
        except Exception as e:
            await self.session.rollback()
            return False
    
    # ==============================================
    # 全局统计
    # ==============================================
    
    async def increment_user_count(self) -> bool:
        """增加用户总数"""
        return await self._update_glovar_count('usercount', 1)
    
    async def decrement_user_count(self) -> bool:
        """减少用户总数"""
        return await self._update_glovar_count('usercount', -1)
    
    async def increment_project_count(self) -> bool:
        """增加项目总数"""
        return await self._update_glovar_count('projectcount', 1)
    
    async def decrement_project_count(self) -> bool:
        """减少项目总数"""
        return await self._update_glovar_count('projectcount', -1)
    
    async def increment_project_item_count(self) -> bool:
        """增加文章总数"""
        return await self._update_glovar_count('projectitemcount', 1)
    
    async def decrement_project_item_count(self) -> bool:
        """减少文章总数"""
        return await self._update_glovar_count('projectitemcount', -1)
    
    async def _update_glovar_count(self, varname: str, delta: int) -> bool:
        """
        更新全局统计数量
        
        Args:
            varname: 变量名
            delta: 变化量（正数增加，负数减少）
            
        Returns:
            bool: 更新是否成功
        """
        try:
            statement = select(Glovar).where(Glovar.varname == varname)
            result = await self.session.exec(statement)
            glovar = result.first()
            
            if glovar:
                glovar.varvalue = (glovar.varvalue or 0) + delta
                # 确保不会变成负数
                if glovar.varvalue < 0:
                    glovar.varvalue = 0
            else:
                # 如果记录不存在，创建新记录
                glovar = Glovar(varname=varname, varvalue=max(0, delta))
                self.session.add(glovar)
            
            await self.session.commit()
            await self.session.refresh(glovar)
            return True
        except Exception as e:
            await self.session.rollback()
            return False
    
    # ==============================================
    # 复合操作
    # ==============================================
    
    async def handle_comment_creation(self, comment: Post) -> bool:
        """
        处理评论创建时的统计更新
        
        Args:
            comment: 评论对象
            
        Returns:
            bool: 更新是否成功
        """
        try:
            # 1. 如果是回复，增加根评论的回复数
            if comment.rootid and comment.rootid > 0:
                await self.increment_post_reply_count(comment.rootid)
            
            # 2. 增加文章的评论数
            if comment.projectitemid and comment.projectitemid > 0:
                await self.increment_article_comment_count(comment.projectitemid)
                
                # 获取文章信息以更新项目统计
                article_statement = select(ProjectItem).where(ProjectItem.id == comment.projectitemid)
                article_result = await self.session.exec(article_statement)
                article = article_result.first()
                
                if article and article.projectid:
                    # 3. 增加项目的评论数
                    await self.increment_project_comment_count(article.projectid)
                    
                    # 4. 增加分类的评论数
                    if article.folderid and article.folderid > 0:
                        await self.increment_folder_post_count(article.folderid)
            
            return True
        except Exception as e:
            await self.session.rollback()
            return False
    
    async def handle_comment_deletion(self, comment: Post) -> bool:
        """
        处理评论删除时的统计更新
        
        Args:
            comment: 评论对象
            
        Returns:
            bool: 更新是否成功
        """
        try:
            # 1. 如果是回复，减少根评论的回复数
            if comment.rootid and comment.rootid > 0:
                await self.decrement_post_reply_count(comment.rootid)
            
            # 2. 减少文章的评论数
            if comment.projectitemid and comment.projectitemid > 0:
                await self.decrement_article_comment_count(comment.projectitemid)
                
                # 获取文章信息以更新项目统计
                article_statement = select(ProjectItem).where(ProjectItem.id == comment.projectitemid)
                article_result = await self.session.exec(article_statement)
                article = article_result.first()
                
                if article and article.projectid:
                    # 3. 减少项目的评论数
                    await self.decrement_project_comment_count(article.projectid)
                    
                    # 4. 减少分类的评论数
                    if article.folderid and article.folderid > 0:
                        await self.decrement_folder_post_count(article.folderid)
            
            return True
        except Exception as e:
            await self.session.rollback()
            return False
    
    async def handle_article_creation(self, article: ProjectItem) -> bool:
        """
        处理文章创建时的统计更新
        
        Args:
            article: 文章对象
            
        Returns:
            bool: 更新是否成功
        """
        try:
            # 1. 增加项目的文章数
            if article.projectid:
                await self.increment_project_record_count(article.projectid)
            
            # 2. 增加分类的文章数
            if article.folderid and article.folderid > 0:
                await self.increment_folder_record_count(article.folderid)
            
            # 3. 增加全局文章数
            await self.increment_project_item_count()
            
            return True
        except Exception as e:
            await self.session.rollback()
            return False
    
    async def handle_article_deletion(self, article: ProjectItem) -> bool:
        """
        处理文章删除时的统计更新
        
        Args:
            article: 文章对象
            
        Returns:
            bool: 更新是否成功
        """
        try:
            # 1. 减少项目的文章数
            if article.projectid:
                await self.decrement_project_record_count(article.projectid)
            
            # 2. 减少分类的文章数
            if article.folderid and article.folderid > 0:
                await self.decrement_folder_record_count(article.folderid)
            
            # 3. 减少全局文章数
            await self.decrement_project_item_count()
            
            return True
        except Exception as e:
            await self.session.rollback()
            return False
    
    async def handle_article_folder_change(self, article: ProjectItem, old_folder_id: int, new_folder_id: int) -> bool:
        """
        处理文章分类变更时的统计更新
        
        Args:
            article: 文章对象
            old_folder_id: 旧分类ID
            new_folder_id: 新分类ID
            
        Returns:
            bool: 更新是否成功
        """
        try:
            # 1. 减少旧分类的文章数
            if old_folder_id and old_folder_id > 0:
                await self.decrement_folder_record_count(old_folder_id)
            
            # 2. 增加新分类的文章数
            if new_folder_id and new_folder_id > 0:
                await self.increment_folder_record_count(new_folder_id)
            
            return True
        except Exception as e:
            await self.session.rollback()
            return False
