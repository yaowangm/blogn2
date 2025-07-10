from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.database import User, get_async_session

# 创建路由器
router = APIRouter()

@router.get("/user", response_model=List[User])
async def get_top_users(session: AsyncSession = Depends(get_async_session)):
    """
    获取按创建时间排序的前三个用户
    访问地址: http://blogn2.local/api/user
    """
    try:
        # 查询按创建时间排序的前三个用户
        statement = select(User).order_by(User.regtime.desc()).limit(3)
        result = await session.exec(statement)
        users = result.all()
        
        if not users:
            return []
        
        return users
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"数据库查询失败: {str(e)}"
        )

@router.get("/user/count")
async def get_user_count(session: AsyncSession = Depends(get_async_session)):
    """
    获取用户总数
    访问地址: http://blogn2.local/api/user/count
    """
    try:
        statement = select(User)
        result = await session.exec(statement)
        users = result.all()
        return {"total_users": len(users)}
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"数据库查询失败: {str(e)}"
        )

@router.get("/user/{user_id}", response_model=User)
async def get_user_by_id(user_id: int, session: AsyncSession = Depends(get_async_session)):
    """
    根据ID获取用户信息
    访问地址: http://blogn2.local/api/user/{user_id}
    """
    try:
        statement = select(User).where(User.ID == user_id)
        result = await session.exec(statement)
        user = result.first()
        
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"数据库查询失败: {str(e)}"
        ) 