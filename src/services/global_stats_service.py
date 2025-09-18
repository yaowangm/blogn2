"""
全局统计服务

管理glovar表中的全局统计数据，包括用户数量、项目数量、项目项数量等。
"""

from sqlmodel import select, update
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import Optional
from src.models.glovar import Glovar


class GlobalStatsService:
    """全局统计服务
    
    负责管理glovar表中的全局统计数据，提供增量和减量更新功能。
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_stat_value(self, varname: str) -> int:
        """获取指定统计变量的值
        
        Args:
            varname: 变量名（如 'usercount', 'projectcount', 'projectitemcount'）
            
        Returns:
            int: 统计值，如果不存在则返回0
        """
        statement = select(Glovar).where(Glovar.varname == varname)
        result = await self.session.exec(statement)
        glovar = result.first()
        
        if glovar:
            return glovar.varvalue or 0
        return 0
    
    async def set_stat_value(self, varname: str, value: int) -> bool:
        """设置指定统计变量的值
        
        Args:
            varname: 变量名
            value: 新值
            
        Returns:
            bool: 更新是否成功
        """
        try:
            # 先尝试更新现有记录
            statement = update(Glovar).where(Glovar.varname == varname).values(varvalue=value)
            result = await self.session.exec(statement)
            
            # 如果没有记录被更新，则创建新记录
            if result.rowcount == 0:
                new_glovar = Glovar(varname=varname, varvalue=value)
                self.session.add(new_glovar)
            
            await self.session.commit()
            return True
        except Exception as e:
            await self.session.rollback()
            print(f"Error setting stat value {varname}={value}: {e}")
            return False
    
    async def increment_stat(self, varname: str, amount: int = 1) -> bool:
        """增加指定统计变量的值
        
        Args:
            varname: 变量名
            amount: 增加的数量，默认为1
            
        Returns:
            bool: 更新是否成功
        """
        try:
            current_value = await self.get_stat_value(varname)
            new_value = current_value + amount
            return await self.set_stat_value(varname, new_value)
        except Exception as e:
            print(f"Error incrementing stat {varname}: {e}")
            return False
    
    async def decrement_stat(self, varname: str, amount: int = 1) -> bool:
        """减少指定统计变量的值
        
        Args:
            varname: 变量名
            amount: 减少的数量，默认为1
            
        Returns:
            bool: 更新是否成功
        """
        try:
            current_value = await self.get_stat_value(varname)
            new_value = max(current_value - amount, 0)  # 确保不会变成负数
            return await self.set_stat_value(varname, new_value)
        except Exception as e:
            print(f"Error decrementing stat {varname}: {e}")
            return False
    
    async def update_user_count(self, increment: bool = True) -> bool:
        """更新用户数量统计
        
        Args:
            increment: True为增加，False为减少
            
        Returns:
            bool: 更新是否成功
        """
        if increment:
            return await self.increment_stat('usercount')
        else:
            return await self.decrement_stat('usercount')
    
    async def update_project_count(self, increment: bool = True) -> bool:
        """更新项目数量统计
        
        Args:
            increment: True为增加，False为减少
            
        Returns:
            bool: 更新是否成功
        """
        if increment:
            return await self.increment_stat('projectcount')
        else:
            return await self.decrement_stat('projectcount')
    
    async def update_project_item_count(self, increment: bool = True) -> bool:
        """更新项目项数量统计
        
        Args:
            increment: True为增加，False为减少
            
        Returns:
            bool: 更新是否成功
        """
        if increment:
            return await self.increment_stat('projectitemcount')
        else:
            return await self.decrement_stat('projectitemcount')
    
    async def get_all_stats(self) -> dict:
        """获取所有统计信息
        
        Returns:
            dict: 包含所有统计信息的字典
        """
        stats = {}
        for varname in ['usercount', 'projectcount', 'projectitemcount']:
            stats[varname] = await self.get_stat_value(varname)
        return stats
    
    async def sync_stats_from_database(self) -> bool:
        """从实际数据库数据同步统计信息
        
        这个方法会重新计算所有统计值，用于数据修复或初始化。
        
        Returns:
            bool: 同步是否成功
        """
        try:
            from src.models.user import User
            from src.models.project import Project
            from src.models.project_item import ProjectItem
            from sqlmodel import func
            
            # 统计用户数量
            user_count_statement = select(func.count(User.id))
            user_count_result = await self.session.exec(user_count_statement)
            user_count = user_count_result.first() or 0
            
            # 统计项目数量
            project_count_statement = select(func.count(Project.id))
            project_count_result = await self.session.exec(project_count_statement)
            project_count = project_count_result.first() or 0
            
            # 统计项目项数量
            project_item_count_statement = select(func.count(ProjectItem.id))
            project_item_count_result = await self.session.exec(project_item_count_statement)
            project_item_count = project_item_count_result.first() or 0
            
            # 更新统计值
            await self.set_stat_value('usercount', user_count)
            await self.set_stat_value('projectcount', project_count)
            await self.set_stat_value('projectitemcount', project_item_count)
            
            return True
        except Exception as e:
            print(f"Error syncing stats from database: {e}")
            return False
