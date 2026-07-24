from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    failed_login_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_locked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    reset_code_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reset_code_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    shopping_lists: Mapped[list["ShoppingList"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )
    memberships: Mapped[list["ListMember"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
