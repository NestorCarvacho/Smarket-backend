from app.core.exceptions import ConflictError, UnauthorizedError
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
from app.schemas.auth import TokenResponse


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
        if user is None or not verify_password(password, user.hashed_password):
            raise UnauthorizedError("Email o password invalidos")
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

        return self.issue_tokens(user)
