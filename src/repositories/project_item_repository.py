from sqlmodel import select, func
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List, Optional
from src.models.project_item import ProjectItem
from src.models.user import User
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
        
        query = (
            select(ProjectItem, User.name.label("author_name"), Project.name.label("blog_name"))
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
        
        for project_item, author_name, blog_name in result:
            posts.append({
                "id": project_item.id,
                "name": project_item.name,
                "comment": project_item.comment,
                "attachment": project_item.attachment,
                "author_name": author_name,
                "blog_name": blog_name,
                "blog_id": project_item.projectid,
                "createtime": project_item.createtime,
                "userid": project_item.userid
            })
        
        return posts

    async def get_by_project_id_and_folder(self, project_id: int, folder_id: Optional[int] = None, limit: int = None, offset: int = 0, include_deleted: bool = False) -> List[dict]:
        """根据项目ID和文件夹ID获取项目项，包含用户信息"""
        from src.models.user import User
        
        query = (
            select(ProjectItem, User.name.label("author_name"))
            .join(User, ProjectItem.userid == User.id)
            .where(ProjectItem.projectid == project_id)
            .where(ProjectItem.status == 1)  # 只获取正常状态的文章
        )
        
        # 根据include_deleted参数决定是否包含已删除的文章
        if not include_deleted:
            query = query.where(ProjectItem.itemtype != ArticleStatus.DELETED)  # 排除已删除的文章
        
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
        
        # 转换为字典格式
        posts = []
        for project_item, author_name in result:
            posts.append({
                "id": project_item.id,
                "name": project_item.name,
                "comment": project_item.comment,
                "createtime": project_item.createtime,
                "accesscount": project_item.accesscount,
                "commentcount": project_item.commentcount,
                "userid": project_item.userid,
                "author_name": author_name,
                "attachment": project_item.attachment
            })
        
        return posts

    async def count_by_project_id_and_folder(self, project_id: int, folder_id: Optional[int] = None) -> int:
        """根据项目ID和文件夹ID统计项目项总数"""
        statement = select(func.count(ProjectItem.id)).where(ProjectItem.projectid == project_id)
        statement = statement.where(ProjectItem.status == 1)  # 只统计正常状态的文章
        statement = statement.where(ProjectItem.itemtype != ArticleStatus.DELETED)  # 排除已删除的文章
        
        if folder_id is not None:
            statement = statement.where(ProjectItem.folderid == folder_id)
        
        result = await self.session.exec(statement)
        return result.first() or 0
    
    async def get_count_from_folder_recordcount(self, project_id: int, folder_id: Optional[int] = None) -> int:
        """
        从folders表的recordcount字段获取文章数量，避免实时查询
        
        Args:
            project_id: 项目ID
            folder_id: 文件夹ID（可选）
            
        Returns:
            int: 文章数量
        """
        from src.models.folder import Folder
        
        if folder_id is not None:
            # 如果指定了文件夹，直接从该文件夹的recordcount获取
            folder_query = select(Folder.recordcount).where(
                Folder.id == folder_id,
                Folder.projectid == project_id
            )
            result = await self.session.exec(folder_query)
            folder_recordcount = result.first()
            return folder_recordcount if folder_recordcount is not None else 0
        else:
            # 如果没有指定文件夹，统计项目下所有文件夹的文章总数
            # 注意：这里需要包含未分配到任何文件夹的文章
            folders_query = select(Folder.recordcount).where(Folder.projectid == project_id)
            result = await self.session.exec(folders_query)
            folder_recordcounts = result.all()
            folder_count = sum(recordcount or 0 for recordcount in folder_recordcounts)
            
            # 还需要统计没有分配到任何文件夹的文章数量
            unassigned_query = select(func.count(ProjectItem.id)).where(
                ProjectItem.projectid == project_id,
                ProjectItem.folderid.is_(None),  # 未分配文件夹的文章
                ProjectItem.status == 1  # 只统计正常状态的文章
            )
            unassigned_result = await self.session.exec(unassigned_query)
            unassigned_count = unassigned_result.first() or 0
            
            return folder_count + unassigned_count
    
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

    async def delete(self, project_item_id: int) -> bool:
        """
        删除项目项
        
        Args:
            project_item_id: 项目项ID
            
        Returns:
            bool: 删除是否成功
        """
        project_item = await self.get_by_id(project_item_id)
        if project_item:
            # 更新统计信息
            try:
                from src.services.stats_service import StatsService
                stats_service = StatsService(self.session)
                await stats_service.handle_article_deletion(project_item)
            except Exception as e:
                # 统计更新失败不影响文章删除，静默处理
                pass
            
            await self.session.delete(project_item)
            await self.session.commit()
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
    
    async def count_by_project_id_and_folder(self, project_id: int, folder_id: Optional[int] = None) -> int:
        """根据项目ID和文件夹ID统计文章数量
        
        Args:
            project_id: 项目ID
            folder_id: 文件夹ID，None表示所有文章，0表示未分类
            
        Returns:
            int: 文章数量
        """
        query = select(func.count(ProjectItem.id)).where(ProjectItem.projectid == project_id)
        
        if folder_id is not None:
            query = query.where(ProjectItem.folderid == folder_id)
        
        result = await self.session.exec(query)
        return result.first() or 0