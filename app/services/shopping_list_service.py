import secrets

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.list_item import ListItemStatus
from app.models.shopping_list import ShoppingList
from app.repositories.interfaces import IListItemRepository, IShoppingListRepository
from app.schemas.shopping_list import ShoppingListItemSeed, ShoppingListRead


def compute_list_summary(shopping_list: ShoppingList, user_id: int) -> ShoppingListRead:
    items = shopping_list.items or []
    total_spent = sum(
        float(p.price) * float(p.quantity_purchased) for item in items for p in (item.purchases or [])
    )
    completed_count = sum(1 for item in items if item.status == ListItemStatus.COMPLETED)
    return ShoppingListRead(
        id=shopping_list.id,
        name=shopping_list.name,
        created_at=shopping_list.created_at,
        is_owner=shopping_list.user_id == user_id,
        item_count=len(items),
        completed_count=completed_count,
        total_spent=round(total_spent, 2),
    )


class ShoppingListService:
    def __init__(
        self, list_repository: IShoppingListRepository, item_repository: IListItemRepository
    ) -> None:
        self._list_repository = list_repository
        self._item_repository = item_repository

    async def create_list(
        self, user_id: int, name: str, items: list[ShoppingListItemSeed] | None = None
    ) -> ShoppingList:
        shopping_list = await self._list_repository.create(user_id, name)
        for seed in items or []:
            await self._item_repository.create(
                shopping_list.id,
                seed.product_name,
                seed.quantity_requested,
                seed.unit,
            )
        return await self.get_accessible_list(shopping_list.id, user_id)

    async def rename_list(self, list_id: int, user_id: int, name: str) -> ShoppingList:
        shopping_list = await self.require_owner(list_id, user_id)
        shopping_list.name = name
        await self._list_repository.save(shopping_list)
        return await self.get_accessible_list(list_id, user_id)

    async def duplicate_list(
        self, list_id: int, user_id: int, name: str | None = None
    ) -> ShoppingList:
        """Crea una lista nueva del usuario con los mismos productos, sin compras."""
        source = await self.get_accessible_list(list_id, user_id)
        new_name = (name or f"{source.name} (copia)").strip()
        new_list = await self._list_repository.create(user_id, new_name)
        for item in source.items or []:
            await self._item_repository.create(
                new_list.id,
                item.product_name,
                float(item.quantity_requested),
                item.unit,
            )
        return await self.get_accessible_list(new_list.id, user_id)

    async def list_for_user(self, user_id: int) -> list[ShoppingListRead]:
        lists = await self._list_repository.list_accessible_by_user(user_id)
        return [compute_list_summary(shopping_list, user_id) for shopping_list in lists]

    async def get_accessible_list(self, list_id: int, user_id: int) -> ShoppingList:
        shopping_list = await self._list_repository.get_by_id(list_id)
        if shopping_list is None:
            raise NotFoundError("Lista no encontrada")
        if not await self._user_can_access(shopping_list, user_id):
            raise ForbiddenError("No tenes acceso a esta lista")
        return shopping_list

    async def get_owned_list(self, list_id: int, user_id: int) -> ShoppingList:
        """Compatibilidad: acceso de colaborador o owner (antes solo owner)."""
        return await self.get_accessible_list(list_id, user_id)

    async def require_owner(self, list_id: int, user_id: int) -> ShoppingList:
        shopping_list = await self._list_repository.get_by_id(list_id)
        if shopping_list is None:
            raise NotFoundError("Lista no encontrada")
        if shopping_list.user_id != user_id:
            raise ForbiddenError("Solo el dueño puede realizar esta accion")
        return shopping_list

    async def delete_list(self, list_id: int, user_id: int) -> None:
        shopping_list = await self.require_owner(list_id, user_id)
        await self._list_repository.delete(shopping_list)

    async def create_share_link(self, list_id: int, user_id: int) -> tuple[str, str]:
        shopping_list = await self.require_owner(list_id, user_id)
        if not shopping_list.share_token:
            shopping_list.share_token = secrets.token_urlsafe(16)
            await self._list_repository.save(shopping_list)
        from app.core.config import settings

        share_url = f"{settings.PUBLIC_BASE_URL.rstrip('/')}/join/{shopping_list.share_token}"
        return shopping_list.share_token, share_url

    async def revoke_share_link(self, list_id: int, user_id: int) -> None:
        shopping_list = await self.require_owner(list_id, user_id)
        shopping_list.share_token = None
        await self._list_repository.save(shopping_list)

    async def join_by_token(self, share_token: str, user_id: int) -> ShoppingList:
        shopping_list = await self._list_repository.get_by_share_token(share_token.strip())
        if shopping_list is None:
            raise NotFoundError("Link de invitacion invalido o expirado")
        if shopping_list.user_id == user_id:
            raise ConflictError("Ya sos el dueño de esta lista")
        if await self._list_repository.is_member(shopping_list.id, user_id):
            return shopping_list
        await self._list_repository.add_member(shopping_list.id, user_id)
        return await self.get_accessible_list(shopping_list.id, user_id)

    async def leave_list(self, list_id: int, user_id: int) -> None:
        shopping_list = await self._list_repository.get_by_id(list_id)
        if shopping_list is None:
            raise NotFoundError("Lista no encontrada")
        if shopping_list.user_id == user_id:
            raise ConflictError("El dueño no puede abandonar la lista; eliminala en su lugar")
        if not await self._list_repository.is_member(list_id, user_id):
            raise ForbiddenError("No sos miembro de esta lista")
        await self._list_repository.remove_member(list_id, user_id)

    async def get_invite_preview(self, share_token: str) -> ShoppingList:
        shopping_list = await self._list_repository.get_by_share_token(share_token.strip())
        if shopping_list is None:
            raise NotFoundError("Link de invitacion invalido o expirado")
        return shopping_list

    async def _user_can_access(self, shopping_list: ShoppingList, user_id: int) -> bool:
        if shopping_list.user_id == user_id:
            return True
        return await self._list_repository.is_member(shopping_list.id, user_id)
