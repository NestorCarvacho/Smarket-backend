"""add share_token and list_members

Revision ID: b2c4d6e8f0a1
Revises: 849aec39be73
Create Date: 2026-07-24 14:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b2c4d6e8f0a1"
down_revision: Union[str, None] = "849aec39be73"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("shopping_lists", sa.Column("share_token", sa.String(length=64), nullable=True))
    op.create_index(op.f("ix_shopping_lists_share_token"), "shopping_lists", ["share_token"], unique=True)

    op.create_table(
        "list_members",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("list_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("joined_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["list_id"], ["shopping_lists.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("list_id", "user_id", name="uq_list_member"),
    )
    op.create_index(op.f("ix_list_members_list_id"), "list_members", ["list_id"], unique=False)
    op.create_index(op.f("ix_list_members_user_id"), "list_members", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_list_members_user_id"), table_name="list_members")
    op.drop_index(op.f("ix_list_members_list_id"), table_name="list_members")
    op.drop_table("list_members")
    op.drop_index(op.f("ix_shopping_lists_share_token"), table_name="shopping_lists")
    op.drop_column("shopping_lists", "share_token")
