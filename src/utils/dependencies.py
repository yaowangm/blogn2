"""
依赖注入工具
提供通用的依赖注入函数，减少控制器中的重复代码
"""
from typing import Type, Callable
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import Depends

from src.database import get_async_session
from src.repositories.user_repository import UserRepository
from src.repositories.project_item_repository import ProjectItemRepository
from src.repositories.project_repository import ProjectRepository
from src.repositories.post_repository import PostRepository
from src.services.metadata_service import MetadataService
from src.services.user_service import UserService
from src.services.blog_service import BlogService

def create_service_dependency(service_class: Type, *repository_classes: Type):
    """
    创建服务依赖注入函数
    
    Args:
        service_class: 服务类
        *repository_classes: 仓储类列表
        
    Returns:
        Callable: 依赖注入函数
    """
    async def get_service(session: AsyncSession = Depends(get_async_session)):
        """
        依赖注入：创建服务实例
        
        Args:
            session: 数据库会话
            
        Returns:
            服务实例
        """
        repositories = [repo_cls(session) for repo_cls in repository_classes]
        return service_class(*repositories)
    
    return get_service

# 预定义的服务依赖
get_metadata_service = create_service_dependency(
    MetadataService, 
    UserRepository, 
    ProjectItemRepository
)

get_user_service = create_service_dependency(
    UserService, 
    UserRepository
)

get_blog_service = create_service_dependency(
    BlogService, 
    UserRepository, 
    ProjectItemRepository, 
    ProjectRepository, 
    PostRepository
) 