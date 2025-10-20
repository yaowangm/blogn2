from typing import Optional
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models.glovar import Glovar


class GlovarRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_value(self, varname: str) -> Optional[str]:
        statement = select(Glovar).where(Glovar.varname == varname)
        result = await self.session.exec(statement)
        glovar = result.first()
        return getattr(glovar, "varvalue", None) if glovar else None


