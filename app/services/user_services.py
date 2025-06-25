from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.core.security import create_access_token
from app.db.repositories.user_repository import UserRepository
from app.models.models import User
from app.schemas.user_schema import UserCreate
from app.services.auth import pwd_context


class UserService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def register_user(self, user_data: UserCreate) -> User:

        try:
            async with self.user_repository.db.begin():
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

                await self.user_repository.create(new_user)
                await self.user_repository.db.flush()
                await self.user_repository.db.refresh(new_user)
                return new_user

        except IntegrityError as e:
            raise HTTPException(status_code=400, detail="Username or email already exists")

    async def authenticate_user(self, username: str, password: str) -> dict:
        user = await self.user_repository.get_by_username(username)
        if not user or not pwd_context.verify(password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Incorrect username or password")
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "access_token": create_access_token(str(user.id))
        }

    async def change_password(
            self,
            user: User,
            old_password: str,
            new_password: str
    ) -> dict:
        if not pwd_context.verify(old_password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Incorrect old password")

        if len(new_password) < 8:
            raise HTTPException(
                status_code=400,
                detail="New password is too short (minimum 8 characters)"
            )

        new_hashed_password = pwd_context.hash(new_password)
        await self.user_repository.update_user_password(user, new_hashed_password)

        return {"message": "Password changed successfully"}

