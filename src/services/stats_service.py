"""
统计服务
提供实时统计计算功能，确保统计数据始终准确。

统计更新仅修改当前 session 中的对象，不自行 commit；
由调用方在同一事务内统一提交。
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from typing import Optional
from src.models.post import Post
from src.models.project_item import ProjectItem
from src.models.project import Project
from src.models.folder import Folder
from src.models.glovar import Glovar
from src.repositories.project_repository import ProjectRepository
from src.utils.time_utils import TimeUtils


class StatsService:
    """统计服务类"""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ==============================================
    # 评论相关统计
    # ==============================================

    async def increment_post_reply_count(
        self, root_post_id: int, reply_user_id: Optional[int] = None
    ) -> bool:
        """增加根帖/主评论的回复数"""
        try:
            statement = select(Post).where(Post.id == root_post_id)
            result = await self.session.exec(statement)
            post = result.first()

            if post:
                post.replycount = (post.replycount or 0) + 1
                post.lastreplytime = TimeUtils.now_utc()
                if reply_user_id is not None:
                    post.lastreplyid = reply_user_id
                return True
            return False
        except Exception:
            return False

    async def decrement_post_reply_count(self, root_post_id: int) -> bool:
        """减少根帖/主评论的回复数"""
        try:
            statement = select(Post).where(Post.id == root_post_id)
            result = await self.session.exec(statement)
            post = result.first()

            if post and post.replycount and post.replycount > 0:
                post.replycount -= 1
                if post.replycount > 0:
                    latest_reply = await self._get_latest_reply(root_post_id)
                    if latest_reply:
                        post.lastreplytime = latest_reply.posttime
                        post.lastreplyid = latest_reply.userid
                else:
                    post.lastreplytime = None
                    post.lastreplyid = None
                return True
            return False
        except Exception:
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
        """增加文章的评论数"""
        try:
            statement = select(ProjectItem).where(ProjectItem.id == article_id)
            result = await self.session.exec(statement)
            article = result.first()

            if article:
                article.commentcount = (article.commentcount or 0) + 1
                return True
            return False
        except Exception:
            return False

    async def decrement_article_comment_count(self, article_id: int) -> bool:
        """减少文章的评论数"""
        try:
            statement = select(ProjectItem).where(ProjectItem.id == article_id)
            result = await self.session.exec(statement)
            article = result.first()

            if article and article.commentcount and article.commentcount > 0:
                article.commentcount -= 1
                return True
            return False
        except Exception:
            return False

    # ==============================================
    # 分类文章统计
    # ==============================================

    async def increment_folder_record_count(self, folder_id: int) -> bool:
        """增加分类的文章数"""
        try:
            statement = select(Folder).where(Folder.id == folder_id)
            result = await self.session.exec(statement)
            folder = result.first()

            if folder:
                folder.recordcount = (folder.recordcount or 0) + 1
                return True
            return False
        except Exception:
            return False

    async def decrement_folder_record_count(self, folder_id: int) -> bool:
        """减少分类的文章数"""
        try:
            statement = select(Folder).where(Folder.id == folder_id)
            result = await self.session.exec(statement)
            folder = result.first()

            if folder and folder.recordcount and folder.recordcount > 0:
                folder.recordcount -= 1
                return True
            return False
        except Exception:
            return False

    # ==============================================
    # 分类评论统计
    # ==============================================

    async def increment_folder_post_count(self, folder_id: int) -> bool:
        """增加分类的评论数"""
        try:
            statement = select(Folder).where(Folder.id == folder_id)
            result = await self.session.exec(statement)
            folder = result.first()

            if folder:
                folder.postcount = (folder.postcount or 0) + 1
                return True
            return False
        except Exception:
            return False

    async def decrement_folder_post_count(self, folder_id: int) -> bool:
        """减少分类的评论数"""
        try:
            statement = select(Folder).where(Folder.id == folder_id)
            result = await self.session.exec(statement)
            folder = result.first()

            if folder and folder.postcount and folder.postcount > 0:
                folder.postcount -= 1
                return True
            return False
        except Exception:
            return False

    async def adjust_folder_post_count(self, folder_id: int, delta: int) -> bool:
        """按增量调整分类评论数（批量删除评论时使用）"""
        if delta == 0:
            return True
        try:
            statement = select(Folder).where(Folder.id == folder_id)
            result = await self.session.exec(statement)
            folder = result.first()

            if folder:
                folder.postcount = max((folder.postcount or 0) + delta, 0)
                return True
            return False
        except Exception:
            return False

    # ==============================================
    # 项目统计
    # ==============================================

    async def increment_project_record_count(self, project_id: int) -> bool:
        """增加项目的文章数"""
        try:
            statement = select(Project).where(Project.id == project_id)
            result = await self.session.exec(statement)
            project = result.first()

            if project:
                project.recordcount = (project.recordcount or 0) + 1
                project_repo = ProjectRepository(self.session)
                await project_repo.sync_updatetime_from_latest_published_article(project_id, project)
                return True
            return False
        except Exception:
            return False

    async def decrement_project_record_count(self, project_id: int) -> bool:
        """减少项目的文章数"""
        try:
            statement = select(Project).where(Project.id == project_id)
            result = await self.session.exec(statement)
            project = result.first()

            if project and project.recordcount and project.recordcount > 0:
                project.recordcount -= 1
                project_repo = ProjectRepository(self.session)
                await project_repo.sync_updatetime_from_latest_published_article(project_id, project)
                return True
            return False
        except Exception:
            return False

    async def increment_project_comment_count(self, project_id: int) -> bool:
        """增加项目的评论数"""
        try:
            statement = select(Project).where(Project.id == project_id)
            result = await self.session.exec(statement)
            project = result.first()

            if project:
                project.commentcount = (project.commentcount or 0) + 1
                return True
            return False
        except Exception:
            return False

    async def decrement_project_comment_count(self, project_id: int) -> bool:
        """减少项目的评论数"""
        try:
            statement = select(Project).where(Project.id == project_id)
            result = await self.session.exec(statement)
            project = result.first()

            if project and project.commentcount and project.commentcount > 0:
                project.commentcount -= 1
                return True
            return False
        except Exception:
            return False

    async def adjust_project_comment_count(self, project_id: int, delta: int) -> bool:
        """按增量调整项目评论数（批量删除评论时使用）"""
        if delta == 0:
            return True
        try:
            statement = select(Project).where(Project.id == project_id)
            result = await self.session.exec(statement)
            project = result.first()

            if project:
                project.commentcount = max((project.commentcount or 0) + delta, 0)
                return True
            return False
        except Exception:
            return False

    # ==============================================
    # 全局统计
    # ==============================================

    async def increment_user_count(self) -> bool:
        """增加用户总数"""
        return await self._update_glovar_count("usercount", 1)

    async def decrement_user_count(self) -> bool:
        """减少用户总数"""
        return await self._update_glovar_count("usercount", -1)

    async def increment_project_count(self) -> bool:
        """增加项目总数"""
        return await self._update_glovar_count("projectcount", 1)

    async def decrement_project_count(self) -> bool:
        """减少项目总数"""
        return await self._update_glovar_count("projectcount", -1)

    async def increment_project_item_count(self) -> bool:
        """增加文章总数"""
        return await self._update_glovar_count("projectitemcount", 1)

    async def decrement_project_item_count(self) -> bool:
        """减少文章总数"""
        return await self._update_glovar_count("projectitemcount", -1)

    async def _update_glovar_count(self, varname: str, delta: int) -> bool:
        """更新全局统计数量"""
        try:
            statement = select(Glovar).where(Glovar.varname == varname)
            result = await self.session.exec(statement)
            glovar = result.first()

            if glovar:
                glovar.varvalue = (glovar.varvalue or 0) + delta
                if glovar.varvalue < 0:
                    glovar.varvalue = 0
            else:
                glovar = Glovar(varname=varname, varvalue=max(0, delta))
                self.session.add(glovar)

            return True
        except Exception:
            return False

    # ==============================================
    # 复合操作
    # ==============================================

    async def handle_comment_creation(self, comment: Post) -> bool:
        """处理评论/留言创建时的统计更新"""
        try:
            if comment.rootid and comment.rootid > 0:
                await self.increment_post_reply_count(comment.rootid, comment.userid)

            if comment.projectitemid and comment.projectitemid > 0:
                await self.increment_article_comment_count(comment.projectitemid)

                article_statement = select(ProjectItem).where(
                    ProjectItem.id == comment.projectitemid
                )
                article_result = await self.session.exec(article_statement)
                article = article_result.first()

                if article and article.projectid:
                    await self.increment_project_comment_count(article.projectid)

                    if article.folderid and article.folderid > 0:
                        await self.increment_folder_post_count(article.folderid)

            return True
        except Exception:
            return False

    async def handle_comment_deletion(self, comment: Post) -> bool:
        """处理评论删除时的统计更新"""
        try:
            if comment.rootid and comment.rootid > 0:
                await self.decrement_post_reply_count(comment.rootid)

            if comment.projectitemid and comment.projectitemid > 0:
                await self.decrement_article_comment_count(comment.projectitemid)

                article_statement = select(ProjectItem).where(
                    ProjectItem.id == comment.projectitemid
                )
                article_result = await self.session.exec(article_statement)
                article = article_result.first()

                if article and article.projectid:
                    await self.decrement_project_comment_count(article.projectid)

                    if article.folderid and article.folderid > 0:
                        await self.decrement_folder_post_count(article.folderid)

            return True
        except Exception:
            return False

    async def handle_article_comments_bulk_removal(
        self, article: ProjectItem, removed_count: int
    ) -> bool:
        """彻底删除文章时，批量移除其下评论对应的博客/分类评论统计"""
        if removed_count <= 0:
            return True
        try:
            if article.projectid:
                await self.adjust_project_comment_count(article.projectid, -removed_count)
            if article.folderid and article.folderid > 0:
                await self.adjust_folder_post_count(article.folderid, -removed_count)
            return True
        except Exception:
            return False

    async def handle_article_creation(self, article: ProjectItem) -> bool:
        """处理文章创建时的统计更新"""
        try:
            if article.projectid:
                await self.increment_project_record_count(article.projectid)

            if article.folderid and article.folderid > 0:
                await self.increment_folder_record_count(article.folderid)

            await self.increment_project_item_count()

            return True
        except Exception:
            return False

    async def handle_article_deletion(self, article: ProjectItem) -> bool:
        """处理文章删除（软删或硬删）时的统计更新"""
        try:
            if article.projectid:
                await self.decrement_project_record_count(article.projectid)

            if article.folderid and article.folderid > 0:
                await self.decrement_folder_record_count(article.folderid)

            await self.decrement_project_item_count()

            return True
        except Exception:
            return False

    async def handle_article_folder_change(
        self, article: ProjectItem, old_folder_id: int, new_folder_id: int
    ) -> bool:
        """处理文章分类变更时的统计更新"""
        try:
            if old_folder_id and old_folder_id > 0:
                await self.decrement_folder_record_count(old_folder_id)

            if new_folder_id and new_folder_id > 0:
                await self.increment_folder_record_count(new_folder_id)

            return True
        except Exception:
            return False
