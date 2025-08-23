"""
附件模型
用于存储文章的多张图片附件
基于实际数据库表结构
"""

from sqlalchemy import Column, Integer, String, DateTime, BigInteger
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Attachment(Base):
    """附件表模型"""
    __tablename__ = 'attachment'
    
    id = Column(BigInteger, primary_key=True)
    parentid = Column(BigInteger, nullable=False, comment='关联的文章ID')
    amtype = Column(Integer, comment='附件类型')
    comment = Column(String(200), comment='图片注释/描述')
    linkstr = Column(String(200), nullable=False, comment='图片链接路径')
    createtime = Column(DateTime, comment='创建时间')
    updatetime = Column(DateTime, comment='更新时间')
    
    def __repr__(self):
        return f"<Attachment(id={self.id}, parentid={self.parentid}, comment='{self.comment}')>"
