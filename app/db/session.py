from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.exceptions import DomainError

engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True, future=True)

AsyncSessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency de FastAPI que provee una sesion por request (patron Unit of Work simplificado)."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except DomainError:
            # Persistimos side-effects de dominio (ej. intentos fallidos / bloqueo)
            # aunque la respuesta HTTP sea un error.
            await session.commit()
            raise
        except Exception:
            await session.rollback()
            raise
        else:
            await session.commit()
