import os

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

# Асинхронный URL PostgreSQL (формат: postgresql+asyncpg://user:password@host/dbname)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:123123@db:5432/db")

engine = create_async_engine(DATABASE_URL, echo=True)


# Используем async_sessionmaker вместо sessionmaker
AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession
)

Base = declarative_base()

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session