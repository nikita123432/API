from datetime import datetime
from typing import Tuple, List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.models import DeviceLog


class LogRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_audit_logs(
            self,
            page_number: int = 1,
            page_size: int = 100,
            object_type: Optional[str] = None,
            object_id: Optional[int] = None,
            user_id: Optional[int] = None
    ) -> Tuple[List[DeviceLog], int]:
        offset = (page_number - 1) * page_size

        query = select(DeviceLog).options(
            joinedload(DeviceLog.user)
        ).order_by(
            DeviceLog.timestamp.desc()
        ).offset(offset).limit(page_size)

        count_query = select(func.count(DeviceLog.id))

        filters = []
        if object_type:
            filters.append(DeviceLog.object_type == object_type)
        if object_id:
            filters.append(DeviceLog.object_id == object_id)
        if user_id:
            filters.append(DeviceLog.user_id == user_id)

        if filters:
            query = query.where(*filters)
            count_query = count_query.where(*filters)

        result = await self.db.execute(query)
        logs = result.unique().scalars().all()

        total = await self.db.scalar(count_query)

        return logs, total

    async def create_device_log(
            self,
            user_id: int,
            action: str,
            object_type: str,
            object_id: int,
            details: dict = None
    ) -> DeviceLog:
        db_log = DeviceLog(
            user_id=user_id,
            action=action,
            object_type=object_type,
            object_id=object_id,
            timestamp=datetime.utcnow(),
            details=details
        )
        self.db.add(db_log)
        await self.db.commit()
        await self.db.refresh(db_log)
        return db_log
