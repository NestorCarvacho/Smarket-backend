from sqlalchemy.ext.asyncio import AsyncSession

from app.models.purchase import Purchase
from app.repositories.interfaces import IPurchaseRepository


class SqlAlchemyPurchaseRepository(IPurchaseRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, purchase_id: int) -> Purchase | None:
        return await self._session.get(Purchase, purchase_id)

    async def create(
        self,
        list_item_id: int,
        brand: str,
        purchased_name: str,
        price: float,
        quantity_purchased: float,
    ) -> Purchase:
        purchase = Purchase(
            list_item_id=list_item_id,
            brand=brand,
            purchased_name=purchased_name,
            price=price,
            quantity_purchased=quantity_purchased,
        )
        self._session.add(purchase)
        await self._session.flush()
        return purchase

    async def delete(self, purchase: Purchase) -> None:
        await self._session.delete(purchase)
