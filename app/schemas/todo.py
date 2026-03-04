from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID


class TodoCreate(BaseModel):
    title: str
    description: Optional[str] = None
    deadline: Optional[datetime] = None
    parent_id: Optional[UUID] = None
    context_tags: list[str] = Field(default_factory=list)


class TodoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None
    context_tags: Optional[list[str]] = None


class TodoOut(BaseModel):
    id: str
    title: str
    description: Optional[str]
    completed: bool
    deadline: Optional[datetime]
    created_at: Optional[datetime]
    parent_id: Optional[str]
    context_tags: list[str] = Field(default_factory=list)
    subtasks: list["TodoOut"] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


TodoOut.model_rebuild()
