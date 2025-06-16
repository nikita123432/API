from types import SimpleNamespace

from authx import AuthX, AuthXConfig
from sqlalchemy.sql.functions import user

from database import AsyncSessionLocal
from models import User
from sqlalchemy.future import select
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Правильная инициализация AuthX

config = AuthXConfig()
config.JWT_SECRET_KEY = "SECRET_KEY"
config.JWT_ACCESS_COOKIE_NAME = "access_token"
config.JWT_TOKEN_LOCATION = ["cookies"]

security = AuthX(config=config)

async def authenticate_user(username: str, password: str) -> User | None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()
        if not user:
            return None
        if not pwd_context.verify(password, user.hashed_password):
            return None
        return user


