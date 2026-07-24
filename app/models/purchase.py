from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Purchase(Base):
    """Registro de una compra real de un item, para una marca especifica.

    Un mismo ListItem puede tener varias Purchase (ej. 2 de Marca A y 2 de
    Marca B) para cubrir la cantidad solicitada.
    """

    __tablename__ = "purchases"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    list_item_id: Mapped[int] = mapped_column(
        ForeignKey("list_items.id", ondelete="CASCADE"), index=True
    )
    brand: Mapped[str] = mapped_column(String(120), nullable=False)
    purchased_name: Mapped[str] = mapped_column(String(120), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    quantity_purchased: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    purchased_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    list_item: Mapped["ListItem"] = relationship(back_populates="purchases")
