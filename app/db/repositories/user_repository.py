from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models import models


async def get_user_by_id(db: AsyncSession, user_id: str):
    try:
        user_id_int = int(user_id)
    except ValueError:
        return None

    return await db.scalar(select(models.User).where(models.User.id == user_id_int))




