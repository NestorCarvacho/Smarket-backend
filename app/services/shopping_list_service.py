from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.shopping_list import ShoppingList
from app.repositories.interfaces import IShoppingListRepository


class ShoppingListService:
    def __init__(self, list_repository: IShoppingListRepository) -> None:
        self._list_repository = list_repository

    async def create_list(self, user_id: int, name: str) -> ShoppingList:
        return await self._list_repository.create(user_id, name)

    async def list_for_user(self, user_id: int) -> list[ShoppingList]:
        return await self._list_repository.list_by_user(user_id)

    async def get_owned_list(self, list_id: int, user_id: int) -> ShoppingList:
        shopping_list = await self._list_repository.get_by_id(list_id)
        if shopping_list is None:
            raise NotFoundError("Lista no encontrada")
        if shopping_list.user_id != user_id:
            raise ForbiddenError("No tenes acceso a esta lista")
        return shopping_list

    async def delete_list(self, list_id: int, user_id: int) -> None:
        shopping_list = await self.get_owned_list(list_id, user_id)
        await self._list_repository.delete(shopping_list)
