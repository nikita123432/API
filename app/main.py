import asyncio
import datetime

from contextlib import asynccontextmanager
from random import randint

import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from typer.cli import default_app_names

from app import schemas
from app.crud import crud
from app.crud.crud import send_email_with_code, get_current_user
from app.models import models
from app.schemas import deviceSchemas, logSchema
from app.auth import authenticate_user, pwd_context, security
from app.models.models import User
from app.database import engine, Base, get_db
from sqlalchemy.future import select
from datetime import datetime, timedelta

from app.schemas.userSchema import UserCreate, Token, UserLogin, UserResponse, ChangePassword, PasswordResetRequest, \
    SetNewPasswordRequest


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Код инициализации (заменяет startup event)
    print("Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield  # Здесь приложение работает

    # Код завершения (опционально, заменяет shutdown event)
    print("Closing database connections...")
    await engine.dispose()
app = FastAPI(lifespan=lifespan)

# Регистрация
@app.post("/register", response_model=UserResponse)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == user.username))
    if result.scalar_one_or_none():
        raise HTTPException(400, "Username exists")

    hashed_password = pwd_context.hash(user.password)
    new_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


# Логин
# @app.post("/login", response_model=Token)
# async def login(credentials: UserLogin, response: Response, db: AsyncSession = Depends(get_db)):
#     user = await authenticate_user(credentials.username, credentials.password, db)
#     if not user:
#         raise HTTPException(401, "Invalid credentials")
#
#     # Создаем access токен
#     access_token = security.create_access_token(
#         uid=str(user.id),
#     )
#     # Генерация CSRF токена
#     csrf_token = security.create_access_token(
#         uid=str(user.id),
#         fresh=True
#     )
#
#     security.set_access_cookies(access_token, response)
#
#     return {
#         "access_token": access_token,
#         "token_type": "bearer",
#         "csrf_token": csrf_token
#     }


@app.post("/login", response_model=Token)
async def login(
        response: Response,
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: AsyncSession = Depends(get_db)
):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(401, "Invalid credentials")

    access_token = security.create_access_token(
        uid=str(user.id),  # используем 'sub' вместо 'uid'
    )

    # Устанавливаем куки
    security.set_access_cookies(access_token, response)

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


# Защищенный роут
@app.get("/protected", dependencies=[Depends(security.access_token_required)])
async def protected():
    return {"message": "Hello"}


# смена пароля
@app.put("/change-password")
async def change_password(
        passwords: ChangePassword,
        current_user: User = Depends(authenticate_user),
        db: AsyncSession = Depends(get_db)
):
    user = current_user

    if not pwd_context.verify(passwords.old_password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect old password")

    if len(passwords.new_password) < 8:
        raise HTTPException(status_code=400, detail="New password is too short (minimum 8 characters)")

    new_hashed_password = pwd_context.hash(passwords.new_password)

    user.hashed_password = new_hashed_password
    db.add(user)
    await db.commit()

    return {"message": "Password changed successfully"}



@app.post("/request-password-reset")
async def request_password_reset(request: PasswordResetRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter(User.email == request.email))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Генерация 4-значного кода
    reset_code = str(randint(1000, 9999))
    expiration = datetime.utcnow() + timedelta(minutes=0.5)

    user.reset_code = reset_code
    user.reset_code_expiration = expiration
    db.add(user)
    await db.commit()

    # Отправка письма
    await asyncio.to_thread(
        send_email_with_code,
        "smtp.gmail.com", 587,
        "nikita04mar@gmail.com", "fjmx jyop frnv xhtq",
        user.email, reset_code
    )

    return {"message": "Verification code sent to email"}


@app.post("/set-new-password")
async def set_new_password(request: SetNewPasswordRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter(User.email == request.email))
    user = result.scalar_one_or_none()

    if user is None or user.reset_code != request.code:
        raise HTTPException(status_code=400, detail="Invalid request")

    if user.reset_code_expiration < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Code expired")

    if len(request.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password too short")

    user.hashed_password = pwd_context.hash(request.new_password)
    user.reset_code = None
    user.reset_code_expiration = None
    db.add(user)
    await db.commit()

    return {"message": "Password updated successfully"}


@app.post("/devices/", response_model=deviceSchemas.ISGDevice)
async def create_device(
    device: deviceSchemas.ISGDeviceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return await crud.create_device(db, device, current_user.id)


@app.get("/device/", response_model=deviceSchemas.ISGDevice)
async def get_devices(device_id: int, db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)):
    device = await crud.get_device(db, device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@app.get("/devices/", response_model=list[deviceSchemas.ISGDevice])
async def get_device(skip: int = 0, limit: int = 100 , db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)):
    return await crud.get_devices(db, skip, limit)


@app.put("/device/", response_model=deviceSchemas.ISGDevice)
async def update_device(
    device_id: int,
    device: deviceSchemas.ISGDeviceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    updated_device = await crud.update_device(db, device_id, device, current_user.id)
    if updated_device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    return updated_device


@app.delete("/device/", response_model=deviceSchemas.ISGDevice)
async def delete_device(
    device_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    device = await crud.delete_device(db, device_id, current_user.id)
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@app.get("/audit-logs/", response_model=list[logSchema.LogWithUser])
async def get_audit_logs(
        skip: int = 0,
        limit: int = 100,
        object_type: str = None,
        object_id: int = None,
        db: AsyncSession = Depends(get_db),
):

    logs = await crud.get_device_log(
        db,
        skip=skip,
        limit=limit,
        object_type=object_type,
        object_id=object_id
    )

    # Добавляем имя пользователя к каждой записи
    result = []
    for log in logs:
        log_data = logSchema.LogWithUser    .from_orm(log)
        log_data.username = log.user.username
        result.append(log_data)

    return result


if __name__ == "__main__":
    uvicorn.run("app.main.app", host="0.0.0.0", port=8000, reload=True)