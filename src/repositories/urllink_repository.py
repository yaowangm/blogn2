from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from src.models.urllink import UrlLink
from typing import List, Optional

class UrlLinkRepository:
    """友情链接数据访问层"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_friend_links_by_project(
        self, 
        project_id: int
    ) -> List[UrlLink]:
        """
        获取指定项目的友情链接列表
        
        Args:
            project_id: 项目ID
            
        Returns:
            List[UrlLink]: 友情链接列表，按ordernum排序
        """
        query = (
            select(UrlLink)
            .where(UrlLink.projectid == project_id)
            .order_by(UrlLink.ordernum)
        )
        
        result = await self.session.exec(query)
        return result.all()
    
    async def get_all_friend_links(self) -> List[UrlLink]:
        """
        获取所有友情链接列表
            
        Returns:
            List[UrlLink]: 友情链接列表，按ordernum排序
        """
        query = (
            select(UrlLink)
            .order_by(UrlLink.ordernum)
        )
        
        result = await self.session.exec(query)
        return result.all()
    
    async def get_friend_link_by_id(
        self, 
        link_id: int
    ) -> Optional[UrlLink]:
        """
        根据ID获取友情链接
        
        Args:
            link_id: 友情链接ID
            
        Returns:
            Optional[UrlLink]: 友情链接对象，如果不存在则返回None
        """
        query = select(UrlLink).where(UrlLink.id == link_id)
        result = await self.session.exec(query)
        return result.first()
    
    async def create_friend_link(
        self,
        project_id: int,
        friend_link_data
    ) -> UrlLink:
        """
        创建友情链接
        
        Args:
            project_id: 项目ID
            friend_link_data: 友情链接数据 (可以是字典或Pydantic模型)
            
        Returns:
            UrlLink: 创建的友情链接
        """
        # 处理Pydantic模型或字典
        if hasattr(friend_link_data, 'dict'):
            # Pydantic模型
            data = friend_link_data.dict()
        else:
            # 字典
            data = friend_link_data
            
        friend_link = UrlLink(
            subject=data["subject"],
            linkstr=data["linkstr"],
            projectid=project_id,
            ordernum=data.get("ordernum", 0)
        )
        
        self.session.add(friend_link)
        await self.session.commit()
        await self.session.refresh(friend_link)
        return friend_link
    
    async def update_friend_link(
        self,
        link_id: int,
        friend_link_data
    ) -> UrlLink:
        """
        更新友情链接
        
        Args:
            link_id: 友情链接ID
            friend_link_data: 更新的友情链接数据 (可以是字典或Pydantic模型)
            
        Returns:
            UrlLink: 更新后的友情链接
        """
        # 处理Pydantic模型或字典
        if hasattr(friend_link_data, 'dict'):
            # Pydantic模型
            data = friend_link_data.dict()
        else:
            # 字典
            data = friend_link_data
            
        # 获取现有友情链接
        query = select(UrlLink).where(UrlLink.id == link_id)
        result = await self.session.exec(query)
        friend_link = result.first()
        
        if not friend_link:
            raise ValueError("友情链接不存在")
        
        # 更新字段
        if "subject" in data:
            friend_link.subject = data["subject"]
        if "linkstr" in data:
            friend_link.linkstr = data["linkstr"]
        if "ordernum" in data:
            friend_link.ordernum = data["ordernum"]
        
        await self.session.commit()
        await self.session.refresh(friend_link)
        return friend_link
    
    async def delete_friend_link(
        self,
        link_id: int
    ) -> bool:
        """
        删除友情链接
        
        Args:
            link_id: 友情链接ID
            
        Returns:
            bool: 删除是否成功
        """
        # 获取现有友情链接
        query = select(UrlLink).where(UrlLink.id == link_id)
        result = await self.session.exec(query)
        friend_link = result.first()
        
        if not friend_link:
            raise ValueError("友情链接不存在")
        
        await self.session.delete(friend_link)
        await self.session.commit()
        return True
