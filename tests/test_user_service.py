from types import SimpleNamespace
from unittest.mock import MagicMock

from app.services import user_service


def test_create_user_hashes_password_and_persists(monkeypatch):
    db = MagicMock()
    monkeypatch.setattr(user_service, "hash_password", lambda password: "hashed::" + password)

    def refresh_side_effect(user):
        user.id = "user-1"

    db.refresh.side_effect = refresh_side_effect

    user = user_service.create_user(db, "alice@example.com", "pw123")

    assert user.email == "alice@example.com"
    assert user.hashed_password == "hashed::pw123"
    assert user.id == "user-1"
    db.add.assert_called_once_with(user)
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(user)


def test_create_user_returns_model_instance(monkeypatch):
    db = MagicMock()
    monkeypatch.setattr(user_service, "hash_password", lambda password: "hash")

    user = user_service.create_user(db, "bob@example.com", "pw")

    assert hasattr(user, "email")
    assert user.email == "bob@example.com"
    assert user.hashed_password == "hash"
