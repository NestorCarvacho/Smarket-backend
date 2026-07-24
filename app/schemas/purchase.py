from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PurchaseCreate(BaseModel):
    brand: str = Field(min_length=1, max_length=120)
    purchased_name: str = Field(min_length=1, max_length=120)
    price: float = Field(gt=0)
    quantity_purchased: float = Field(gt=0)


class PurchaseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    list_item_id: int
    brand: str
    purchased_name: str
    price: float
    quantity_purchased: float
    purchased_at: datetime
