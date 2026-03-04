from sqlalchemy.orm import Session
from sqlalchemy.orm import selectinload

from app.models.context_tag import TodoContextTag
from app.models.todo import Todo


def create_todo(db: Session, data, user_id):
    payload = data.model_dump(exclude={"context_tags"})
    todo = Todo(**payload, user_id=user_id)
    tags = _normalize_context_tags(data.context_tags)
    db.add(todo)
    db.flush()
    if tags:
        db.add_all(
            [
                TodoContextTag(todo_id=todo.id, user_id=user_id, tag=tag)
                for tag in tags
            ]
        )
    db.commit()
    db.refresh(todo)
    return todo


def get_todos(db: Session, user_id):
    todos = (
        db.query(Todo)
        .options(selectinload(Todo.context_tags))
        .filter(Todo.user_id == user_id)
        .order_by(Todo.created_at.asc())
        .all()
    )
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
    update_fields = data.model_dump(exclude_unset=True, exclude={"context_tags"})
    for key, value in update_fields.items():
        setattr(todo, key, value)

    if "context_tags" in data.model_fields_set:
        tags = _normalize_context_tags(data.context_tags or [])
        todo.context_tags.clear()
        for tag in tags:
            todo.context_tags.append(TodoContextTag(todo_id=todo.id, user_id=todo.user_id, tag=tag))

    db.commit()
    db.refresh(todo)
    return todo


def delete_todo(db: Session, todo):
    todo.completed = True
    db.commit()
    db.refresh(todo)
    return todo


def clear_finished_parent_todos(db: Session, user_id):
    finished_roots = db.query(Todo).filter(
        Todo.user_id == user_id,
        Todo.completed.is_(True),
        Todo.parent_id.is_(None),
    ).all()

    cleared = len(finished_roots)
    for todo in finished_roots:
        db.delete(todo)

    db.commit()
    return cleared


def _to_dict(todo: Todo):
    return {
        "id": str(todo.id),
        "title": todo.title,
        "description": todo.description,
        "completed": todo.completed,
        "deadline": todo.deadline,
        "created_at": todo.created_at,
        "parent_id": str(todo.parent_id) if todo.parent_id else None,
        "context_tags": [item.tag for item in todo.context_tags],
        "subtasks": [],
    }


def _normalize_context_tags(tags):
    if not tags:
        return []

    normalized = []
    seen = set()
    for raw in tags:
        tag = str(raw).strip()
        if not tag:
            continue
        key = tag.lower()
        if key in seen:
            continue
        seen.add(key)
        normalized.append(tag[:64])
    return normalized
