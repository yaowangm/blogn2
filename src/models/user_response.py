"""
用户响应模型
定义安全的用户数据响应结构，确保敏感字段不会泄露
"""

from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class UserPublicResponse(BaseModel):
    """公开用户信息响应模型 - 不包含任何敏感信息"""
    id: int
    name: str
    state: int
    regtime: Optional[datetime] = None
    projectid: Optional[int] = None
    intropiid: Optional[int] = None
    lastupdate: Optional[datetime] = None


class UserPrivateResponse(BaseModel):
    """私有用户信息响应模型 - 包含邮箱等敏感信息，但不包含密码"""
    id: int
    name: str
    email: Optional[str] = None
    state: int
    regtime: Optional[datetime] = None
    iplog: Optional[str] = None
    point: Optional[int] = None
    projectid: Optional[int] = None
    intropiid: Optional[int] = None
    lastupdate: Optional[datetime] = None


class UserListResponse(BaseModel):
    """用户列表响应模型 - 用于分页用户列表"""
    id: int
    name: str
    state: int
    regtime: Optional[datetime] = None
    point: Optional[int] = None
    projectid: Optional[int] = None
    project_name: Optional[str] = None


class UserSummaryResponse(BaseModel):
    """用户摘要响应模型 - 用于统计信息"""
    id: int
    name: str
    regtime: Optional[datetime] = None


class UserProfileResponse(BaseModel):
    """用户个人资料响应模型 - 根据权限动态返回数据"""
    id: int
    name: str
    state: int
    regtime: Optional[datetime] = None
    projectid: Optional[int] = None
    intropiid: Optional[int] = None
    lastupdate: Optional[datetime] = None
    
    # 可选字段 - 根据权限决定是否包含
    email: Optional[str] = Field(None, description="邮箱地址（需要权限）")
    iplog: Optional[str] = Field(None, description="IP日志（需要权限）")
    point: Optional[int] = Field(None, description="积分（需要权限）")
    
    # 权限信息
    permissions: Dict[str, bool] = Field(..., description="当前用户的权限信息")


def create_user_public_response(user_data: Dict[str, Any]) -> UserPublicResponse:
    """创建公开用户响应"""
    return UserPublicResponse(
        id=user_data.get("id"),
        name=user_data.get("name"),
        state=user_data.get("state"),
        regtime=user_data.get("regtime"),
        projectid=user_data.get("projectid"),
        intropiid=user_data.get("intropiid"),
        lastupdate=user_data.get("lastupdate")
    )


def create_user_private_response(user_data: Dict[str, Any]) -> UserPrivateResponse:
    """创建私有用户响应（不包含密码）"""
    return UserPrivateResponse(
        id=user_data.get("id"),
        name=user_data.get("name"),
        email=user_data.get("email"),
        state=user_data.get("state"),
        regtime=user_data.get("regtime"),
        iplog=user_data.get("iplog"),
        point=user_data.get("point"),
        projectid=user_data.get("projectid"),
        intropiid=user_data.get("intropiid"),
        lastupdate=user_data.get("lastupdate")
    )


def create_user_list_response(user_data: Dict[str, Any]) -> UserListResponse:
    """创建用户列表响应"""
    return UserListResponse(
        id=user_data.get("id"),
        name=user_data.get("name"),
        state=user_data.get("state"),
        regtime=user_data.get("regtime"),
        point=user_data.get("point"),
        projectid=user_data.get("projectid"),
        project_name=user_data.get("project_name")
    )


def create_user_summary_response(user_data: Dict[str, Any]) -> UserSummaryResponse:
    """创建用户摘要响应"""
    return UserSummaryResponse(
        id=user_data.get("id"),
        name=user_data.get("name"),
        regtime=user_data.get("regtime")
    )


def create_user_profile_response(
    user_data: Dict[str, Any], 
    permissions: Dict[str, bool]
) -> UserProfileResponse:
    """创建用户个人资料响应（根据权限动态包含字段）"""
    response_data = {
        "id": user_data.get("id"),
        "name": user_data.get("name"),
        "state": user_data.get("state"),
        "regtime": user_data.get("regtime"),
        "projectid": user_data.get("projectid"),
        "intropiid": user_data.get("intropiid"),
        "lastupdate": user_data.get("lastupdate"),
        "permissions": permissions
    }
    
    # 根据权限添加敏感字段
    if permissions.get("can_view_email"):
        response_data["email"] = user_data.get("email")
    if permissions.get("can_view_iplog"):
        response_data["iplog"] = user_data.get("iplog")
    if permissions.get("can_view_point"):
        response_data["point"] = user_data.get("point")
    
    return UserProfileResponse(**response_data)
