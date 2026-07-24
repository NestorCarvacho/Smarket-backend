from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.list_item import ListItem
from app.repositories.interfaces import IListItemRepository
from app.services.shopping_list_service import ShoppingListService


class ListItemService:
    """Casos de uso de items de una lista (producto + cantidad)."""

    def __init__(
        self, item_repository: IListItemRepository, shopping_list_service: ShoppingListService
    ) -> None:
        self._item_repository = item_repository
        self._shopping_list_service = shopping_list_service

    async def add_item(
        self,
        list_id: int,
        user_id: int,
        product_name: str,
        quantity_requested: float,
        unit: str | None,
    ) -> ListItem:
        await self._shopping_list_service.get_owned_list(list_id, user_id)
        return await self._item_repository.create(list_id, product_name, quantity_requested, unit)

    async def list_items(self, list_id: int, user_id: int) -> list[ListItem]:
        await self._shopping_list_service.get_owned_list(list_id, user_id)
        return await self._item_repository.list_by_list_id(list_id)

    async def get_owned_item(self, list_id: int, item_id: int, user_id: int) -> ListItem:
        await self._shopping_list_service.get_owned_list(list_id, user_id)
        item = await self._item_repository.get_by_id(item_id)
        if item is None or item.list_id != list_id:
            raise NotFoundError("Item no encontrado en esta lista")
        return item

    async def update_item(
        self,
        list_id: int,
        item_id: int,
        user_id: int,
        product_name: str | None,
        quantity_requested: float | None,
        unit: str | None,
    ) -> ListItem:
        item = await self.get_owned_item(list_id, item_id, user_id)

        if product_name is not None:
            item.product_name = product_name
        if quantity_requested is not None:
            item.quantity_requested = quantity_requested
        if unit is not None:
            item.unit = unit

        return await self._item_repository.save(item)

    async def delete_item(self, list_id: int, item_id: int, user_id: int) -> None:
        item = await self.get_owned_item(list_id, item_id, user_id)
        await self._item_repository.delete(item)
