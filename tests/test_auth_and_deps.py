from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.api import auth, deps


def test_register_delegates_to_create_user(monkeypatch):
    db = MagicMock()
    schema = MagicMock(email="new@example.com", password="pw123")
    expected = {"id": "abc"}

    create_user_mock = MagicMock(return_value=expected)
    monkeypatch.setattr(auth, "create_user", create_user_mock)

    result = auth.register(schema, db=db)

    assert result == expected
    create_user_mock.assert_called_once_with(db, "new@example.com", "pw123")


def test_login_returns_access_token_on_success(monkeypatch):
    db = MagicMock()
    login_schema = MagicMock(email="alice@example.com", password="pw")
    db_user = MagicMock(email="alice@example.com", hashed_password="hashed")
    db.query.return_value.filter.return_value.first.return_value = db_user

    monkeypatch.setattr(auth, "verify_password", lambda plain, hashed: True)
    monkeypatch.setattr(auth, "create_access_token", lambda data: "token-123")

    result = auth.login(login_schema, db=db)

    assert result == {"access_token": "token-123"}


def test_login_raises_401_if_user_missing():
    db = MagicMock()
    login_schema = MagicMock(email="missing@example.com", password="pw")
    db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as exc:
        auth.login(login_schema, db=db)

    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid credentials"


def test_login_raises_401_if_password_invalid(monkeypatch):
    db = MagicMock()
    login_schema = MagicMock(email="alice@example.com", password="wrong")
    db_user = MagicMock(email="alice@example.com", hashed_password="hashed")
    db.query.return_value.filter.return_value.first.return_value = db_user
    monkeypatch.setattr(auth, "verify_password", lambda plain, hashed: False)

    with pytest.raises(HTTPException) as exc:
        auth.login(login_schema, db=db)

    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid credentials"


def test_get_db_yields_session_and_closes(monkeypatch):
    closed = {"value": False}

    class FakeSession:
        def close(self):
            closed["value"] = True

    monkeypatch.setattr(deps, "SessionLocal", lambda: FakeSession())

    gen = deps.get_db()
    session = next(gen)
    assert session is not None

    with pytest.raises(StopIteration):
        next(gen)

    assert closed["value"] is True


def test_get_current_user_raises_401_for_invalid_token(monkeypatch):
    db = MagicMock()
    monkeypatch.setattr(deps, "decode_token", lambda token: None)

    with pytest.raises(HTTPException) as exc:
        deps.get_current_user(token="bad-token", db=db)

    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid token"


def test_get_current_user_returns_user_when_token_valid(monkeypatch):
    db = MagicMock()
    expected_user = MagicMock(email="alice@example.com")
    db.query.return_value.filter.return_value.first.return_value = expected_user
    monkeypatch.setattr(deps, "decode_token", lambda token: {"sub": "alice@example.com"})

    result = deps.get_current_user(token="good-token", db=db)

    assert result == expected_user
