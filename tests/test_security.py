from datetime import datetime

from app.core.security import create_access_token, decode_token, hash_password, verify_password


def test_hash_password_produces_non_plaintext():
    plain = "my-secret-password"
    hashed = hash_password(plain)

    assert hashed != plain
    assert isinstance(hashed, str)


def test_verify_password_accepts_valid_pair():
    plain = "correct-horse-battery-staple"
    hashed = hash_password(plain)

    assert verify_password(plain, hashed) is True


def test_verify_password_rejects_invalid_pair():
    hashed = hash_password("actual-password")

    assert verify_password("wrong-password", hashed) is False


def test_create_and_decode_access_token_round_trip():
    token = create_access_token({"sub": "alice@example.com"})
    payload = decode_token(token)

    assert payload is not None
    assert payload["sub"] == "alice@example.com"
    assert "exp" in payload


def test_decode_token_returns_none_for_invalid_token():
    payload = decode_token("not-a-real-token")
    assert payload is None


def test_create_access_token_embeds_future_expiration():
    token = create_access_token({"sub": "timing@example.com"})
    payload = decode_token(token)

    assert payload is not None
    assert payload["exp"] > datetime.utcnow().timestamp()
