
from fastapi import Depends, APIRouter, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.repositories import log_repository
from app.database import get_db
from app.models.models import User
from app.schemas.log_schema import LogWithUser
from app.schemas.pagination_schemas import PaginatedResponse

router = APIRouter(tags=["logs"])


@router.get("/audit-logs/", response_model=PaginatedResponse[LogWithUser])
async def get_audit_logs(
        page_number: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=100),
        object_type: str = Query(None),
        object_id: int = Query(None),
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),

):

    logs, total = await log_repository.get_device_log(
        db,
        page_number=page_number,
        page_size=page_size,
        object_type=object_type,
        object_id=object_id
    )

    result = []
    for log in logs:
        log_data = LogWithUser.from_orm(log)
        log_data.username = log.user.username
        result.append(log_data)

    num_pages = (total + page_size - 1) // page_size

    return {
        "data": result,
        "pagination": {
            "page_number": page_number,
            "page_size": page_size,
            "num_pages": num_pages,
            "total_results": total
        }
    }
