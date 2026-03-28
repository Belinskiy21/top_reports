from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from sqlalchemy.orm import Session

from app.db import get_session
from app.models.user import UserRecord
from app.services.auth.jwt import JwtGenerator

bearer_scheme = HTTPBearer()
jwt_generator = JwtGenerator()


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    session: Annotated[Session, Depends(get_session)],
) -> UserRecord:
    token = credentials.credentials

    try:
        payload = jwt_generator.decode(token)
    except (InvalidTokenError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc

    user_id = payload["sub"]
    if not user_id.isdigit():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user = session.get(UserRecord, int(user_id))
    if user is None or user.auth_token != token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    return user
