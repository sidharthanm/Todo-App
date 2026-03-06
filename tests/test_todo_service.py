import uuid
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.schemas.todo import TodoCreate, TodoUpdate
from app.services import todo_service


def test_normalize_context_tags_handles_empty_inputs():
    assert todo_service._normalize_context_tags(None) == []
    assert todo_service._normalize_context_tags([]) == []


def test_normalize_context_tags_trims_deduplicates_and_preserves_order():
    tags = ["  Work ", "work", "", "Personal", "personal", "  errands  "]

    normalized = todo_service._normalize_context_tags(tags)

    assert normalized == ["Work", "Personal", "errands"]


def test_normalize_context_tags_truncates_long_values():
    long_tag = "x" * 80

    normalized = todo_service._normalize_context_tags([long_tag])

    assert normalized == ["x" * 64]


def test_to_dict_serializes_expected_fields():
    todo = SimpleNamespace(
        id=uuid.uuid4(),
        title="One",
        description="Desc",
        completed=False,
        deadline=None,
        created_at=datetime.utcnow(),
        parent_id=None,
        context_tags=[SimpleNamespace(tag="work"), SimpleNamespace(tag="home")],
    )

    out = todo_service._to_dict(todo)

    assert out["id"] == str(todo.id)
    assert out["title"] == "One"
    assert out["context_tags"] == ["work", "home"]
    assert out["subtasks"] == []


def test_get_todos_builds_parent_child_tree():
    user_id = uuid.uuid4()
    parent_id = uuid.uuid4()
    child_id = uuid.uuid4()
    parent = SimpleNamespace(
        id=parent_id,
        title="Parent",
        description=None,
        completed=False,
        deadline=None,
        created_at=datetime.utcnow(),
        parent_id=None,
        context_tags=[],
    )
    child = SimpleNamespace(
        id=child_id,
        title="Child",
        description=None,
        completed=False,
        deadline=None,
        created_at=datetime.utcnow(),
        parent_id=parent_id,
        context_tags=[],
    )
    db = MagicMock()
    db.query.return_value.options.return_value.filter.return_value.order_by.return_value.all.return_value = [
        parent,
        child,
    ]

    result = todo_service.get_todos(db, user_id)

    assert len(result) == 1
    assert result[0]["id"] == str(parent_id)
    assert len(result[0]["subtasks"]) == 1
    assert result[0]["subtasks"][0]["id"] == str(child_id)


def test_create_todo_adds_todo_and_normalized_tags():
    user_id = uuid.uuid4()
    payload = TodoCreate(title="Task", context_tags=["  Work ", "work", "Home"])
    db = MagicMock()

    def flush_side_effect():
        created_todo = db.add.call_args_list[0].args[0]
        created_todo.id = uuid.uuid4()

    db.flush.side_effect = flush_side_effect

    todo = todo_service.create_todo(db, payload, user_id)

    assert todo.title == "Task"
    assert todo.user_id == user_id
    assert db.add.call_count >= 1
    db.flush.assert_called_once()
    db.add_all.assert_called_once()
    added_tags = db.add_all.call_args.args[0]
    assert [item.tag for item in added_tags] == ["Work", "Home"]
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(todo)


def test_update_todo_updates_scalar_fields_without_touching_tags():
    todo = SimpleNamespace(
        title="Old",
        description="old-desc",
        completed=False,
        context_tags=[SimpleNamespace(tag="existing")],
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
    )
    data = TodoUpdate(title="New", completed=True)
    db = MagicMock()

    updated = todo_service.update_todo(db, todo, data)

    assert updated.title == "New"
    assert updated.completed is True
    assert [item.tag for item in updated.context_tags] == ["existing"]
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(todo)


def test_update_todo_replaces_tags_when_context_tags_present():
    todo = SimpleNamespace(
        title="Task",
        description=None,
        completed=False,
        context_tags=[SimpleNamespace(tag="old")],
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
    )
    data = TodoUpdate(context_tags=["  Work ", "work", "Home"])
    db = MagicMock()

    updated = todo_service.update_todo(db, todo, data)

    assert [item.tag for item in updated.context_tags] == ["Work", "Home"]
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(todo)


def test_delete_todo_marks_completed_and_persists():
    todo = SimpleNamespace(completed=False)
    db = MagicMock()

    result = todo_service.delete_todo(db, todo)

    assert result.completed is True
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(todo)


def test_clear_finished_parent_todos_deletes_only_finished_roots():
    user_id = uuid.uuid4()
    finished_roots = [SimpleNamespace(id=uuid.uuid4()), SimpleNamespace(id=uuid.uuid4())]
    db = MagicMock()
    db.query.return_value.filter.return_value.all.return_value = finished_roots

    cleared = todo_service.clear_finished_parent_todos(db, user_id)

    assert cleared == 2
    assert db.delete.call_count == 2
    db.commit.assert_called_once()
