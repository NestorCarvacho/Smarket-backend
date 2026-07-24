from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.list_item import ListItem
from app.models.list_member import ListMember
from app.models.shopping_list import ShoppingList
from app.repositories.interfaces import IShoppingListRepository


class SqlAlchemyShoppingListRepository(IShoppingListRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _detail_options(self):
        return (
            selectinload(ShoppingList.items).selectinload(ListItem.purchases),
            selectinload(ShoppingList.members),
        )

    async def get_by_id(self, list_id: int) -> ShoppingList | None:
        stmt = select(ShoppingList).where(ShoppingList.id == list_id).options(*self._detail_options())
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_share_token(self, share_token: str) -> ShoppingList | None:
        stmt = (
            select(ShoppingList)
            .where(ShoppingList.share_token == share_token)
            .options(*self._detail_options())
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_accessible_by_user(self, user_id: int) -> list[ShoppingList]:
        member_list_ids = select(ListMember.list_id).where(ListMember.user_id == user_id)
        stmt = (
            select(ShoppingList)
            .where(or_(ShoppingList.user_id == user_id, ShoppingList.id.in_(member_list_ids)))
            .options(*self._detail_options())
            .order_by(ShoppingList.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().unique().all())

    async def create(self, user_id: int, name: str) -> ShoppingList:
        shopping_list = ShoppingList(user_id=user_id, name=name)
        self._session.add(shopping_list)
        await self._session.flush()
        await self._session.refresh(shopping_list, attribute_names=["items", "members"])
        return shopping_list

    async def save(self, shopping_list: ShoppingList) -> ShoppingList:
        self._session.add(shopping_list)
        await self._session.flush()
        return shopping_list

    async def delete(self, shopping_list: ShoppingList) -> None:
        await self._session.delete(shopping_list)

    async def add_member(self, list_id: int, user_id: int) -> ListMember:
        member = ListMember(list_id=list_id, user_id=user_id)
        self._session.add(member)
        await self._session.flush()
        return member

    async def remove_member(self, list_id: int, user_id: int) -> None:
        stmt = select(ListMember).where(ListMember.list_id == list_id, ListMember.user_id == user_id)
        result = await self._session.execute(stmt)
        member = result.scalar_one_or_none()
        if member is not None:
            await self._session.delete(member)

    async def is_member(self, list_id: int, user_id: int) -> bool:
        stmt = select(ListMember.id).where(ListMember.list_id == list_id, ListMember.user_id == user_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None
