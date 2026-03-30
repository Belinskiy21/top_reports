from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from app.exceptions.auth import InvalidCredentialsError, UserAlreadyExistsError
from app.schema.user import AuthenticatedUser, UserSignInRequest, UserSignUpRequest
from app.services.auth.jwt import JwtGenerator
from app.services.user import UserService

password_hash = PasswordHash.recommended()
jwt_generator = JwtGenerator()
user_service = UserService()


class AuthService:
    def sign_up(self, session: Session, payload: UserSignUpRequest) -> AuthenticatedUser:
        existing_user = user_service.find_by_email(session, payload.email)
        if existing_user is not None:
            raise UserAlreadyExistsError

        user = user_service.create(
            session,
            email=payload.email,
            password_hash=password_hash.hash(payload.password),
            auth_token="",
        )
        user.auth_token = jwt_generator.generate(user_id=user.id, email=user.email)
        user = user_service.save(session, user)
        return AuthenticatedUser(id=user.id, email=user.email, token=user.auth_token)

    def sign_in(self, session: Session, payload: UserSignInRequest) -> AuthenticatedUser:
        user = user_service.find_by_email(session, payload.email)
        if user is None:
            raise InvalidCredentialsError

        if not password_hash.verify(payload.password, user.password_hash):
            raise InvalidCredentialsError

        user.auth_token = jwt_generator.generate(user_id=user.id, email=user.email)
        user = user_service.save(session, user)
        return AuthenticatedUser(id=user.id, email=user.email, token=user.auth_token)
