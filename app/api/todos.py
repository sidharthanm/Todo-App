from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.todo import TodoCreate, TodoUpdate
from app.services.todo_service import *
from app.api.deps import get_db, get_current_user
from app.models.todo import Todo

router = APIRouter(prefix="/todos")


@router.post("/")
def create(todo: TodoCreate,
           db: Session = Depends(get_db),
           user=Depends(get_current_user)):
    return create_todo(db, todo, user.id)


@router.get("/")
def list_all(db: Session = Depends(get_db),
             user=Depends(get_current_user)):
    return get_todos(db, user.id)


@router.put("/{todo_id}")
def update(todo_id: str,
           data: TodoUpdate,
           db: Session = Depends(get_db),
           user=Depends(get_current_user)):
    todo = db.query(Todo).filter(Todo.id == todo_id,
                                 Todo.user_id == user.id).first()
    if not todo:
        raise HTTPException(status_code=404)
    return update_todo(db, todo, data)


@router.delete("/{todo_id}")
def delete(todo_id: str,
           db: Session = Depends(get_db),
           user=Depends(get_current_user)):
    todo = db.query(Todo).filter(Todo.id == todo_id,
                                 Todo.user_id == user.id).first()
    if not todo:
        raise HTTPException(status_code=404)
    delete_todo(db, todo)
    return {"deleted": True}
