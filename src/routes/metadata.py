from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select, func
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import Dict, Any
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.database import User, ProjectItem, get_async_session

# 创建路由器
router = APIRouter()

@router.get("/metadata", response_model=Dict[str, Any])
async def get_site_metadata(session: AsyncSession = Depends(get_async_session)):
    """
    获取网站元数据
    访问地址: http://localhost:8000/api/metadata
    """
    try:
        # 查询用户总数
        user_count_statement = select(func.count(User.id))
        user_count_result = await session.exec(user_count_statement)
        user_count = user_count_result.first() or 0
        
        # 查询博客文章总数
        post_count_statement = select(func.count(ProjectItem.id))
        post_count_result = await session.exec(post_count_statement)
        post_count = post_count_result.first() or 0
        
        # 返回网站元数据
        metadata = {
            "site_name": "BlogN",
            "version": "V1",
            "logo_url": "/static/images/logo-light.svg",
            "user_count": user_count,
            "post_count": post_count
        }
        
        return metadata
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"获取网站元数据失败: {str(e)}"
        ) 