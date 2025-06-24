import datetime

from random import randint

from fastapi import Depends, HTTPException, Response, APIRouter, BackgroundTasks, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.models import models
from app.services.auth import authenticate_user, pwd_context, security, send_email_with_code
from app.models.models import User
from app.database import get_db
from sqlalchemy.future import select
from datetime import datetime, timedelta

from app.schemas.user_schema import UserCreate, Token, UserResponse, ChangePassword, PasswordResetRequest, \
    SetNewPasswordRequest, CustomLoginForm

router = APIRouter(tags=["auth"])


@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    username_result = await db.execute(select(User).where(User.username == user.username))
    if username_result.scalar_one_or_none():
        raise HTTPException(400, "Username exists")

    email_result = await db.execute(select(User).where(User.email == user.email))
    if email_result.scalar_one_or_none():
        raise HTTPException(400, "Email exists")

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


@router.post("/login", response_model=Token)
async def login(
        response: Response,
        form_data: CustomLoginForm = Depends(),
        db: AsyncSession = Depends(get_db)
):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(401, "Invalid credentials")

    access_token = security.create_access_token(
        uid=str(user.id),
    )

    security.set_access_cookies(access_token, response)

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.put("/change-password")
async def change_password(
        passwords: ChangePassword,
        current_user: User = Depends(get_current_user),
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


@router.post("/request-password-reset")
async def request_password_reset(request: PasswordResetRequest, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter(User.email == request.email))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        reset_code = str(randint(1000, 9999))
        expiration = datetime.utcnow() + timedelta(minutes=0.5)

        user.reset_code = reset_code
        user.reset_code_expiration = expiration
        db.add(user)
        await db.commit()

        background_tasks.add_task(
            send_email_with_code,
            recipient=user.email,
            code=reset_code
        )

        return {"message": "Verification code sent to email"}

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/set-new-password")
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

