from fastapi import FastAPI, Depends, HTTPException, Response, APIRouter, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.repositories import device_repository
from app.models import models
from app.models.models import User
from app.schemas import device_schemas

from app.database import get_db
from app.schemas.device_schemas import ISGDevice
from app.schemas.pagination_schemas import PaginatedResponse

router = APIRouter(tags=["devices"])


@router.post("/devices/", response_model=ISGDevice)
async def create_device(
        device: device_schemas.ISGDeviceCreate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    return await device_repository.create_device(db, device, current_user.id)


@router.get("/devices", response_model=PaginatedResponse[ISGDevice])
async def list_devices(
        page_number: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=100),
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    devices, total = await device_repository.get_devices(
        db,
        page_number=page_number,
        page_size=page_size
    )

    num_pages = (total + page_size - 1) // page_size
    return {
        "data": devices,
        "pagination": {
            "page_number": page_number,
            "page_size": page_size,
            "num_pages": num_pages,
            "total_results": total
        }
    }


@router.get("/devices/{device_id}", response_model=ISGDevice)
async def get_device(
        device_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    device = await device_repository.get_device(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@router.put("/device/", response_model=ISGDevice)
async def update_device(
        device_id: int,
        device: device_schemas.ISGDeviceCreate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    try:
        updated_device = await device_repository.update_device(db, device_id, device, current_user.id)
        if updated_device is None:
            raise HTTPException(status_code=404, detail="Device not found")
        return updated_device
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/device/")
async def delete_device(
        device_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    device = await device_repository.delete_device(db, device_id, current_user.id)
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    return f"device {device_id} deleted"
