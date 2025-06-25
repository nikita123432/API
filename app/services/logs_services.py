from typing import Optional

from app.db.repositories.log_repository import LogRepository
from app.models.models import DeviceLog
from app.schemas.log_schema import LogWithUser
from app.schemas.pagination_schemas import PaginatedResponse


class LogService:
    def __init__(self, log_repository: LogRepository):
        self.log_repository = log_repository

    async def get_audit_logs(
            self,
            page_number: int,
            page_size: int,
            object_type: Optional[str] = None,
            object_id: Optional[int] = None,
            user_id: Optional[int] = None
    ) -> PaginatedResponse[LogWithUser]:
        logs, total = await self.log_repository.get_audit_logs(
            page_number=page_number,
            page_size=page_size,
            object_type=object_type,
            object_id=object_id,
            user_id=user_id
        )

        result = []
        for log in logs:
            log_data = LogWithUser.from_orm(log)
            log_data.username = log.user.username
            result.append(log_data)

        num_pages = (total + page_size - 1) // page_size

        return PaginatedResponse[LogWithUser](
            data=result,
            pagination={
                "page_number": page_number,
                "page_size": page_size,
                "num_pages": num_pages,
                "total_results": total
            }
        )

    async def create_device_log(
            self,
            user_id: int,
            action: str,
            object_type: str,
            object_id: int,
            details: dict = None
    ) -> DeviceLog:
        return await self.log_repository.create_device_log(
            user_id=user_id,
            action=action,
            object_type=object_type,
            object_id=object_id,
            details=details
        )
