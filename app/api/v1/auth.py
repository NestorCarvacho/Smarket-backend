from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import get_auth_service
from app.schemas.auth import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    MessageResponse,
    RecoverPasswordRequest,
    RefreshRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
)
from app.schemas.user import UserRead
from app.services.auth_service import AuthService

router = APIRouter()

AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(payload: UserRegisterRequest, auth_service: AuthServiceDep) -> UserRead:
    user = await auth_service.register(payload.email, payload.password)
    return UserRead.model_validate(user)


@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLoginRequest, auth_service: AuthServiceDep) -> TokenResponse:
    user = await auth_service.authenticate(payload.email, payload.password)
    return auth_service.issue_tokens(user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest, auth_service: AuthServiceDep) -> TokenResponse:
    return await auth_service.refresh_tokens(payload.refresh_token)


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(
    payload: ForgotPasswordRequest, auth_service: AuthServiceDep
) -> ForgotPasswordResponse:
    return await auth_service.request_password_reset(payload.email)


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    payload: ResetPasswordRequest, auth_service: AuthServiceDep
) -> MessageResponse:
    await auth_service.reset_password(payload.email, payload.reset_code, payload.new_password)
    return MessageResponse(message="Contraseña actualizada. Ya podes iniciar sesion.")


@router.post("/recover-password", response_model=MessageResponse)
async def recover_password(
    payload: RecoverPasswordRequest, auth_service: AuthServiceDep
) -> MessageResponse:
    await auth_service.recover_password(payload.email, payload.new_password)
    return MessageResponse(message="Contraseña actualizada. Ya podes iniciar sesion.")
