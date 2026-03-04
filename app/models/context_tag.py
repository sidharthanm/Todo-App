from datetime import datetime
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class TodoContextTag(Base):
    __tablename__ = "todo_context_tags"
    __table_args__ = (UniqueConstraint("todo_id", "tag", name="uq_todo_context_tags_todo_id_tag"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    todo_id = Column(UUID(as_uuid=True), ForeignKey("todos.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    tag = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    todo = relationship("Todo", back_populates="context_tags")
