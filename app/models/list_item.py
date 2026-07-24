import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ListItemStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"


class ListItem(Base):
    """Un producto+cantidad dentro de una lista (ej. 'Leche', 4 unidades)."""

    __tablename__ = "list_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    list_id: Mapped[int] = mapped_column(
        ForeignKey("shopping_lists.id", ondelete="CASCADE"), index=True
    )
    product_name: Mapped[str] = mapped_column(String(120), nullable=False)
    quantity_requested: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    unit: Mapped[str | None] = mapped_column(String(30), nullable=True)
    status: Mapped[ListItemStatus] = mapped_column(
        Enum(ListItemStatus), default=ListItemStatus.PENDING, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    shopping_list: Mapped["ShoppingList"] = relationship(back_populates="items")
    purchases: Mapped[list["Purchase"]] = relationship(
        back_populates="list_item", cascade="all, delete-orphan"
    )
