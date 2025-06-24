from datetime import datetime
from typing import Tuple, List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models import models


async def create_device_log(db: AsyncSession, user_id: int, action: str, object_type: str, object_id: int,
                            details: dict = None):
    db_log = models.DeviceLog(
        user_id=user_id,
        action=action,
        object_type=object_type,
        object_id=object_id,
        timestamp=datetime.utcnow(),
        details=details
    )
    db.add(db_log)
    await db.commit()
    await db.refresh(db_log)
    return db_log


async def get_device_log(db: AsyncSession,page_number: int = 1, page_size: int = 100, object_type: str = None,
                         object_id: int = None, user_id: int = None)-> Tuple[List[models.DeviceLog], int]:
    offset = (page_number - 1) * page_size
    query = select(models.DeviceLog).options(
        joinedload(models.DeviceLog.user)
    )

    if object_type:
        query = query.where(models.DeviceLog.object_type == object_type)
    if object_id:
        query = query.where(models.DeviceLog.object_id == object_id)
    if user_id:
        query = query.where(models.DeviceLog.user_id == user_id)

    data_query = query.order_by(
        models.DeviceLog.timestamp.desc()
    ).offset(offset).limit(page_size)

    count_query = select(func.count(models.DeviceLog.id))

    if object_type:
        count_query = count_query.where(models.DeviceLog.object_type == object_type)
    if object_id:
        count_query = count_query.where(models.DeviceLog.object_id == object_id)
    if user_id:
        count_query = count_query.where(models.DeviceLog.user_id == user_id)

    result = await db.execute(data_query)
    logs = result.unique().scalars().all()

    total = await db.scalar(count_query)

    return logs, total
