from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_session
from app.schema.user import AuthenticatedUser, UserSignInRequest, UserSignUpRequest
from app.services.auth import AuthService, InvalidCredentialsError, UserAlreadyExistsError

router = APIRouter(prefix="/api/v1")
auth_service = AuthService()


@router.post("/sign-up", response_model=AuthenticatedUser, status_code=status.HTTP_201_CREATED)
def sign_up(
    payload: UserSignUpRequest,
    session: Annotated[Session, Depends(get_session)],
) -> AuthenticatedUser:
    try:
        user = auth_service.sign_up(session, payload)
    except UserAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists",
        ) from exc

    return user


@router.post("/sign-in", response_model=AuthenticatedUser)
def sign_in(
    payload: UserSignInRequest,
    session: Annotated[Session, Depends(get_session)],
) -> AuthenticatedUser:
    try:
        user = auth_service.sign_in(session, payload)
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        ) from exc

    return user
