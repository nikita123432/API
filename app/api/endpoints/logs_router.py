
from fastapi import Depends, APIRouter, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.repositories import log_repository
from app.database import get_db
from app.dependencies import get_log_service
from app.models.models import User
from app.schemas.log_schema import LogWithUser
from app.schemas.pagination_schemas import PaginatedResponse
from app.services.logs_services import LogService

router = APIRouter(tags=["logs"])


@router.get("/audit-logs/", response_model=PaginatedResponse[LogWithUser])
async def get_audit_logs(
    page_number: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    object_type: str = Query(None),
    object_id: int = Query(None),
    log_service: LogService = Depends(get_log_service),
    current_user: User = Depends(get_current_user),
):
    return await log_service.get_audit_logs(
        page_number=page_number,
        page_size=page_size,
        object_type=object_type,
        object_id=object_id,
        user_id=current_user.id  )

