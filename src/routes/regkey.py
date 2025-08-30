"""
注册码管理API路由
提供注册码的查询、兑换等功能
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List, Dict, Any
import uuid
from datetime import datetime

from src.database import get_async_session
from src.models.regkey import RegKey, RegKeyWithUserInfo
from src.models.user import User
from src.utils.auth_middleware import get_current_user

router = APIRouter(prefix="/api/regkey", tags=["注册码管理"])


@router.get("/list", response_model=dict)
async def get_regkey_list(
    session: AsyncSession = Depends(get_async_session),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    获取注册码列表
    
    Args:
        session: 数据库会话
        current_user: 当前登录用户
        
    Returns:
        包含注册码列表的字典
    """
    try:
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
        raise HTTPException(status_code=500, detail=f"获取注册码列表失败: {str(e)}")


@router.post("/exchange", response_model=dict)
async def exchange_regkey(
    user_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    兑换注册码
    
    Args:
        user_id: 申请者用户ID
        session: 数据库会话
        current_user: 当前登录用户
        
    Returns:
        包含新注册码的字典
    """
    try:
        # 验证用户权限（只能为自己兑换）
        if current_user.id != user_id:
            raise HTTPException(status_code=403, detail="只能为自己兑换注册码")
        
        # 检查用户积分是否足够
        if current_user.point < 10:
            raise HTTPException(status_code=400, detail="积分不足，需要10积分")
        
        # 生成唯一注册码
        regkey = str(uuid.uuid4()).replace('-', '')[:16].upper()
        
        # 创建新的注册码记录
        new_regkey = RegKey(
            name=regkey,
            ownerid=user_id,
            status=1,  # 未使用
            createtime=datetime.now()
        )
        
        session.add(new_regkey)
        
        # 扣除用户积分
        current_user.point -= 10
        session.add(current_user)
        
        # 提交事务
        await session.commit()
        await session.refresh(new_regkey)
        
        return {
            "regkey": regkey,
            "message": "注册码兑换成功",
            "remaining_points": current_user.point
        }
        
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"兑换注册码失败: {str(e)}")


@router.get("/validate/{regkey}", response_model=dict)
async def validate_regkey(
    regkey: str,
    session: AsyncSession = Depends(get_async_session)
):
    """
    验证注册码是否有效
    
    Args:
        regkey: 注册码
        session: 数据库会话
        
    Returns:
        注册码验证结果
    """
    try:
        # 查询注册码
        stmt = select(RegKey).where(RegKey.name == regkey)
        result = await session.exec(stmt)
        regkey_record = result.first()
        
        if not regkey_record:
            return {"valid": False, "message": "注册码不存在"}
        
        if regkey_record.status == 2:
            return {"valid": False, "message": "注册码已被使用"}
        
        return {
            "valid": True,
            "message": "注册码有效",
            "regkey_id": regkey_record.id,
            "owner_id": regkey_record.ownerid
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"验证注册码失败: {str(e)}")


@router.post("/use/{regkey_id}", response_model=dict)
async def use_regkey(
    regkey_id: int,
    user_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    使用注册码
    
    Args:
        regkey_id: 注册码ID
        user_id: 使用者用户ID
        session: 数据库会话
        current_user: 当前登录用户
        
    Returns:
        使用结果
    """
    try:
        # 查询注册码
        stmt = select(RegKey).where(RegKey.id == regkey_id)
        result = await session.exec(stmt)
        regkey_record = result.first()
        
        if not regkey_record:
            raise HTTPException(status_code=404, detail="注册码不存在")
        
        if regkey_record.status == 2:
            raise HTTPException(status_code=404, detail="注册码已被使用")
        
        # 更新注册码状态
        regkey_record.status = 2  # 已使用
        regkey_record.userid = user_id
        
        session.add(regkey_record)
        await session.commit()
        
        return {"message": "注册码使用成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"使用注册码失败: {str(e)}")
