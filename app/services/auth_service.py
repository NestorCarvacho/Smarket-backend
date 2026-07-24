import secrets
from datetime import datetime, timedelta

from app.core.config import settings
from app.core.exceptions import AccountLockedError, ConflictError, UnauthorizedError
from app.core.security import (
    InvalidTokenError,
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.interfaces import IUserRepository
from app.schemas.auth import ForgotPasswordResponse, TokenResponse


class AuthService:
    """Casos de uso de autenticacion. Depende solo de la interfaz de repositorio (DIP)."""

    def __init__(self, user_repository: IUserRepository) -> None:
        self._user_repository = user_repository

    async def register(self, email: str, password: str) -> User:
        existing = await self._user_repository.get_by_email(email)
        if existing is not None:
            raise ConflictError("Ya existe un usuario con ese email")
        return await self._user_repository.create(email, hash_password(password))

    async def authenticate(self, email: str, password: str) -> User:
        user = await self._user_repository.get_by_email(email)
        if user is None:
            raise UnauthorizedError("Email o password invalidos")

        if user.is_locked:
            raise AccountLockedError(
                "Cuenta bloqueada por demasiados intentos. Restablece tu contraseña para desbloquearla."
            )

        if not verify_password(password, user.hashed_password):
            user.failed_login_attempts = int(user.failed_login_attempts or 0) + 1
            remaining = settings.MAX_FAILED_LOGIN_ATTEMPTS - user.failed_login_attempts
            if user.failed_login_attempts >= settings.MAX_FAILED_LOGIN_ATTEMPTS:
                user.is_locked = True
                await self._user_repository.save(user)
                raise AccountLockedError(
                    "Cuenta bloqueada por demasiados intentos. Restablece tu contraseña para desbloquearla."
                )
            await self._user_repository.save(user)
            raise UnauthorizedError(
                f"Email o password invalidos. Te quedan {max(remaining, 0)} intento(s)."
            )

        user.failed_login_attempts = 0
        await self._user_repository.save(user)
        return user

    def issue_tokens(self, user: User) -> TokenResponse:
        subject = str(user.id)
        return TokenResponse(
            access_token=create_access_token(subject),
            refresh_token=create_refresh_token(subject),
        )

    async def refresh_tokens(self, refresh_token: str) -> TokenResponse:
        try:
            user_id = decode_token(refresh_token, TokenType.REFRESH)
        except InvalidTokenError as exc:
            raise UnauthorizedError(str(exc)) from exc

        user = await self._user_repository.get_by_id(int(user_id))
        if user is None:
            raise UnauthorizedError("Usuario no encontrado")
        if user.is_locked:
            raise AccountLockedError(
                "Cuenta bloqueada. Restablece tu contraseña para desbloquearla."
            )

        return self.issue_tokens(user)

    async def request_password_reset(self, email: str) -> ForgotPasswordResponse:
        message = (
            "Si el email existe, generamos un codigo para restablecer la contraseña. "
            "Con ese codigo podes desbloquear la cuenta."
        )
        user = await self._user_repository.get_by_email(email)
        if user is None:
            return ForgotPasswordResponse(message=message, reset_code=None)

        reset_code = f"{secrets.randbelow(1_000_000):06d}"
        user.reset_code_hash = hash_password(reset_code)
        user.reset_code_expires_at = datetime.utcnow() + timedelta(
            minutes=settings.RESET_CODE_EXPIRE_MINUTES
        )
        await self._user_repository.save(user)

        return ForgotPasswordResponse(
            message=message,
            reset_code=reset_code if settings.EXPOSE_RESET_CODES else None,
        )

    async def reset_password(self, email: str, reset_code: str, new_password: str) -> None:
        user = await self._user_repository.get_by_email(email)
        if (
            user is None
            or not user.reset_code_hash
            or not user.reset_code_expires_at
            or user.reset_code_expires_at < datetime.utcnow()
            or not verify_password(reset_code.strip(), user.reset_code_hash)
        ):
            raise UnauthorizedError("Codigo de restablecimiento invalido o expirado")

        user.hashed_password = hash_password(new_password)
        user.is_locked = False
        user.failed_login_attempts = 0
        user.reset_code_hash = None
        user.reset_code_expires_at = None
        await self._user_repository.save(user)
