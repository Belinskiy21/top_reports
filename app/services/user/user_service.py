from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.exceptions.auth import UserAlreadyExistsError
from app.models.user import UserRecord


class UserService:
    def find_first(self, session: Session) -> UserRecord | None:
        return session.scalar(select(UserRecord).order_by(UserRecord.id))

    def find_by_email(self, session: Session, email: str) -> UserRecord | None:
        return session.scalar(select(UserRecord).where(UserRecord.email == email))

    def create(
        self,
        session: Session,
        *,
        email: str,
        password_hash: str,
        auth_token: str,
    ) -> UserRecord:
        existing_user = self.find_by_email(session, email)
        if existing_user is not None:
            raise UserAlreadyExistsError

        user = UserRecord(
            email=email,
            password_hash=password_hash,
            auth_token=auth_token,
        )
        session.add(user)
        try:
            session.flush()
        except IntegrityError as exc:
            session.rollback()
            raise UserAlreadyExistsError from exc
        return user

    def save(self, session: Session, user: UserRecord) -> UserRecord:
        session.commit()
        session.refresh(user)
        return user
