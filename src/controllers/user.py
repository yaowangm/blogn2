from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List, Dict, Any

from src.config.database import get_async_session
from src.repositories.user_repository import UserRepository
from src.services.user_service import UserService
from src.database import User

router = APIRouter()

def get_user_service(session: AsyncSession = Depends(get_async_session)) -> UserService:
    user_repo = UserRepository(session)
    return UserService(user_repo)

@router.get("/users/summary", response_model=Dict[str, Any])
async def get_user_summary(
    user_service: UserService = Depends(get_user_service)
):
    try:
        return await user_service.get_user_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户摘要失败: {str(e)}")

@router.get("/users/listnew", response_model=List[User])
async def get_new_users(
    user_service: UserService = Depends(get_user_service)
):
    try:
        return await user_service.get_top_users(3)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取最新用户失败: {str(e)}")

@router.get("/users/count")
async def get_user_count(
    user_service: UserService = Depends(get_user_service)
):
    try:
        count = await user_service.get_user_count()
        return {"count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户总数失败: {str(e)}")

@router.get("/users/{user_id}", response_model=User)
async def get_user_by_id(
    user_id: int,
    user_service: UserService = Depends(get_user_service)
):
    try:
        user = await user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户信息失败: {str(e)}") 