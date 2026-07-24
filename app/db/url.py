"""Normalizacion de URLs de base de datos para SQLAlchemy async/sync."""


def to_async_database_url(url: str) -> str:
    """Convierte postgres://... a postgresql+asyncpg://..."""
    normalized = url.strip()
    if normalized.startswith("postgres://"):
        normalized = "postgresql://" + normalized[len("postgres://") :]
    if normalized.startswith("postgresql://") and "+asyncpg" not in normalized:
        normalized = "postgresql+asyncpg://" + normalized[len("postgresql://") :]
    return normalized


def to_sync_database_url(url: str) -> str:
    """Convierte postgres:// / postgresql+asyncpg:// a postgresql+psycopg://."""
    normalized = url.strip()
    if normalized.startswith("postgres://"):
        normalized = "postgresql://" + normalized[len("postgres://") :]
    if "+asyncpg://" in normalized:
        normalized = normalized.replace("+asyncpg://", "://", 1)
    if normalized.startswith("postgresql://") and "+psycopg" not in normalized:
        normalized = "postgresql+psycopg://" + normalized[len("postgresql://") :]
    return normalized
