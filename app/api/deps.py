"""Proveedores de dependencias de FastAPI.

Aca se resuelve la inyeccion de dependencias: se construyen los
repositorios concretos (SQLAlchemy) y se inyectan en los services, que solo
conocen las interfaces. Cambiar de implementacion de persistencia solo
requiere tocar este archivo.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import InvalidTokenError, TokenType, decode_token
from app.db.session import get_db_session
from app.models.user import User
from app.repositories.sqlalchemy_list_item_repository import SqlAlchemyListItemRepository
from app.repositories.sqlalchemy_purchase_repository import SqlAlchemyPurchaseRepository
from app.repositories.sqlalchemy_shopping_list_repository import SqlAlchemyShoppingListRepository
from app.repositories.sqlalchemy_user_repository import SqlAlchemyUserRepository
from app.services.auth_service import AuthService
from app.services.list_item_service import ListItemService
from app.services.purchase_service import PurchaseService
from app.services.shopping_list_service import ShoppingListService

_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

DbSession = Annotated[AsyncSession, Depends(get_db_session)]


def get_auth_service(session: DbSession) -> AuthService:
    return AuthService(SqlAlchemyUserRepository(session))


def get_shopping_list_service(session: DbSession) -> ShoppingListService:
    return ShoppingListService(SqlAlchemyShoppingListRepository(session))


def get_list_item_service(
    session: DbSession,
    shopping_list_service: Annotated[ShoppingListService, Depends(get_shopping_list_service)],
) -> ListItemService:
    return ListItemService(SqlAlchemyListItemRepository(session), shopping_list_service)


def get_purchase_service(
    session: DbSession,
    list_item_service: Annotated[ListItemService, Depends(get_list_item_service)],
) -> PurchaseService:
    return PurchaseService(
        SqlAlchemyPurchaseRepository(session),
        SqlAlchemyListItemRepository(session),
        list_item_service,
    )


async def get_current_user(
    token: Annotated[str, Depends(_oauth2_scheme)],
    session: DbSession,
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        user_id = decode_token(token, TokenType.ACCESS)
    except InvalidTokenError as exc:
        raise credentials_exception from exc

    user = await SqlAlchemyUserRepository(session).get_by_id(int(user_id))
    if user is None:
        raise credentials_exception
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
