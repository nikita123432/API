from pydantic import BaseModel, ConfigDict

model_config = ConfigDict(from_attributes=True)

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    model_config = ConfigDict(from_attributes=True)


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    username: str
    password: str
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str
    model_config = ConfigDict(from_attributes=True)


class ChangePassword(BaseModel):
    old_password: str
    new_password: str
    model_config = ConfigDict(from_attributes=True)

class PasswordResetRequest(BaseModel):
    email: str
    model_config = ConfigDict(from_attributes=True)

# Модель для нового пароля
class ResetPassword(BaseModel):
    new_password: str
    model_config = ConfigDict(from_attributes=True)


class VerifyCodeRequest(BaseModel):
    email: str
    code: str
    model_config = ConfigDict(from_attributes=True)

class SetNewPasswordRequest(BaseModel):
    email: str
    code: str
    new_password: str
    model_config = ConfigDict(from_attributes=True)
