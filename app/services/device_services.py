from typing import Dict, Any

from fastapi import HTTPException, status

from app.db.repositories.device_repository import DeviceRepository
from app.db.repositories.log_repository import LogRepository
from app.schemas.device_schemas import ISGDevice
from app.schemas.pagination_schemas import PaginatedResponse, Pagination


class DeviceService:
    def __init__(
            self,
            device_repository: DeviceRepository,
            log_repository: LogRepository
    ):
        self.device_repository = device_repository
        self.log_repository = log_repository

    async def create_device(
            self,
            device_data: dict,
            user_id: int
    ) -> ISGDevice:
        if await self.device_repository.check_device_exists(
                uid=device_data.get("uid"),
                ip_address=device_data.get("ip_address"),
                port=device_data.get("port")
        ):
            raise HTTPException(
                400,
                detail="Device already exists"
            )
        db_device = await self.device_repository.create_device(device_data, user_id)

        await self.log_repository.create_device_log(
            user_id=user_id,
            action="Create",
            object_type="isg_device",
            object_id=db_device.id,
            details=device_data
        )

        return db_device

    async def list_devices(
            self,
            page_number: int,
            page_size: int
    ) -> PaginatedResponse[ISGDevice]:
        devices, total = await self.device_repository.get_devices(
            page_number=page_number,
            page_size=page_size
        )

        num_pages = (total + page_size - 1) // page_size

        return PaginatedResponse[ISGDevice](
            data=devices,
            pagination=Pagination(
                page_number=page_number,
                page_size=page_size,
                num_pages=num_pages,
                total_results=total
            )
        )

    async def get_device(
            self,
            device_id: int
    ) -> ISGDevice:
        device = await self.device_repository.get_device(device_id)

        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )

        return device

    async def update_device(
            self,
            device_id: int,
            update_data: Dict[str, Any],
            user_id: int
    ) -> ISGDevice:
        device = await self.device_repository.get_device(device_id)
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")

        new_uid = update_data.get("uid")
        if new_uid and new_uid != device.uid:
            if await self.device_repository.check_device_exists(new_uid):
                raise ValueError(f"UID '{new_uid}' already exists")

        old_values = {c.name: getattr(device, c.name) for c in device.__table__.columns}

        try:
            updated_device = await self.device_repository.update_device_fields(
                device,
                update_data
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        new_values = {c.name: getattr(updated_device, c.name) for c in device.__table__.columns}

        changes = {
            k: {"old": old_values[k], "new": new_values[k]}
            for k in old_values
            if old_values[k] != new_values[k]
        }

        if changes:
            await self.log_repository.create_device_log(
                user_id=user_id,
                action="update",
                object_type="isg_device",
                object_id=device_id,
                details=changes
            )

        return updated_device

    async def delete_device(
            self,
            device_id: int,
            user_id: int
    ) -> str:

        device = await self.device_repository.get_device(device_id)
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")

        device_data = await self.device_repository.get_device_data(device)

        await self.device_repository.delete_device(device)

        await self.log_repository.create_device_log(
            user_id=user_id,
            action="delete",
            object_type="isg_device",
            object_id=device_id,
            details=device_data
        )

        return f"device {device_id} deleted"