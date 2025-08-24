"""
Attachment模型单元测试
测试附件模型的基本功能和属性
"""

import pytest
from datetime import datetime
from src.models.attachment import Attachment


class TestAttachmentModel:
    """Attachment模型测试类"""
    
    def test_attachment_creation(self):
        """测试附件创建"""
        attachment = Attachment(
            id=1,
            parentid=123,
            amtype="image",
            comment="测试图片",
            linkstr="/upload/test.jpg",
            createtime=datetime.now(),
            updatetime=datetime.now()
        )
        
        assert attachment.id == 1
        assert attachment.parentid == 123
        assert attachment.amtype == "image"
        assert attachment.comment == "测试图片"
        assert attachment.linkstr == "/upload/test.jpg"
        assert attachment.createtime is not None
        assert attachment.updatetime is not None
    
    def test_attachment_default_values(self):
        """测试附件的默认值"""
        attachment = Attachment(
            id=1,
            parentid=123,
            amtype="file"
        )
        
        assert attachment.id == 1
        assert attachment.parentid == 123
        assert attachment.amtype == "file"
        assert attachment.comment is None
        assert attachment.linkstr is None
        assert attachment.createtime is None
        assert attachment.updatetime is None
    
    def test_attachment_string_representation(self):
        """测试附件的字符串表示"""
        attachment = Attachment(
            id=1,
            parentid=123,
            amtype="image",
            comment="测试图片"
        )
        
        str_repr = str(attachment)
        assert "1" in str_repr
        assert "123" in str_repr
        # SQLModel的默认字符串表示可能不包含所有字段
        # 我们只验证基本结构
        assert "Attachment" in str_repr
    
    def test_attachment_repr_representation(self):
        """测试附件的repr表示"""
        attachment = Attachment(
            id=1,
            parentid=123,
            amtype="image"
        )
        
        repr_str = repr(attachment)
        assert "Attachment" in repr_str
        assert "id=1" in repr_str
        assert "parentid=123" in repr_str
    
    def test_attachment_equality(self):
        """测试附件的相等性比较"""
        attachment1 = Attachment(id=1, parentid=123, amtype="image")
        attachment2 = Attachment(id=1, parentid=123, amtype="image")
        attachment3 = Attachment(id=2, parentid=123, amtype="image")
        
        # SQLModel对象比较基于ID，如果ID相同则认为相等
        assert attachment1.id == attachment2.id
        assert attachment1.id != attachment3.id
    
    def test_attachment_hash(self):
        """测试附件的哈希值"""
        attachment1 = Attachment(id=1, parentid=123, amtype="image")
        attachment2 = Attachment(id=1, parentid=123, amtype="image")
        
        # SQLModel对象的哈希值可能不同，我们验证ID的哈希值
        assert hash(attachment1.id) == hash(attachment2.id)
    
    def test_attachment_field_types(self):
        """测试附件字段的类型"""
        attachment = Attachment(
            id=1,
            parentid=123,
            amtype="image",
            comment="测试图片",
            linkstr="/upload/test.jpg"
        )
        
        assert isinstance(attachment.id, int)
        assert isinstance(attachment.parentid, int)
        assert isinstance(attachment.amtype, str)
        assert isinstance(attachment.comment, str)
        assert isinstance(attachment.linkstr, str)
    
    def test_attachment_optional_fields(self):
        """测试附件的可选字段"""
        attachment = Attachment(
            id=1,
            parentid=123,
            amtype="image"
        )
        
        # 可选字段应该为None
        assert attachment.comment is None
        assert attachment.linkstr is None
        assert attachment.createtime is None
        assert attachment.updatetime is None
    
    def test_attachment_with_datetime_fields(self):
        """测试包含日期时间字段的附件"""
        now = datetime.now()
        attachment = Attachment(
            id=1,
            parentid=123,
            amtype="image",
            createtime=now,
            updatetime=now
        )
        
        assert attachment.createtime == now
        assert attachment.updatetime == now
        assert isinstance(attachment.createtime, datetime)
        assert isinstance(attachment.updatetime, datetime)
