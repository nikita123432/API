import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from fastapi import Depends, HTTPException, status, Cookie
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import security
from app.database import get_db
from app.models import models
from app.schemas import deviceSchemas


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


async def get_user_by_id(db: AsyncSession, user_id: str):
    try:
        user_id_int = int(user_id)
    except ValueError:
        return None

    return await db.scalar(select(models.User).where(models.User.id == user_id_int))


async def get_current_user(
    token_header: str = Depends(oauth2_scheme),  # Для Swagger (Authorization header)
    token_cookie: str = Cookie(None, alias="access_token"),  # Для браузера (cookie)
    db: AsyncSession = Depends(get_db)
):
    # Проверяем оба источника токена
    token = token_header or token_cookie
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(
            token,
            security.config.JWT_SECRET_KEY,
            algorithms=[security.config.JWT_ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token verification failed",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user

def send_email_with_code(smtp_server, smtp_port, sender_email, sender_password, recipient_email, code):
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = 'Your Password Reset Code'

    body = f"Your password reset code is: {code}\nIt is valid for 10 minutes."
    msg.attach(MIMEText(body, 'plain'))

    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(sender_email, sender_password)
    server.sendmail(sender_email, recipient_email, msg.as_string())
    server.quit()


async def get_device(db: AsyncSession, device_id: int):
    return await db.get(models.ISGDevice, device_id)


async def create_device(db: AsyncSession, device: deviceSchemas.ISGDeviceCreate, user_id: int):
    db_device = models.ISGDevice(**device.dict())
    db.add(db_device)
    await db.commit()
    await db.refresh(db_device)

    await create_device_log(db, user_id=user_id, action="Create", object_type="isg_device", object_id=db_device.id, details=device.dict())

    return db_device


async def get_devices(db: AsyncSession, skip: int = 0, limit: int = 100):
    stmt = select(models.ISGDevice).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


async def update_device(db: AsyncSession, device_id: int, device: deviceSchemas.ISGDeviceCreate, user_id: int):
    db_device = await get_device(db, device_id)
    if db_device:

        old_values = {c.name: getattr(db_device, c.name) for c in db_device.__table__.columns}

        for key, value in device.dict().items():
            setattr(db_device, key, value)

        await db.commit()
        await db.refresh(db_device)

        new_values = {c.name: getattr(db_device, c.name) for c in db_device.__table__.columns}
        changes = {k: {"old": old_values[k], "new": new_values[k]}
                   for k in old_values if old_values[k] != new_values[k]}

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

    return db_device


async def create_device_log(db: AsyncSession, user_id: int, action: str, object_type: str, object_id: int, details: dict=None):
    db_log = models.DeviceLog(
        user_id=user_id,
        action=action,
        object_type=object_type,
        object_id=object_id,
        timestamp=datetime.utcnow(),  # Добавляем текущее время
        details=details
    )
    db.add(db_log)
    await db.commit()
    await db.refresh(db_log)
    return db_log


async def get_device_log(db: AsyncSession, skip: int = 0, limit: int = 100, object_type: str = None, object_id: int = None, user_id: int = None):
    query = select(models.DeviceLog).options(
        selectinload(models.DeviceLog.user)  #
    )

    if object_type:
        query = query.where(models.DeviceLog.object_type == object_type)
    if object_id:
        query = query.where(models.DeviceLog.object_id == object_id)
    if user_id:
        query = query.where(models.DeviceLog.user_id == user_id)

    query = query.offset(skip).limit(limit).order_by(models.DeviceLog.timestamp.desc())

    result = await db.execute(query)
    return result.scalars().all()

