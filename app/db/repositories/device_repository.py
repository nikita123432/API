from typing import Tuple, List

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.log_repository import create_device_log
from app.models import models
from app.schemas import device_schemas


async def get_device(db: AsyncSession, device_id: int):
    return await db.get(models.ISGDevice, device_id)


async def create_device(db: AsyncSession, device: device_schemas.ISGDeviceCreate, user_id: int):
    try:
        if device.uid or device.ip_address or device.port:
            existing = await db.execute(
                select(models.ISGDevice).filter(
                    models.ISGDevice.uid == device.uid or
                    models.ISGDevice.ip_address == device.ip_address
                    or models.ISGDevice.port == device.port
                )
            )
            if existing.scalar_one_or_none():
                raise HTTPException(
                    400,
                    detail=f"Device already exists"
                )

        db_device = models.ISGDevice(**device.dict())
        db.add(db_device)
        await db.commit()
        await db.refresh(db_device)

        await create_device_log(db, user_id=user_id, action="Create", object_type="isg_device", object_id=db_device.id,
                                details=device.dict())

        return db_device

    except IntegrityError as e:
        await db.rollback()
        if "unique constraint" in str(e).lower():
            raise HTTPException(
                400,
                detail="Device with these parameters already exists"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            400,
            detail=f"Unexpected error: {str(e)}"
        )


async def get_devices(db: AsyncSession, page_number: int = 1, page_size: int = 10) -> Tuple[List[models.ISGDevice], int]:
    offset = (page_number - 1) * page_size

    stmt = select(models.ISGDevice).offset(offset).limit(page_size)
    result = await db.execute(stmt)
    devices = result.scalars().all()

    total = await db.scalar(select(func.count(models.ISGDevice.id)))


    return devices, total


async def update_device(db: AsyncSession, device_id: int, device: device_schemas.ISGDeviceCreate, user_id: int):
    db_device = await get_device(db, device_id)
    if not db_device:
        return None

    if db_device:
        new_uid = device.uid
        if new_uid and new_uid != db_device.uid:
            stmt = select(models.ISGDevice).where(
                models.ISGDevice.uid == new_uid,
                models.ISGDevice.id != device_id
            )
            result = await db.execute(stmt)
            if result.scalar_one_or_none():
                raise ValueError(f"UID '{new_uid}' already exists")

        old_values = {c.name: getattr(db_device, c.name) for c in db_device.__table__.columns}

        for key, value in device.dict().items():
            setattr(db_device, key, value)
        try:
            await db.commit()
            await db.refresh(db_device)
        except IntegrityError as e:
            await db.rollback()
            if "unique constraint" in str(e).lower():
                raise ValueError("Data update causes duplicate in unique field")
            raise

        new_values = {c.name: getattr(db_device, c.name) for c in db_device.__table__.columns}
        changes = {k: {"old": old_values[k], "new": new_values[k]}
                   for k in old_values if old_values[k] != new_values[k]}
        if changes:
            await create_device_log(
                db,
                user_id=user_id,
                action="update",
                object_type="isg_device",
                object_id=device_id,
                details=changes
            )

    return db_device


async def delete_device(db: AsyncSession, device_id: int, user_id: int):
    db_device = await get_device(db, device_id)
    if db_device:
        device_data = {c.name: getattr(db_device, c.name) for c in db_device.__table__.columns}

        await db.delete(db_device)
        await db.commit()

        await create_device_log(
            db,
            user_id=user_id,
            action="delete",
            object_type="isg_device",
            object_id=device_id,
            details=device_data
        )

    return f"device {device_id} deleted"
