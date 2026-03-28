import os
from datetime import UTC, datetime, timedelta
from typing import Final, cast
from uuid import uuid4

import jwt

from app.services.auth.jwt.jwt_payload import JwtPayload


class JwtGenerator:
    def __init__(self) -> None:
        self._secret: Final[str] = os.getenv("JWT_SECRET", "top_reports_dev_secret")
        self._algorithm: Final[str] = "HS256"
        self._expiration_delta: Final[timedelta] = timedelta(hours=24)

    def generate(self, user_id: int, email: str) -> str:
        issued_at = datetime.now(tz=UTC)
        payload: JwtPayload = {
            "sub": str(user_id),
            "email": email,
            "iat": int(issued_at.timestamp()),
            "exp": int((issued_at + self._expiration_delta).timestamp()),
            "jti": str(uuid4()),
        }
        return self._encode(payload)

    def decode(self, token: str) -> JwtPayload:
        raw_payload = self._decode(token)
        if not isinstance(raw_payload, dict):
            raise ValueError("JWT payload must be an object")

        payload = cast(dict[str, object], raw_payload)
        sub = payload.get("sub")
        email = payload.get("email")
        issued_at = payload.get("iat")
        expires_at = payload.get("exp")
        jwt_id = payload.get("jti")
        if not (
            isinstance(sub, str)
            and isinstance(email, str)
            and isinstance(issued_at, int)
            and isinstance(expires_at, int)
            and isinstance(jwt_id, str)
        ):
            raise ValueError("JWT payload has invalid types")

        return {
            "sub": sub,
            "email": email,
            "iat": issued_at,
            "exp": expires_at,
            "jti": jwt_id,
        }

    def _encode(self, payload: JwtPayload) -> str:
        return jwt.encode(payload, self._secret, algorithm=self._algorithm)  # type: ignore[arg-type]  # pyright: ignore[reportUnknownMemberType, reportArgumentType]

    def _decode(self, token: str) -> object:
        return cast(
            object,
            jwt.decode(token, self._secret, algorithms=[self._algorithm]),  # pyright: ignore[reportUnknownMemberType]
        )
