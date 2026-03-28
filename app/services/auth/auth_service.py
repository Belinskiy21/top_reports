from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions.auth import InvalidCredentialsError, UserAlreadyExistsError
from app.models.user import UserRecord
from app.schema.user import AuthenticatedUser, UserSignInRequest, UserSignUpRequest
from app.services.auth.jwt import JwtGenerator

password_hash = PasswordHash.recommended()
jwt_generator = JwtGenerator()


class AuthService:
    def sign_up(self, session: Session, payload: UserSignUpRequest) -> AuthenticatedUser:
        existing_user = session.scalar(select(UserRecord).where(UserRecord.email == payload.email))
        if existing_user is not None:
            raise UserAlreadyExistsError

        user = UserRecord(
            email=payload.email,
            password_hash=password_hash.hash(payload.password),
            auth_token="",
        )
        session.add(user)
        session.flush()
        user.auth_token = jwt_generator.generate(user_id=user.id, email=user.email)
        session.commit()
        session.refresh(user)
        return AuthenticatedUser(id=user.id, email=user.email, token=user.auth_token)

    def sign_in(self, session: Session, payload: UserSignInRequest) -> AuthenticatedUser:
        user = session.scalar(select(UserRecord).where(UserRecord.email == payload.email))
        if user is None:
            raise InvalidCredentialsError

        if not password_hash.verify(payload.password, user.password_hash):
            raise InvalidCredentialsError

        user.auth_token = jwt_generator.generate(user_id=user.id, email=user.email)
        session.commit()
        session.refresh(user)
        return AuthenticatedUser(id=user.id, email=user.email, token=user.auth_token)
