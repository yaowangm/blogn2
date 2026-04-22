from src.utils.time_utils import TimeUtils
"""
用户注册API路由
提供新用户注册功能
"""

from fastapi import APIRouter, HTTPException, Depends, Body, Request
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import Dict, Any
from pydantic import BaseModel, EmailStr, validator
import re
from datetime import datetime
import hashlib

from src.database import get_async_session
from src.models.regkey import RegKey
from src.models.user import User
from src.utils.password_validation import validate_password as validate_password_rules
from src.services.auth_security_service import AuthSecurityService

# 创建用户注册API路由器
router = APIRouter(prefix="/register", tags=["用户注册"])

# 请求模型
class UserRegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    regkey: str
    
    @validator('username')
    def validate_username(cls, v):
        if not v or len(v.strip()) < 3:
            raise ValueError('用户名至少需要3个字符')
        if len(v.strip()) > 50:
            raise ValueError('用户名不能超过50个字符')
        if not re.match(r'^[a-zA-Z0-9_\u4e00-\u9fa5]+$', v.strip()):
            raise ValueError('用户名只能包含字母、数字、下划线和中文')
        return v.strip()
    
    @validator('email')
    def validate_email(cls, v):
        if not v or not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v.strip()):
            raise ValueError('邮箱格式不正确')
        return v.strip().lower()
    
    @validator('password')
    def validate_password(cls, v):
        validate_password_rules(v or "")
        return v
    
    @validator('regkey')
    def validate_regkey(cls, v):
        if not v:
            raise ValueError('注册码不能为空')
        
        # 移除连字符后检查长度
        v_clean = v.strip().upper()
        v_without_dashes = v_clean.replace('-', '')
        
        if len(v_without_dashes) != 25:
            raise ValueError('注册码格式不正确')
        
        return v_clean

class UserRegisterResponse(BaseModel):
    message: str
    user_id: int
    username: str

@router.post("/register", response_model=UserRegisterResponse)
async def register_user(
    request: UserRegisterRequest,
    session: AsyncSession = Depends(get_async_session),
    http_request: Request = None,
):
    """
    用户注册
    
    Args:
        request: 用户注册请求数据
        session: 数据库会话
        
    Returns:
        UserRegisterResponse: 注册成功响应
        
    Raises:
        HTTPException: 当验证失败或注册码无效时
    """
    try:
        auth_security_service = AuthSecurityService()
        if http_request:
            xff = http_request.headers.get("x-forwarded-for", "")
            raw_ip = xff.split(",")[0].strip() if xff else (
                http_request.client.host if http_request.client else "unknown"
            )
        else:
            raw_ip = "unknown"
        client_ip = auth_security_service.normalize_ip(raw_ip)
        await auth_security_service.check_register_rate_limit(client_ip)

        generic_register_error = "注册失败，请检查信息或稍后重试"

        # 1. 检查用户名是否已存在
        username_stmt = select(User).where(User.name == request.username)
        username_result = await session.exec(username_stmt)
        if username_result.first():
            raise HTTPException(status_code=400, detail=generic_register_error)
        
        # 2. 检查邮箱是否已存在
        email_stmt = select(User).where(User.email == request.email)
        email_result = await session.exec(email_stmt)
        if email_result.first():
            raise HTTPException(status_code=400, detail=generic_register_error)
        
        # 3. 验证注册码
        # 处理注册码格式，移除连字符并转换为大写
        regkey_clean = request.regkey.strip().upper()
        regkey_without_dashes = regkey_clean.replace('-', '')
        
        # 检查注册码格式
        if len(regkey_without_dashes) != 25:
            raise HTTPException(status_code=400, detail=generic_register_error)
        
        # 查询注册码（尝试两种格式：带连字符和不带连字符）
        regkey_stmt = select(RegKey).where(
            (RegKey.name == regkey_clean) | (RegKey.name == regkey_without_dashes),
            RegKey.status == 1  # 未使用
        )
        regkey_result = await session.exec(regkey_stmt)
        regkey_record = regkey_result.first()
        
        if not regkey_record:
            raise HTTPException(status_code=400, detail=generic_register_error)
        
        # 4. 创建新用户
        # 对密码进行双重哈希加密：password → MD5 → bcrypt
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        md5_hash = hashlib.md5(request.password.encode()).hexdigest()
        password_hash = pwd_context.hash(md5_hash)
        
        new_user = User(
            name=request.username,
            email=request.email,
            password=password_hash,
            state=1,  # 正常状态
            regtime=TimeUtils.now_utc(),
            point=0,  # 初始积分
            lastupdate=TimeUtils.now_utc()
        )
        
        # 5. 在事务中完成用户创建和注册码更新
        session.add(new_user)
        
        # 刷新session以获取生成的用户ID
        await session.flush()
        
        # 更新注册码状态
        regkey_record.status = 2  # 已使用
        regkey_record.userid = new_user.id
        
        session.add(regkey_record)
        
        # 更新全局用户数量统计
        from src.services.global_stats_service import GlobalStatsService
        stats_service = GlobalStatsService(session)
        await stats_service.update_user_count(increment=True)
        
        # 提交事务
        await session.commit()
        
        return UserRegisterResponse(
            message="用户注册成功",
            user_id=new_user.id,
            username=new_user.name
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"用户注册失败: {str(e)}")

@router.get("/validate_regkey/{regkey}")
async def validate_regkey(
    regkey: str,
    session: AsyncSession = Depends(get_async_session),
    http_request: Request = None,
):
    """
    验证注册码是否有效
    
    Args:
        regkey: 注册码
        session: 数据库会话
        
    Returns:
        包含验证结果的字典
    """
    try:
        auth_security_service = AuthSecurityService()
        if http_request:
            xff = http_request.headers.get("x-forwarded-for", "")
            raw_ip = xff.split(",")[0].strip() if xff else (
                http_request.client.host if http_request.client else "unknown"
            )
        else:
            raw_ip = "unknown"
        client_ip = auth_security_service.normalize_ip(raw_ip)
        await auth_security_service.check_register_rate_limit(client_ip)

        if not regkey:
            return {"valid": False, "message": "注册码不能为空"}
        
        # 移除连字符后检查长度
        regkey_clean = regkey.strip().upper()
        regkey_without_dashes = regkey_clean.replace('-', '')
        
        if len(regkey_without_dashes) != 25:
            return {"valid": False, "message": "注册码格式不正确"}
        
        # 查询注册码
        stmt = select(RegKey).where(
            RegKey.name == regkey_clean,
            RegKey.status == 1  # 未使用
        )
        result = await session.exec(stmt)
        regkey_record = result.first()
        
        if regkey_record:
            return {"valid": True, "message": "注册码有效"}
        else:
            return {"valid": False, "message": "注册码无效或已被使用"}
            
    except Exception as e:
        return {"valid": False, "message": f"验证失败: {str(e)}"}
