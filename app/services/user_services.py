from fastapi import HTTPException

from app.db.repositories.user_repository import UserRepository
from app.models.models import User
from app.schemas.user_schema import UserCreate
from app.services.auth import pwd_context


class UserService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def register_user(self, user_data: UserCreate) -> User:

        if await self.user_repository.get_by_username(user_data.username):
            raise HTTPException(status_code=400, detail="Username already exists")

        if await self.user_repository.get_by_email(user_data.email):
            raise HTTPException(status_code=400, detail="Email already exists")

        hashed_password = pwd_context.hash(user_data.password)

        new_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password
        )

        # Сохранение
        return await self.user_repository.create(new_user)