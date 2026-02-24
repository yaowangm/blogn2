"""
密码重置令牌数据访问层
"""

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from datetime import datetime
from typing import Optional

from src.models.password_reset_token import PasswordResetToken
from src.models.user import User


class PasswordResetTokenRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: int, token: str, expires_at: datetime) -> PasswordResetToken:
        """插入一条密码重置令牌记录"""
        record = PasswordResetToken(
            user_id=user_id,
            token=token,
            expires_at=expires_at,
        )
        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)
        return record

    async def get_valid_token(self, token: str) -> Optional[PasswordResetToken]:
        """根据 token 查询且未过期的记录"""
        now = datetime.utcnow()
        statement = select(PasswordResetToken).where(
            PasswordResetToken.token == token,
            PasswordResetToken.expires_at > now,
        )
        result = await self.session.exec(statement)
        return result.first()

    async def update_password_and_delete_token(
        self, user_id: int, hashed_password: str, token: str
    ) -> None:
        """
        在同一事务中更新用户密码并删除 token，避免密码已改但 token 未删导致可重复使用。
        """
        user = await self.session.get(User, user_id)
        if not user:
            raise ValueError("用户不存在")
        user.password = hashed_password
        statement = select(PasswordResetToken).where(PasswordResetToken.token == token)
        result = await self.session.exec(statement)
        record = result.first()
        if record:
            await self.session.delete(record)
        await self.session.commit()

    async def delete_by_token(self, token: str) -> bool:
        """使用后删除指定 token"""
        statement = select(PasswordResetToken).where(PasswordResetToken.token == token)
        result = await self.session.exec(statement)
        record = result.first()
        if record:
            await self.session.delete(record)
            await self.session.commit()
            return True
        return False

    async def delete_expired(self) -> int:
        """删除过期记录，返回删除条数（可选，供定时任务使用）"""
        now = datetime.utcnow()
        statement = select(PasswordResetToken).where(PasswordResetToken.expires_at <= now)
        result = await self.session.exec(statement)
        records = result.all()
        for record in records:
            await self.session.delete(record)
        if records:
            await self.session.commit()
        return len(records)
