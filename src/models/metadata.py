from pydantic import BaseModel
from typing import Dict, Any

class SiteMetadata(BaseModel):
    """网站元数据验证模型"""
    site_name: str
    version: str
    logo_url: str
    user_count: int
    post_count: int

class MetadataResponse(BaseModel):
    """元数据响应模型"""
    data: SiteMetadata
    success: bool = True
    message: str = "获取成功" 