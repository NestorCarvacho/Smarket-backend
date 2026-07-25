from app.core.exceptions import NotFoundError
from app.models.list_item import ListItem, ListItemStatus
from app.repositories.interfaces import IListItemRepository, IPurchaseRepository
from app.services.list_item_service import ListItemService


class PurchaseService:
    """Registra compras de un item, permitiendo varias marcas por producto.

    Regla de negocio: cuando la suma de `quantity_purchased` de todas las
    Purchase de un item alcanza (o supera) `quantity_requested`, el item pasa
    a estado `completed` y deja de aparecer entre los pendientes.
    """

    def __init__(
        self,
        purchase_repository: IPurchaseRepository,
        item_repository: IListItemRepository,
        list_item_service: ListItemService,
    ) -> None:
        self._purchase_repository = purchase_repository
        self._item_repository = item_repository
        self._list_item_service = list_item_service

    async def register_purchase(
        self,
        list_id: int,
        item_id: int,
        user_id: int,
        brand: str | None,
        purchased_name: str,
        price: float,
        quantity_purchased: float,
    ) -> ListItem:
        item = await self._list_item_service.get_owned_item(list_id, item_id, user_id)

        purchase = await self._purchase_repository.create(
            list_item_id=item.id,
            brand=(brand or "").strip(),
            purchased_name=purchased_name,
            price=price,
            quantity_purchased=quantity_purchased,
        )
        # Sincronizamos la coleccion en memoria: `item.purchases` fue cargada
        # antes de crear esta compra, asi que no la incluye automaticamente.
        item.purchases.append(purchase)

        return await self._recalculate_status(item)

    async def undo_purchase(
        self, list_id: int, item_id: int, purchase_id: int, user_id: int
    ) -> ListItem:
        item = await self._list_item_service.get_owned_item(list_id, item_id, user_id)

        purchase = await self._purchase_repository.get_by_id(purchase_id)
        if purchase is None or purchase.list_item_id != item.id:
            raise NotFoundError("Compra no encontrada para este item")

        await self._purchase_repository.delete(purchase)
        item.purchases.remove(purchase)

        return await self._recalculate_status(item)

    async def _recalculate_status(self, item: ListItem) -> ListItem:
        total_purchased = self._total_purchased(item)
        item.status = (
            ListItemStatus.COMPLETED
            if total_purchased >= float(item.quantity_requested)
            else ListItemStatus.PENDING
        )
        return await self._item_repository.save(item)

    @staticmethod
    def _total_purchased(item: ListItem) -> float:
        return sum(float(p.quantity_purchased) for p in item.purchases)
