from typing import Tuple, List, Dict, Any

from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import ISGDevice




class DeviceRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_device_exists(
            self,
            uid: str = None,
            ip_address: str = None,
            port: int = None
    ) -> bool:
        if not any([uid, ip_address, port]):
            return False

        query = select(ISGDevice).where(
            (ISGDevice.uid == uid) if uid else False |
            (ISGDevice.ip_address == ip_address) if ip_address else False |
            (ISGDevice.port == port) if port else False
        )

        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None

    async def create_device(
            self,
            device_data: dict,
            user_id: int
    ) -> ISGDevice:
        try:
            db_device = ISGDevice(**device_data)
            self.db.add(db_device)
            await self.db.commit()
            await self.db.refresh(db_device)
            return db_device
        except IntegrityError as e:
            await self.db.rollback()
            if "unique constraint" in str(e).lower():
                raise HTTPException(
                    400,
                    detail="Device with these parameters already exists"
                )
            raise HTTPException(
                500,
                detail=f"Database error: {str(e)}"
            )
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                400,
                detail=f"Unexpected error: {str(e)}"
            )

    async def get_devices(
        self,
        page_number: int = 1,
        page_size: int = 10
    ) -> Tuple[List[ISGDevice], int]:
        offset = (page_number - 1) * page_size

        stmt = select(ISGDevice).offset(offset).limit(page_size)
        result = await self.db.execute(stmt)
        devices = result.scalars().all()

        total = await self.db.scalar(select(func.count(ISGDevice.id)))

        return devices, total

    async def get_device(
            self,
            device_id: int
    ) -> ISGDevice | None:
        return await self.db.get(ISGDevice, device_id)


    async def update_device_fields(
            self,
            device: ISGDevice,
            update_data: Dict[str, Any]
    ) -> ISGDevice:
        try:
            for key, value in update_data.items():
                setattr(device, key, value)

            await self.db.commit()
            await self.db.refresh(device)
            return device
        except IntegrityError as e:
            await self.db.rollback()
            if "unique constraint" in str(e).lower():
                raise ValueError("Data update causes duplicate in unique field")
            raise



    async def delete_device(self, device: ISGDevice):
        await self.db.delete(device)
        await self.db.commit()

    async def get_device_data(self, device: ISGDevice) -> dict:
        return {c.name: getattr(device, c.name) for c in device.__table__.columns}