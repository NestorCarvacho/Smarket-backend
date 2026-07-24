"""Interfaces (puertos) de repositorio.

Los services dependen unicamente de estas abstracciones (Dependency
Inversion Principle). Las implementaciones concretas viven en los modulos
`sqlalchemy_*_repository.py` y podrian reemplazarse (por otra base de datos,
un mock en tests, etc.) sin tocar la logica de negocio.
"""

from abc import ABC, abstractmethod

from app.models.list_item import ListItem
from app.models.list_member import ListMember
from app.models.purchase import Purchase
from app.models.shopping_list import ShoppingList
from app.models.user import User


class IUserRepository(ABC):
    @abstractmethod
    async def get_by_id(self, user_id: int) -> User | None: ...

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None: ...

    @abstractmethod
    async def create(self, email: str, hashed_password: str) -> User: ...

    @abstractmethod
    async def save(self, user: User) -> User: ...


class IShoppingListRepository(ABC):
    @abstractmethod
    async def get_by_id(self, list_id: int) -> ShoppingList | None: ...

    @abstractmethod
    async def get_by_share_token(self, share_token: str) -> ShoppingList | None: ...

    @abstractmethod
    async def list_accessible_by_user(self, user_id: int) -> list[ShoppingList]: ...

    @abstractmethod
    async def create(self, user_id: int, name: str) -> ShoppingList: ...

    @abstractmethod
    async def save(self, shopping_list: ShoppingList) -> ShoppingList: ...

    @abstractmethod
    async def delete(self, shopping_list: ShoppingList) -> None: ...

    @abstractmethod
    async def add_member(self, list_id: int, user_id: int) -> ListMember: ...

    @abstractmethod
    async def remove_member(self, list_id: int, user_id: int) -> None: ...

    @abstractmethod
    async def is_member(self, list_id: int, user_id: int) -> bool: ...


class IListItemRepository(ABC):
    @abstractmethod
    async def get_by_id(self, item_id: int) -> ListItem | None: ...

    @abstractmethod
    async def list_by_list_id(self, list_id: int) -> list[ListItem]: ...

    @abstractmethod
    async def create(
        self, list_id: int, product_name: str, quantity_requested: float, unit: str | None
    ) -> ListItem: ...

    @abstractmethod
    async def save(self, item: ListItem) -> ListItem: ...

    @abstractmethod
    async def delete(self, item: ListItem) -> None: ...


class IPurchaseRepository(ABC):
    @abstractmethod
    async def get_by_id(self, purchase_id: int) -> Purchase | None: ...

    @abstractmethod
    async def create(
        self,
        list_item_id: int,
        brand: str,
        purchased_name: str,
        price: float,
        quantity_purchased: float,
    ) -> Purchase: ...

    @abstractmethod
    async def delete(self, purchase: Purchase) -> None: ...
