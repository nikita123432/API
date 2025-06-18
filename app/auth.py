from types import SimpleNamespace

from authx import AuthX, AuthXConfig
from sqlalchemy.sql.functions import user

from app.models.models import User
from app.database import AsyncSessionLocal
from sqlalchemy.future import select
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Правильная инициализация AuthX

config = AuthXConfig()
config.JWT_SECRET_KEY = "d16841d40972f840c12983edf8df6586f0fcbc2fa3de9bf278c1cc9a97796d2b"
config.JWT_ACCESS_COOKIE_NAME = "access_token"
config.JWT_TOKEN_LOCATION = ["cookies"]
config.JWT_ALGORITHM = "HS256"


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


