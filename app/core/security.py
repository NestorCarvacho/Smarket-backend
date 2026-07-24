"""Utilidades de seguridad: hashing de passwords y manejo de JWT.

Aislar esto en un modulo propio permite que el resto de la app (services,
repositories) no dependa directamente de "jose" o "passlib" (Dependency
Inversion): si el dia de mañana se cambia la libreria de JWT, solo se
modifica este archivo.
"""

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"


class InvalidTokenError(Exception):
    pass


def hash_password(plain_password: str) -> str:
    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return _pwd_context.verify(plain_password, hashed_password)


def _create_token(subject: str, token_type: TokenType, expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type.value,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_access_token(subject: str) -> str:
    return _create_token(
        subject, TokenType.ACCESS, timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )


def create_refresh_token(subject: str) -> str:
    return _create_token(
        subject, TokenType.REFRESH, timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    )


def decode_token(token: str, expected_type: TokenType) -> str:
    """Decodifica un JWT y devuelve el "subject" (id de usuario) si es valido."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError as exc:
        raise InvalidTokenError("Token invalido o expirado") from exc

    if payload.get("type") != expected_type.value:
        raise InvalidTokenError(f"Se esperaba un token de tipo '{expected_type.value}'")

    subject = payload.get("sub")
    if subject is None:
        raise InvalidTokenError("Token sin subject")

    return subject
