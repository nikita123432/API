import asyncio
import datetime
import smtplib
from contextlib import asynccontextmanager
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from random import randint

import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from auth import authenticate_user, pwd_context, security
from models.models import User
from database import engine, Base, get_db
from sqlalchemy.future import select
from datetime import datetime, timedelta

from schemas.userSchema import UserCreate, Token, UserLogin, UserResponse, ChangePassword, PasswordResetRequest, \
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
@app.post("/login", response_model=Token)
async def login(credentials: UserLogin, response: Response):
    user = await authenticate_user(credentials.username, credentials.password)
    if not user:
        raise HTTPException(401, "Invalid credentials")

    # Создаем access токен и сразу получаем CSRF
    access_token = security.create_access_token(
        uid=str(user.id),
    )
    # Генерация CSRF токена
    csrf_token = security.create_access_token(
        uid=str(user.id),
        fresh=True  # Например, fresh токен для CSRF
    )

    # Устанавливаем куки
    security.set_access_cookies(access_token, response)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "csrf_token": csrf_token
    }

# Защищенный роут
@app.get("/protected", dependencies=[Depends(security.access_token_required)])
async def protected():
    return {"message": "Hello"}


# Обновлённый эндпоинт с использованием get_current_user
@app.put("/change-password")
async def change_password(
        passwords: ChangePassword,
        current_user: User = Depends(authenticate_user),  # Используем зависимость для получения пользователя
        db: AsyncSession = Depends(get_db)
):
    user = current_user

    # Проверка старого пароля
    if not pwd_context.verify(passwords.old_password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect old password")

    # Дополнительная валидация нового пароля
    if len(passwords.new_password) < 8:
        raise HTTPException(status_code=400, detail="New password is too short (minimum 8 characters)")

    # Хешируем новый пароль
    new_hashed_password = pwd_context.hash(passwords.new_password)

    # Обновляем пароль в базе данных
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

if __name__ == "__main__":
    uvicorn.run("main.app", host="0.0.0.0", port=8000)