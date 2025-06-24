from typing import Annotated, Union

from fastapi import Form
from pydantic import BaseModel, ConfigDict, constr, EmailStr, field_validator

model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    username: constr(
        min_length=3,
        max_length=30,
        strip_whitespace=True,
        pattern=r"^[a-zA-Z0-9_]+$"
    )
    email: EmailStr
    password: str

    @field_validator("username")
    def username_no_spaces(cls, v):
        if " " in v:
            raise ValueError("Username cannot contain spaces")
        return v

    model_config = ConfigDict(from_attributes=True)


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    model_config = ConfigDict(from_attributes=True)


class CustomLoginForm:
    def __init__(
        self,
        *,
        username: Annotated[str, Form(...)],
        password: Annotated[str, Form(...)],

    ):
        self.username = username
        self.password = password

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
