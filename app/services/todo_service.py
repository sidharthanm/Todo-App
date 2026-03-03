from sqlalchemy.orm import Session
from app.models.todo import Todo


def create_todo(db: Session, data, user_id):
    payload = data.dict()
    todo = Todo(**payload, user_id=user_id)
    db.add(todo)
    db.commit()
    db.refresh(todo)
    return todo


def get_todos(db: Session, user_id):
    todos = db.query(Todo).filter(Todo.user_id == user_id).order_by(
        Todo.created_at.asc()).all()
    out_by_id = {}
    for todo in todos:
        out_by_id[str(todo.id)] = _to_dict(todo)

    roots = []
    for todo in todos:
        node = out_by_id[str(todo.id)]
        if todo.parent_id:
            parent = out_by_id.get(str(todo.parent_id))
            if parent:
                parent["subtasks"].append(node)
                continue
        roots.append(node)

    return roots


def update_todo(db: Session, todo, data):
    for key, value in data.dict(exclude_unset=True).items():
        setattr(todo, key, value)
    db.commit()
    db.refresh(todo)
    return todo


def delete_todo(db: Session, todo):
    todo.completed = True
    db.commit()
    db.refresh(todo)
    return todo


def _to_dict(todo: Todo):
    return {
        "id": str(todo.id),
        "title": todo.title,
        "description": todo.description,
        "completed": todo.completed,
        "deadline": todo.deadline,
        "created_at": todo.created_at,
        "parent_id": str(todo.parent_id) if todo.parent_id else None,
        "subtasks": [],
    }
