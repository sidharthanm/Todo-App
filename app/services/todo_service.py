from sqlalchemy.orm import Session
from app.models.todo import Todo


def create_todo(db: Session, data, user_id):
    todo = Todo(**data.dict(), user_id=user_id)
    db.add(todo)
    db.commit()
    db.refresh(todo)
    return todo


def get_todos(db: Session, user_id):
    return db.query(Todo).filter(Todo.user_id == user_id).all()


def update_todo(db: Session, todo, data):
    for key, value in data.dict(exclude_unset=True).items():
        setattr(todo, key, value)
    db.commit()
    db.refresh(todo)
    return todo


def delete_todo(db: Session, todo):
    db.delete(todo)
    db.commit()
