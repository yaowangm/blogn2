from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from src.models.urllink import UrlLink
from typing import List

class UrlLinkRepository:
    """友情链接数据访问层"""
    
    @staticmethod
    async def get_friend_links_by_project(
        session: AsyncSession, 
        project_id: int
    ) -> List[UrlLink]:
        """
        获取指定项目的友情链接列表
        
        Args:
            session: 数据库会话
            project_id: 项目ID
            
        Returns:
            List[UrlLink]: 友情链接列表，按ordernum排序，限制前10条
        """
        query = (
            select(UrlLink)
            .where(UrlLink.projectid == project_id)
            .order_by(UrlLink.ordernum)
            .limit(10)
        )
        
        result = await session.exec(query)
        return result.all()
    
    @staticmethod
    async def get_all_friend_links(session: AsyncSession) -> List[UrlLink]:
        """
        获取所有友情链接列表
        
        Args:
            session: 数据库会话
            
        Returns:
            List[UrlLink]: 友情链接列表，按ordernum排序，限制前10条
        """
        query = (
            select(UrlLink)
            .order_by(UrlLink.ordernum)
            .limit(10)
        )
        
        result = await session.exec(query)
        return result.all()
