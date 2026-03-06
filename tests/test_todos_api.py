import uuid
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.api import todos
from app.schemas.todo import TodoCreate, TodoUpdate


def test_create_rejects_missing_parent(user):
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    payload = TodoCreate(title="Child", parent_id=uuid.uuid4())

    with pytest.raises(HTTPException) as exc:
        todos.create(payload, db=db, user=user)

    assert exc.value.status_code == 404
    assert exc.value.detail == "Parent task not found"


def test_create_calls_service_when_parent_exists(monkeypatch, user):
    db = MagicMock()
    parent = MagicMock(id=uuid.uuid4(), user_id=user.id)
    db.query.return_value.filter.return_value.first.return_value = parent
    payload = TodoCreate(title="Child", parent_id=parent.id, context_tags=["work"])

    create_mock = MagicMock(return_value={"ok": True})
    monkeypatch.setattr(todos, "create_todo", create_mock)

    result = todos.create(payload, db=db, user=user)

    assert result == {"ok": True}
    create_mock.assert_called_once_with(db, payload, user.id)


def test_create_calls_service_for_root_todo(monkeypatch, user):
    db = MagicMock()
    payload = TodoCreate(title="Root")
    create_mock = MagicMock(return_value={"id": "1"})
    monkeypatch.setattr(todos, "create_todo", create_mock)

    result = todos.create(payload, db=db, user=user)

    assert result == {"id": "1"}
    create_mock.assert_called_once_with(db, payload, user.id)
    assert db.query.call_count == 0


def test_list_all_uses_service(monkeypatch, user):
    db = MagicMock()
    get_mock = MagicMock(return_value=[{"id": "1"}])
    monkeypatch.setattr(todos, "get_todos", get_mock)

    result = todos.list_all(db=db, user=user)

    assert result == [{"id": "1"}]
    get_mock.assert_called_once_with(db, user.id)


def test_clear_finished_parents_returns_count(monkeypatch, user):
    db = MagicMock()
    clear_mock = MagicMock(return_value=3)
    monkeypatch.setattr(todos, "clear_finished_parent_todos", clear_mock)

    result = todos.clear_finished_parents(db=db, user=user)

    assert result == {"cleared": 3}
    clear_mock.assert_called_once_with(db, user.id)


def test_update_raises_404_when_not_found(user):
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as exc:
        todos.update("missing", TodoUpdate(title="x"), db=db, user=user)

    assert exc.value.status_code == 404


def test_update_delegates_to_service(monkeypatch, user):
    db = MagicMock()
    todo = MagicMock(id=uuid.uuid4(), user_id=user.id)
    db.query.return_value.filter.return_value.first.return_value = todo
    update_mock = MagicMock(return_value={"id": str(todo.id), "title": "updated"})
    monkeypatch.setattr(todos, "update_todo", update_mock)
    payload = TodoUpdate(title="updated")

    result = todos.update(str(todo.id), payload, db=db, user=user)

    assert result == {"id": str(todo.id), "title": "updated"}
    update_mock.assert_called_once_with(db, todo, payload)


def test_delete_raises_404_when_not_found(user):
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as exc:
        todos.delete("missing", db=db, user=user)

    assert exc.value.status_code == 404


def test_delete_returns_finished_payload(monkeypatch, user):
    db = MagicMock()
    todo = MagicMock(id=uuid.uuid4(), user_id=user.id)
    updated = MagicMock(id=todo.id, completed=True)
    db.query.return_value.filter.return_value.first.return_value = todo
    delete_mock = MagicMock(return_value=updated)
    monkeypatch.setattr(todos, "delete_todo", delete_mock)

    result = todos.delete(str(todo.id), db=db, user=user)

    assert result == {"finished": True, "id": str(todo.id), "completed": True}
    delete_mock.assert_called_once_with(db, todo)
