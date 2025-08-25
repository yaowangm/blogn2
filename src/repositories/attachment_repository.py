"""
附件仓库
提供附件数据的数据库操作方法
基于实际数据库表结构
"""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from src.models.attachment import Attachment

class AttachmentRepository:
    """附件仓库类"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_project_item_id(self, project_item_id: int) -> List[Attachment]:
        """
        根据文章ID获取所有附件，按创建时间排序
        
        Args:
            project_item_id: 文章ID
            
        Returns:
            List[Attachment]: 附件列表，按创建时间升序排列
        """
        stmt = select(Attachment).where(
            Attachment.parentid == project_item_id
        ).order_by(Attachment.createtime)
        
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_by_id(self, attachment_id: int) -> Optional[Attachment]:
        """
        根据附件ID获取附件
        
        Args:
            attachment_id: 附件ID
            
        Returns:
            Optional[Attachment]: 附件对象或None
        """
        stmt = select(Attachment).where(Attachment.id == attachment_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def create(self, attachment: Attachment) -> Attachment:
        """
        创建新附件
        
        Args:
            attachment: 附件对象
            
        Returns:
            Attachment: 创建后的附件对象
        """
        self.session.add(attachment)
        await self.session.commit()
        await self.session.refresh(attachment)
        return attachment
    
    async def delete(self, attachment_id: int) -> bool:
        """
        删除附件
        
        Args:
            attachment_id: 附件ID
            
        Returns:
            bool: 删除是否成功
        """
        attachment = await self.get_by_id(attachment_id)
        if attachment:
            await self.session.delete(attachment)
            await self.session.commit()
            return True
        return False
    
    async def update(self, attachment_id: int, **kwargs) -> Optional[Attachment]:
        """
        更新附件信息
        
        Args:
            attachment_id: 附件ID
            **kwargs: 要更新的字段
            
        Returns:
            Optional[Attachment]: 更新后的附件对象或None
        """
        attachment = await self.get_by_id(attachment_id)
        if attachment:
            for key, value in kwargs.items():
                if hasattr(attachment, key):
                    setattr(attachment, key, value)
            await self.session.commit()
            await self.session.refresh(attachment)
            return attachment
        return None
