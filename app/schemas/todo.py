from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TodoCreate(BaseModel):
    title: str
    description: Optional[str] = None
    deadline: Optional[datetime] = None


class TodoUpdate(BaseModel):
    title: Optional[str]
    description: Optional[str]
    completed: Optional[bool]


class TodoOut(BaseModel):
    id: str
    title: str
    description: Optional[str]
    completed: bool

    class Config:
        orm_mode = True
