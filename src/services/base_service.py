"""
基础服务类
提供所有服务类共用的基础功能
"""
import logging
from typing import TypeVar, Generic
from sqlmodel.ext.asyncio.session import AsyncSession

# 配置日志
logger = logging.getLogger(__name__)

T = TypeVar('T')

class BaseService(Generic[T]):
    """
    基础服务类
    
    提供所有服务类共用的基础功能，包括依赖注入和通用方法。
    """
    
    def __init__(self, *repositories):
        """
        初始化服务
        
        Args:
            *repositories: 依赖的仓储实例
        """
        self.repositories = repositories
    
    @classmethod
    def create_with_session(cls, session: AsyncSession, *repository_classes):
        """
        使用数据库会话创建服务实例
        
        Args:
            session: 数据库会话
            *repository_classes: 仓储类列表
            
        Returns:
            BaseService: 服务实例
        """
        repositories = [repo_cls(session) for repo_cls in repository_classes]
        return cls(*repositories)
    
    async def handle_async_operation(self, operation, *args, **kwargs):
        """
        处理异步操作的通用方法
        
        Args:
            operation: 要执行的异步操作
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            操作结果
        """
        try:
            return await operation(*args, **kwargs)
        except Exception as e:
            # 记录错误日志
            logger.error(f"Service operation failed: {e}", exc_info=True)
            raise 