from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.list_item import ListItemRead


class ShoppingListCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class ShoppingListRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    created_at: datetime


class ShoppingListDetailRead(ShoppingListRead):
    items: list[ListItemRead] = []
