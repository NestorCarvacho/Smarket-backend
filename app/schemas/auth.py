from pydantic import BaseModel, EmailStr, Field


class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    message: str
    reset_code: str | None = None


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    reset_code: str = Field(min_length=4, max_length=12)
    new_password: str = Field(min_length=8, max_length=128)


class MessageResponse(BaseModel):
    message: str
