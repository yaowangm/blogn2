from src.utils.time_utils import TimeUtils
"""
JWT认证服务
提供用户登录、令牌生成和验证功能
"""

import hashlib
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
import os
from src.utils.password_hash import bcrypt_hash, bcrypt_verify
from sqlmodel import select

from src.models.user import User
from src.repositories.user_repository import UserRepository

class AuthService:
    """JWT认证服务"""
    
    def __init__(self, user_repo: UserRepository, secret_key: str, algorithm: str = "HS256"):
        self.user_repo = user_repo
        self.secret_key = secret_key
        self.algorithm = algorithm
        
        # JWT配置
        self.access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))  # 访问令牌过期时间
        self.refresh_token_expire_days = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))      # 刷新令牌过期天数
    
    def verify_password(self, plain_password: str, stored_hash: str) -> bool:
        """
        验证密码，支持两种格式：
        1. 直接bcrypt哈希（旧格式）
        2. MD5+bcrypt双重哈希（新格式）
        """
        try:
            # 检查是否是bcrypt格式
            if stored_hash.startswith('$2b$') and len(stored_hash) == 60:
                # 尝试直接验证（旧格式）
                if bcrypt_verify(plain_password, stored_hash):
                    return True
                
                # 如果不是直接验证，尝试MD5+bcrypt双重哈希（新格式）
                md5_hash = hashlib.md5(plain_password.encode()).hexdigest()
                return bcrypt_verify(md5_hash, stored_hash)
            else:
                # 非bcrypt格式，尝试MD5+bcrypt双重哈希
                md5_hash = hashlib.md5(plain_password.encode()).hexdigest()
                return bcrypt_verify(md5_hash, stored_hash)
        except Exception:
            return False
    
    def hash_password(self, password: str) -> str:
        """
        哈希密码：password → MD5 → bcrypt
        用于新用户注册或密码修改
        """
        md5_hash = hashlib.md5(password.encode()).hexdigest()
        return bcrypt_hash(md5_hash)
    
    async def authenticate_user(self, username_or_email: str, password: str, client_ip: str) -> Optional[User]:
        """
        用户认证
        
        Args:
            username_or_email: 用户名或邮箱
            password: 密码
            client_ip: 客户端IP地址
            
        Returns:
            User: 认证成功的用户对象，失败返回None
        """
        try:
            # 查找用户（支持用户名或邮箱登录）
            user = await self.user_repo.get_by_name(username_or_email)
            if not user:
                user = await self.user_repo.get_by_email(username_or_email)
            
            if not user:
                return None
            
            # 检查用户状态
            if user.state == 0 or user.state == 2:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="该用户已经被冻结"
                )
            
            # 验证密码
            if not self.verify_password(password, user.password):
                return None
            
            # 更新最后登录信息
            user.lastupdate = TimeUtils.now_utc()
            user.iplog = client_ip
            await self.user_repo.update(user)
            
            return user
            
        except HTTPException:
            raise
        except Exception:
            return None
    
    def create_access_token(self, user_data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        创建访问令牌
        
        Args:
            user_data: 用户数据
            expires_delta: 过期时间增量
            
        Returns:
            str: JWT访问令牌
        """
        to_encode = user_data.copy()
        
        if expires_delta:
            expire = datetime.now(timezone.utc).replace(tzinfo=None) + expires_delta
        else:
            expire = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc).replace(tzinfo=None),
            "type": "access"
        })
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(self, user_data: Dict[str, Any]) -> str:
        """
        创建刷新令牌
        
        Args:
            user_data: 用户数据
            
        Returns:
            str: JWT刷新令牌
        """
        to_encode = user_data.copy()
        expire = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=self.refresh_token_expire_days)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc).replace(tzinfo=None),
            "type": "refresh"
        })
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        验证JWT令牌
        
        Args:
            token: JWT令牌
            
        Returns:
            Dict: 解码后的令牌数据，验证失败返回None
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # 检查令牌类型
            if payload.get("type") != "access":
                return None
            
            # 检查过期时间
            exp = payload.get("exp")
            if exp is None:
                return None
                
            current_time = datetime.now(timezone.utc).replace(tzinfo=None)
            exp_time = datetime.fromtimestamp(exp)
            
            if current_time > exp_time:
                return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
        except Exception:
            return None
    
    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """
        使用刷新令牌获取新的访问令牌
        
        Args:
            refresh_token: 刷新令牌
            
        Returns:
            str: 新的访问令牌，失败返回None
        """
        try:
            payload = jwt.decode(refresh_token, self.secret_key, algorithms=[self.algorithm])
            
            # 检查令牌类型
            if payload.get("type") != "refresh":
                return None
            
            # 检查过期时间
            exp = payload.get("exp")
            if exp is None:
                return None
                
            if datetime.now(timezone.utc).replace(tzinfo=None) > datetime.fromtimestamp(exp):
                return None
            
            # 创建新的访问令牌
            user_data = {
                "user_id": payload.get("user_id"),
                "username": payload.get("username"),
                "role": payload.get("role")
            }
            
            return self.create_access_token(user_data)
            
        except Exception:
            return None
    
    def get_user_from_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        从令牌中获取用户信息
        
        Args:
            token: JWT令牌
            
        Returns:
            Dict: 用户信息，验证失败返回None
        """
        payload = self.verify_token(token)
        if payload:
            return {
                "user_id": payload.get("user_id"),
                "username": payload.get("username"),
                "role": payload.get("role"),
                "exp": payload.get("exp")
            }
        return None
