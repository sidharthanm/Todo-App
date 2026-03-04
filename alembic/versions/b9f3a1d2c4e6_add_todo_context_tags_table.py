"""add todo context tags table

Revision ID: b9f3a1d2c4e6
Revises: 25cff2077e84
Create Date: 2026-03-05 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "b9f3a1d2c4e6"
down_revision: Union[str, Sequence[str], None] = "25cff2077e84"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "todo_context_tags",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("todo_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tag", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["todo_id"], ["todos.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("todo_id", "tag", name="uq_todo_context_tags_todo_id_tag"),
    )
    op.create_index("ix_todo_context_tags_user_id", "todo_context_tags", ["user_id"], unique=False)
    op.create_index("ix_todo_context_tags_tag", "todo_context_tags", ["tag"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_todo_context_tags_tag", table_name="todo_context_tags")
    op.drop_index("ix_todo_context_tags_user_id", table_name="todo_context_tags")
    op.drop_table("todo_context_tags")
