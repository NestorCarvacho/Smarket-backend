from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.list_item import ListItem
from app.repositories.interfaces import IListItemRepository


class SqlAlchemyListItemRepository(IListItemRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, item_id: int) -> ListItem | None:
        stmt = (
            select(ListItem)
            .where(ListItem.id == item_id)
            .options(selectinload(ListItem.purchases))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_list_id(self, list_id: int) -> list[ListItem]:
        stmt = (
            select(ListItem)
            .where(ListItem.list_id == list_id)
            .options(selectinload(ListItem.purchases))
            .order_by(ListItem.created_at.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def create(
        self, list_id: int, product_name: str, quantity_requested: float, unit: str | None
    ) -> ListItem:
        item = ListItem(
            list_id=list_id,
            product_name=product_name,
            quantity_requested=quantity_requested,
            unit=unit,
        )
        self._session.add(item)
        await self._session.flush()
        # Aseguramos que la relacion "purchases" quede cargada en memoria
        # (un item recien creado no tiene compras, pero sin este refresh
        # SQLAlchemy intentaria un lazy-load sincrono al serializarlo).
        await self._session.refresh(item, attribute_names=["purchases"])
        return item

    async def save(self, item: ListItem) -> ListItem:
        self._session.add(item)
        await self._session.flush()
        return item

    async def delete(self, item: ListItem) -> None:
        await self._session.delete(item)
