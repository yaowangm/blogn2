"""
注册码管理最小化路由
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime

from src.database import get_async_session
from src.models.regkey import RegKey
from src.models.user import User
from src.utils.auth_middleware import get_optional_current_user
from src.utils.permission_decorators import require_auth

router = APIRouter(prefix="/regkey", tags=["注册码管理"])



@router.get("/list")
@require_auth()
async def get_regkey_list(
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user)
):
    """获取注册码列表"""
    if not current_user:
        raise HTTPException(status_code=401, detail="需要登录才能访问")
    try:
        async for session in get_async_session():
            # 查询注册码数据，关联用户信息
            stmt = select(
                RegKey.id,
                RegKey.name,
                RegKey.ownerid,
                RegKey.userid,
                RegKey.status,
                RegKey.createtime,
                User.name.label("owner_name")
            ).select_from(
                RegKey.__table__.join(
                    User.__table__,
                    RegKey.ownerid == User.id,
                    isouter=True
                )
            ).where(
                RegKey.ownerid == current_user["id"]  # 只查询当前用户的注册码
            ).order_by(RegKey.id)
            
            result = await session.exec(stmt)
            rows = result.all()
            
            # 处理结果，添加使用者信息
            regkeys = []
            for row in rows:
                regkey_info = {
                    "id": row.id,
                    "regkey": row.name,  # 使用name字段
                    "ownerid": row.ownerid,
                    "owner_name": row.owner_name,
                    "userid": row.userid,
                    "user_name": None,
                    "status": row.status,
                    "createtime": row.createtime
                }
                
                # 如果有使用者，查询使用者姓名
                if row.userid:
                    user_stmt = select(User.name).where(User.id == row.userid)
                    user_result = await session.exec(user_stmt)
                    user_name = user_result.first()
                    if user_name:
                        regkey_info["user_name"] = user_name
                        
                regkeys.append(regkey_info)
            
            return {"regkeys": regkeys}
            
    except Exception as e:
        print(f"获取注册码列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取注册码列表失败: {str(e)}")

@router.post("/exchange")
@require_auth()
async def exchange_regkey(
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user)
):
    """兑换注册码"""
    try:
        async for session in get_async_session():
            # 生成唯一注册码
            import uuid
            regkey = str(uuid.uuid4()).replace('-', '')[:16].upper()
            
            # 创建新的注册码记录
            new_regkey = RegKey(
                name=regkey,
                ownerid=current_user["id"],
                status=1,  # 未使用
                createtime=datetime.now()
            )
            
            session.add(new_regkey)
            await session.commit()
            await session.refresh(new_regkey)
            
            return {
                "regkey": regkey,
                "message": "注册码兑换成功",
                "regkey_id": new_regkey.id
            }
            
    except Exception as e:
        print(f"兑换注册码失败: {e}")
        raise HTTPException(status_code=500, detail=f"兑换注册码失败: {str(e)}")

@router.get("/validate/{regkey}")
async def validate_regkey(regkey: str):
    """验证注册码"""
    return {"valid": True, "message": "验证功能待实现"}

@router.post("/use/{regkey_id}")
@require_auth()
async def use_regkey(
    regkey_id: int,
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user)
):
    """使用注册码"""
    return {"message": "使用功能待实现"}
