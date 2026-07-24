from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.models.list_item import ListItemStatus
from app.schemas.purchase import PurchaseRead


class ListItemCreate(BaseModel):
    product_name: str = Field(min_length=1, max_length=120)
    quantity_requested: float = Field(gt=0)
    unit: str | None = Field(default=None, max_length=30)


class ListItemUpdate(BaseModel):
    product_name: str | None = Field(default=None, min_length=1, max_length=120)
    quantity_requested: float | None = Field(default=None, gt=0)
    unit: str | None = Field(default=None, max_length=30)


class ListItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    list_id: int
    product_name: str
    quantity_requested: float
    unit: str | None
    status: ListItemStatus
    purchases: list[PurchaseRead] = []

    @computed_field  # type: ignore[prop-decorator]
    @property
    def quantity_purchased(self) -> float:
        return sum(p.quantity_purchased for p in self.purchases)
