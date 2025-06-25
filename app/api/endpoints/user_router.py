import datetime

from random import randint

from fastapi import Depends, HTTPException, Response, APIRouter, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user, set_access_cookies
from app.db.repositories.user_repository import UserRepository
from app.dependencies import get_auth_service, get_user_service
from app.services.auth import authenticate_user, pwd_context, security, send_email_with_code
from app.models.models import User
from app.database import get_db
from sqlalchemy.future import select
from datetime import datetime, timedelta

from app.schemas.user_schema import UserCreate, Token, UserResponse, ChangePassword, PasswordResetRequest, \
    SetNewPasswordRequest, CustomLoginForm
from app.services.user_services import UserService

router = APIRouter(tags=["auth"])


@router.post("/register", response_model=UserResponse)
async def register(
        user: UserCreate,
        db: AsyncSession = Depends(get_db)
):
    user_repository = UserRepository(db)
    user_service = UserService(user_repository)

    new_user = await user_service.register_user(user)
    return new_user


@router.post("/login", response_model=Token)
async def login(
        response: Response,
        form_data: CustomLoginForm = Depends(),
        auth_service: UserService = Depends(get_auth_service)
):
    auth_data = await auth_service.authenticate_user(
        form_data.username,
        form_data.password
    )

    set_access_cookies(auth_data["access_token"], response)

    return {
        "access_token": auth_data["access_token"],
        "token_type": "bearer"
    }
@router.put("/change-password")
async def change_password(
    passwords: ChangePassword,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    return await user_service.change_password(
        user=current_user,
        old_password=passwords.old_password,
        new_password=passwords.new_password
    )

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

