"""add parent_id to todos

Revision ID: 8f2a9d1c4b7e
Revises: 37cb293586fc
Create Date: 2026-03-03 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "8f2a9d1c4b7e"
down_revision: Union[str, Sequence[str], None] = "37cb293586fc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("todos", sa.Column("parent_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_todos_parent_id_todos",
        "todos",
        "todos",
        ["parent_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("fk_todos_parent_id_todos", "todos", type_="foreignkey")
    op.drop_column("todos", "parent_id")
