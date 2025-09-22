"""
数据库操作工具类

提供统一的数据库操作功能，减少重复代码并提高代码质量。

主要功能：
- 安全的数据库操作（自动回滚处理）
- 统一的错误处理和日志记录
- 通用的CRUD操作封装
- 事务管理简化

使用场景：
- Repository层的数据库操作
- 需要事务保证的数据操作
- 批量数据处理
- 错误恢复和回滚

设计原则：
- 单一职责：专注于数据库操作
- 错误安全：自动处理回滚和错误
- 代码复用：减少重复的事务处理代码
- 日志记录：统一的错误日志格式
"""

from sqlmodel.ext.asyncio.session import AsyncSession
from typing import Any, Optional, Type, TypeVar
from sqlmodel import SQLModel
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=SQLModel)

class DatabaseUtils:
    """数据库操作工具类"""
    
    @staticmethod
    async def safe_operation(
        session: AsyncSession,
        operation: callable,
        *args,
        **kwargs
    ) -> tuple[bool, Any]:
        """
        安全执行数据库操作，自动处理回滚
        
        Args:
            session: 数据库会话
            operation: 要执行的操作函数
            *args: 操作函数的参数
            **kwargs: 操作函数的关键字参数
            
        Returns:
            tuple[bool, Any]: (是否成功, 操作结果)
        """
        try:
            result = await operation(*args, **kwargs)
            await session.commit()
            return True, result
        except Exception as e:
            await session.rollback()
            logger.error(f"Database operation failed: {e}")
            return False, None
    
    @staticmethod
    async def safe_create(
        session: AsyncSession,
        model_class: Type[T],
        **data
    ) -> tuple[bool, Optional[T]]:
        """
        安全创建数据库记录
        
        Args:
            session: 数据库会话
            model_class: 模型类
            **data: 模型数据
            
        Returns:
            tuple[bool, Optional[T]]: (是否成功, 创建的记录)
        """
        try:
            instance = model_class(**data)
            session.add(instance)
            await session.commit()
            await session.refresh(instance)
            return True, instance
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to create {model_class.__name__}: {e}")
            return False, None
    
    @staticmethod
    async def safe_update(
        session: AsyncSession,
        instance: T,
        **updates
    ) -> bool:
        """
        安全更新数据库记录
        
        Args:
            session: 数据库会话
            instance: 要更新的实例
            **updates: 更新的字段
            
        Returns:
            bool: 是否成功
        """
        try:
            for key, value in updates.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            
            session.add(instance)
            await session.commit()
            await session.refresh(instance)
            return True
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to update {instance.__class__.__name__}: {e}")
            return False
    
    @staticmethod
    async def safe_delete(
        session: AsyncSession,
        instance: T
    ) -> bool:
        """
        安全删除数据库记录
        
        Args:
            session: 数据库会话
            instance: 要删除的实例
            
        Returns:
            bool: 是否成功
        """
        try:
            session.delete(instance)
            await session.commit()
            return True
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to delete {instance.__class__.__name__}: {e}")
            return False
