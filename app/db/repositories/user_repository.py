from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.models import User


async def get_user_by_id(db: AsyncSession, user_id: str):
    try:
        user_id_int = int(user_id)
    except ValueError:
        return None

    return await db.scalar(select(User).where(User.id == user_id_int))


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_username(self, username: str) -> User | None:
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def create(self, user: User) -> User:
        self.db.add(user)
            # await self.db.commit()
            # await self.db.refresh(user)
        return user

    async def get_user_by_name(self, username: str) -> User | None:
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def update_user_password(self, user: User, new_hashed_password: str) -> User:
        user.hashed_password = new_hashed_password
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user