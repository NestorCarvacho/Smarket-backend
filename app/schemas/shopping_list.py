from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.schemas.list_item import ListItemRead


class ShoppingListItemSeed(BaseModel):
    product_name: str = Field(min_length=1, max_length=120)
    quantity_requested: float = Field(gt=0)
    unit: str | None = Field(default=None, max_length=30)


class ShoppingListCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    items: list[ShoppingListItemSeed] = Field(default_factory=list)


class ShoppingListUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class ShoppingListDuplicate(BaseModel):
    """Copia limpia: productos y cantidades, sin compras ni estados completados."""

    name: str | None = Field(default=None, min_length=1, max_length=120)


class ShoppingListRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    created_at: datetime
    is_owner: bool = True
    item_count: int = 0
    completed_count: int = 0
    total_spent: float = 0.0


class ShoppingListDetailRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    created_at: datetime
    is_owner: bool = True
    share_token: str | None = None
    items: list[ListItemRead] = []

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total_spent(self) -> float:
        return sum(
            float(p.price) * float(p.quantity_purchased)
            for item in self.items
            for p in item.purchases
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def item_count(self) -> int:
        return len(self.items)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def completed_count(self) -> int:
        return sum(1 for item in self.items if str(item.status) == "completed")


class ShareLinkRead(BaseModel):
    share_token: str
    share_url: str


class JoinListRequest(BaseModel):
    share_token: str = Field(min_length=8, max_length=64)


class JoinInvitePreview(BaseModel):
    name: str
    share_token: str
    item_count: int
    deep_link: str
    web_url: str
