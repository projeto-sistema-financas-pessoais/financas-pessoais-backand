from sqlalchemy.ext.asyncio import AsyncSession
from core.database import Session
from typing import Generator, Optional


async def get_session()-> Generator: # type: ignore
    session: AsyncSession = Session()
    try:
        yield session
    finally:
        await session.close()