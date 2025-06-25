from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.db.repositories.device_repository import DeviceRepository
from app.db.repositories.log_repository import LogRepository
from app.db.repositories.user_repository import UserRepository
from app.services.device_services import DeviceService
from app.services.logs_services import LogService
from app.services.user_services import UserService


async def get_auth_service(db: AsyncSession = Depends(get_db)) -> UserService:
    user_repository = UserRepository(db)
    return UserService(user_repository)


async def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


async def get_user_service(
        user_repository: UserRepository = Depends(get_user_repository)
) -> UserService:
    return UserService(user_repository)


async def get_log_repository(db: AsyncSession = Depends(get_db)) -> LogRepository:
    return LogRepository(db)


async def get_log_service(
        log_repository: LogRepository = Depends(get_log_repository)
) -> LogService:
    return LogService(log_repository)

async def get_device_repository(db: AsyncSession = Depends(get_db)) -> DeviceRepository:
    return DeviceRepository(db)

async def get_device_service(
    db: AsyncSession = Depends(get_db),
    device_repository: DeviceRepository = Depends(get_device_repository),
    log_repository: LogRepository = Depends(get_log_repository)
) -> DeviceService:
    return DeviceService(device_repository, log_repository)