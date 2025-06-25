from fastapi import Depends, HTTPException,  APIRouter, Query

from app.core.security import get_current_user
from app.dependencies import get_device_service
from app.models.models import User
from app.schemas import device_schemas

from app.schemas.device_schemas import ISGDevice, ISGDeviceCreate
from app.schemas.pagination_schemas import PaginatedResponse
from app.services.device_services import DeviceService

router = APIRouter(tags=["devices"])


@router.post("/devices/", response_model=device_schemas.ISGDevice)
async def create_device(
    device: device_schemas.ISGDeviceCreate,
    device_service: DeviceService = Depends(get_device_service),
    current_user: User = Depends(get_current_user),
):
    return await device_service.create_device(
        device_data=device.dict(),
        user_id=current_user.id
    )
@router.get("/devices", response_model=PaginatedResponse[ISGDevice])
async def list_devices(
    page_number: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    device_service: DeviceService = Depends(get_device_service),
    current_user: User = Depends(get_current_user),
):
    return await device_service.list_devices(
        page_number=page_number,
        page_size=page_size
    )

@router.get("/devices/{device_id}", response_model=ISGDevice)
async def get_device(
    device_id: int,
    device_service: DeviceService = Depends(get_device_service),
    current_user: User = Depends(get_current_user),
):
    return await device_service.get_device(device_id)

@router.put("/devices/{device_id}", response_model=ISGDevice)
async def update_device(
    device_id: int,
    device: ISGDeviceCreate,
    device_service: DeviceService = Depends(get_device_service),
    current_user: User = Depends(get_current_user),
):
    try:
        return await device_service.update_device(
            device_id=device_id,
            update_data=device.dict(),
            user_id=current_user.id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/devices/{device_id}")
async def delete_device(
    device_id: int,
    device_service: DeviceService = Depends(get_device_service),
    current_user: User = Depends(get_current_user),
):
    try:
        return await device_service.delete_device(
            device_id=device_id,
            user_id=current_user.id
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting device: {str(e)}"
        )