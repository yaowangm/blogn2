from sqlmodel import select, func
from sqlalchemy import or_
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List, Optional
from src.models.project_item import ProjectItem
from src.models.user import User
from src.models.folder import Folder
from src.constants import ArticleStatus

class ProjectItemRepository:
    """项目项数据访问层
    
    提供项目项数据的CRUD操作，包括查询、统计等功能。
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, project_item: ProjectItem) -> ProjectItem:
        """创建新的项目项"""
        self.session.add(project_item)
        await self.session.flush()  # 获取生成的ID
        await self.session.refresh(project_item)  # 刷新对象以获取完整数据
        
        # 更新统计信息
        try:
            from src.services.stats_service import StatsService
            stats_service = StatsService(self.session)
            await stats_service.handle_article_creation(project_item)
        except Exception as e:
            # 统计更新失败不影响文章创建，静默处理
            pass
        
        return project_item
    
    async def count(self) -> int:
        """获取项目项总数"""
        statement = select(func.count(ProjectItem.id))
        result = await self.session.exec(statement)
        return result.first() or 0
    
    async def get_by_id(self, id: int) -> Optional[ProjectItem]:
        """根据ID获取项目项"""
        statement = select(ProjectItem).where(ProjectItem.id == id)
        result = await self.session.exec(statement)
        return result.first()
    
    async def get_by_user_id(self, user_id: int, limit: int = None) -> List[ProjectItem]:
        """根据用户ID获取项目项"""
        statement = select(ProjectItem).where(ProjectItem.userid == user_id)
        if limit:
            statement = statement.limit(limit)
        result = await self.session.exec(statement)
        return result.all()
    
    async def get_by_project_id(self, project_id: int, limit: int = None) -> List[ProjectItem]:
        """根据项目ID获取项目项"""
        statement = select(ProjectItem).where(ProjectItem.projectid == project_id)
        if limit:
            statement = statement.limit(limit)
        result = await self.session.exec(statement)
        return result.all()
    
    async def count_by_project_id(self, project_id: int) -> int:
        """根据项目ID获取项目项总数"""
        statement = select(func.count(ProjectItem.id)).where(ProjectItem.projectid == project_id)
        result = await self.session.exec(statement)
        return result.first() or 0
    
    async def get_recent_items(self, limit: int = 10) -> List[ProjectItem]:
        """获取最近创建的项目项"""
        statement = select(ProjectItem).order_by(ProjectItem.createtime.desc()).limit(limit)
        result = await self.session.exec(statement)
        return result.all()
    
    async def get_popular_items(self, limit: int = 10) -> List[ProjectItem]:
        """获取最受欢迎的项目项（按访问次数）"""
        statement = select(ProjectItem).order_by(ProjectItem.accesscount.desc()).limit(limit)
        result = await self.session.exec(statement)
        return result.all()
    
    async def get_posts_count(self, exclude: Optional[int] = None, blogid: Optional[int] = None) -> int:
        """获取博文总数"""
        from src.models.project import Project
        
        query = (
            select(func.count(ProjectItem.id))
            .join(User, ProjectItem.userid == User.id)
            .join(Project, ProjectItem.projectid == Project.id)
            .where(ProjectItem.status == 1)  # 只获取正常状态的博文
        )
        
        # 如果指定了要获取的博客ID，添加过滤条件
        if blogid is not None:
            query = query.where(ProjectItem.projectid == blogid)
        # 如果指定了要排除的博客ID，添加过滤条件
        elif exclude is not None:
            query = query.where(ProjectItem.projectid != exclude)
        
        result = await self.session.exec(query)
        return result.first() or 0

    async def get_latest_posts(self, limit: int = 5, exclude: Optional[int] = None, blogid: Optional[int] = None, offset: int = 0) -> List[dict]:
        """获取最新的博文记录，包含博客名称（支持分页）"""
        from src.models.project import Project
        from src.utils.text_utils import POST_LIST_EXCERPT_MAX_LENGTH

        comment_excerpt = func.substr(ProjectItem.comment, 1, POST_LIST_EXCERPT_MAX_LENGTH).label("comment")

        query = (
            select(
                ProjectItem.id,
                ProjectItem.name,
                comment_excerpt,
                ProjectItem.attachment,
                ProjectItem.createtime,
                ProjectItem.userid,
                ProjectItem.projectid,
                User.name.label("author_name"),
                Project.name.label("blog_name"),
            )
            .join(User, ProjectItem.userid == User.id)
            .join(Project, ProjectItem.projectid == Project.id)
            .where(ProjectItem.status == 1)  # 只获取正常状态的博文
        )
        
        # 如果指定了要获取的博客ID，添加过滤条件
        if blogid is not None:
            query = query.where(ProjectItem.projectid == blogid)
        # 如果指定了要排除的博客ID，添加过滤条件
        elif exclude is not None:
            query = query.where(ProjectItem.projectid != exclude)
        
        query = query.order_by(ProjectItem.createtime.desc()).offset(offset).limit(limit)
        
        result = await self.session.exec(query)
        posts = []

        for row in result:
            posts.append({
                "id": row.id,
                "name": row.name,
                "comment": row.comment,
                "attachment": row.attachment,
                "author_name": row.author_name,
                "blog_name": row.blog_name,
                "blog_id": row.projectid,
                "createtime": row.createtime,
                "userid": row.userid
            })

        return posts

    async def get_by_project_id_and_folder(self, project_id: int, folder_id: Optional[int] = None, limit: int = None, offset: int = 0, include_deleted: bool = False) -> List[dict]:
        """根据项目ID和文件夹ID获取项目项，包含用户信息"""
        from src.models.user import User
        from src.utils.text_utils import POST_LIST_EXCERPT_MAX_LENGTH

        comment_excerpt = func.substr(ProjectItem.comment, 1, POST_LIST_EXCERPT_MAX_LENGTH).label("comment")

        query = (
            select(
                ProjectItem.id,
                ProjectItem.name,
                comment_excerpt,
                ProjectItem.createtime,
                ProjectItem.accesscount,
                ProjectItem.commentcount,
                ProjectItem.userid,
                ProjectItem.attachment,
                ProjectItem.folderid,
                User.name.label("author_name"),
                Folder.name.label("folder_name"),
            )
            .join(User, ProjectItem.userid == User.id)
            .outerjoin(Folder, ProjectItem.folderid == Folder.id)
            .where(ProjectItem.projectid == project_id)
            .where(ProjectItem.status == 1)  # 只获取正常状态的文章
        )
        
        # 根据include_deleted参数决定是否包含已删除的文章
        if not include_deleted:
            query = query.where(
                or_(
                    ProjectItem.itemtype.is_(None),
                    ProjectItem.itemtype != ArticleStatus.DELETED,
                )
            )
        
        if folder_id is not None:
            # 如果指定了文件夹，只获取该文件夹下的文章
            query = query.where(ProjectItem.folderid == folder_id)
        # 如果没有指定folder_id，则获取所有文章（包括未分配文件夹的文章）
        
        if limit:
            query = query.limit(limit)
        
        if offset > 0:
            query = query.offset(offset)
        
        query = query.order_by(ProjectItem.createtime.desc())
        
        result = await self.session.exec(query)

        posts = []
        for row in result:
            folder_name = row.folder_name
            posts.append({
                "id": row.id,
                "name": row.name,
                "comment": row.comment,
                "createtime": row.createtime,
                "accesscount": row.accesscount,
                "commentcount": row.commentcount,
                "userid": row.userid,
                "author_name": row.author_name,
                "attachment": row.attachment,
                "folderid": row.folderid,
                "category": (folder_name.strip() if folder_name else "未分类"),
            })

        return posts

    async def count_by_project_id_and_folder(self, project_id: int, folder_id: Optional[int] = None) -> int:
        """根据项目ID和文件夹ID统计项目项总数"""
        statement = select(func.count(ProjectItem.id)).where(ProjectItem.projectid == project_id)
        statement = statement.where(ProjectItem.status == 1)  # 只统计正常状态的文章
        statement = statement.where(
            or_(
                ProjectItem.itemtype.is_(None),
                ProjectItem.itemtype != ArticleStatus.DELETED,
            )
        )
        
        if folder_id is not None:
            statement = statement.where(ProjectItem.folderid == folder_id)
        
        result = await self.session.exec(statement)
        return result.first() or 0
    
    async def get_recent_articles(self, limit: int = 20) -> List[dict]:
        """获取最新发布的文章列表（用于RSS）"""
        from src.models.project import Project
        
        # 先尝试不限制任何条件，看看能获取到什么数据
        query = (
            select(ProjectItem, User.name.label("author_name"), Project.name.label("project_name"))
            .join(User, ProjectItem.userid == User.id)
            .join(Project, ProjectItem.projectid == Project.id)
            .order_by(ProjectItem.createtime.desc())
            .limit(limit)
        )
        
        result = await self.session.exec(query)
        
        # 转换为字典格式
        articles = []
        for project_item, author_name, project_name in result:
            articles.append({
                "id": project_item.id,
                "name": project_item.name,
                "comment": project_item.comment,
                "createtime": project_item.createtime,
                "userid": project_item.userid,
                "projectid": project_item.projectid,
                "author_name": author_name,
                "project_name": project_name
            })
        
        return articles
    
    async def get_articles_by_project(self, project_id: int, limit: int = 20) -> List[dict]:
        """获取指定博客下的最新文章列表（用于RSS）"""
        query = (
            select(ProjectItem, User.name.label("author_name"))
            .join(User, ProjectItem.userid == User.id)
            .where(ProjectItem.projectid == project_id)
            .order_by(ProjectItem.createtime.desc())
            .limit(limit)
        )
        
        result = await self.session.exec(query)
        
        # 转换为字典格式
        articles = []
        for project_item, author_name in result:
            articles.append({
                "id": project_item.id,
                "name": project_item.name,
                "comment": project_item.comment,
                "createtime": project_item.createtime,
                "userid": project_item.userid,
                "projectid": project_item.projectid,
                "author_name": author_name
            })
        
        return articles
    
    async def update(self, project_item_id: int, **kwargs) -> Optional[ProjectItem]:
        """
        更新项目项
        
        Args:
            project_item_id: 项目项ID
            **kwargs: 要更新的字段
            
        Returns:
            Optional[ProjectItem]: 更新后的项目项对象或None
        """
        project_item = await self.get_by_id(project_item_id)
        if project_item:
            for key, value in kwargs.items():
                if hasattr(project_item, key):
                    setattr(project_item, key, value)
            await self.session.commit()
            await self.session.refresh(project_item)
            return project_item
        return None

    async def delete(self, project_item_id: int, update_stats: bool = True) -> bool:
        """
        删除项目项

        Args:
            project_item_id: 项目项ID
            update_stats: 是否更新文章数等统计（软删后硬删时应为 False）

        Returns:
            bool: 删除是否成功
        """
        project_item = await self.get_by_id(project_item_id)
        if project_item:
            if update_stats:
                try:
                    from src.services.stats_service import StatsService
                    stats_service = StatsService(self.session)
                    await stats_service.handle_article_deletion(project_item)
                except Exception:
                    pass

            await self.session.delete(project_item)
            return True
        return False
    
    async def increment_comment_count(self, project_item_id: int) -> bool:
        """
        增加项目项的评论数量
        
        Args:
            project_item_id: 项目项ID
            
        Returns:
            bool: 更新是否成功
        """
        project_item = await self.get_by_id(project_item_id)
        if project_item:
            # 增加项目项的评论数
            project_item.commentcount = (project_item.commentcount or 0) + 1
            await self.session.commit()
            await self.session.refresh(project_item)
            
            # 同时更新对应项目的评论数
            from src.repositories.project_repository import ProjectRepository
            project_repo = ProjectRepository(self.session)
            await project_repo.increment_comment_count(project_item.projectid)
            
            return True
        return False
    
    async def decrement_comment_count(self, project_item_id: int) -> bool:
        """
        减少项目项的评论数量
        
        Args:
            project_item_id: 项目项ID
            
        Returns:
            bool: 更新是否成功
        """
        project_item = await self.get_by_id(project_item_id)
        if project_item and project_item.commentcount > 0:
            project_item.commentcount -= 1
            await self.session.commit()
            await self.session.refresh(project_item)
            
            # 同时更新对应项目的评论数
            from src.repositories.project_repository import ProjectRepository
            project_repo = ProjectRepository(self.session)
            await project_repo.decrement_comment_count(project_item.projectid)
            
            return True
        return False
    
    async def increment_access_count(self, project_item_id: int) -> bool:
        """
        增加文章访问次数
        
        Args:
            project_item_id: 文章ID
            
        Returns:
            bool: 更新是否成功
        """
        try:
            project_item = await self.get_by_id(project_item_id)
            if project_item:
                project_item.accesscount = (project_item.accesscount or 0) + 1
                self.session.add(project_item)
                await self.session.commit()
                return True
            else:
                return False
        except Exception as e:
            return False