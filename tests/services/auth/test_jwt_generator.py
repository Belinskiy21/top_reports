import pytest

from app.services.auth.jwt import JwtGenerator


def test_generate_and_decode_round_trip(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET", "test-secret")
    generator = JwtGenerator()

    token = generator.generate(user_id=7, email="user@example.com")
    payload = generator.decode(token)

    assert token.strip() != ""
    assert payload["sub"] == "7"
    assert payload["email"] == "user@example.com"
    assert payload["exp"] > payload["iat"]
    assert payload["jti"].strip() != ""


def test_decode_raises_for_invalid_payload_types(monkeypatch: pytest.MonkeyPatch) -> None:
    generator = JwtGenerator()

    def decode_stub(_: str) -> object:
        return {
            "sub": 7,
            "email": "user@example.com",
            "iat": 1,
            "exp": 2,
            "jti": "token-id",
        }

    monkeypatch.setattr(generator, "_decode", decode_stub)

    with pytest.raises(ValueError, match="invalid types"):
        _ = generator.decode("invalid-token")
