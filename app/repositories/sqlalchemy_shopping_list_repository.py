from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.list_item import ListItem
from app.models.shopping_list import ShoppingList
from app.repositories.interfaces import IShoppingListRepository


class SqlAlchemyShoppingListRepository(IShoppingListRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, list_id: int) -> ShoppingList | None:
        stmt = (
            select(ShoppingList)
            .where(ShoppingList.id == list_id)
            .options(selectinload(ShoppingList.items).selectinload(ListItem.purchases))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: int) -> list[ShoppingList]:
        stmt = (
            select(ShoppingList)
            .where(ShoppingList.user_id == user_id)
            .order_by(ShoppingList.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, user_id: int, name: str) -> ShoppingList:
        shopping_list = ShoppingList(user_id=user_id, name=name)
        self._session.add(shopping_list)
        await self._session.flush()
        return shopping_list

    async def delete(self, shopping_list: ShoppingList) -> None:
        await self._session.delete(shopping_list)
