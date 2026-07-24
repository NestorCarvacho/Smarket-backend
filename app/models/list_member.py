from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ListMember(Base):
    """Colaborador de una lista compartida (no incluye al owner, que vive en ShoppingList.user_id)."""

    __tablename__ = "list_members"
    __table_args__ = (UniqueConstraint("list_id", "user_id", name="uq_list_member"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    list_id: Mapped[int] = mapped_column(ForeignKey("shopping_lists.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    shopping_list: Mapped["ShoppingList"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship(back_populates="memberships")
