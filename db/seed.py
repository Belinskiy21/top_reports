import sys
from pathlib import Path
from typing import cast

from pwdlib import PasswordHash
from sqlalchemy import Table

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.db import Base, SessionLocal, engine, ensure_database_exists  # noqa: E402
from app.models.company import CompanyRecord  # noqa: E402
from app.models.download_history import DownloadHistoryRecord  # noqa: E402
from app.models.report_file import ReportFileRecord  # noqa: E402
from app.models.user import UserRecord  # noqa: E402
from app.services.auth.jwt import JwtGenerator  # noqa: E402
from app.services.company import CompanyService  # noqa: E402
from app.services.user import UserService  # noqa: E402

SEEDED_USER_EMAIL = "seeded-user@quartr.dev"
SEEDED_USER_PASSWORD = "seeded-password"
SEEDED_COMPANIES: tuple[tuple[str, str, str], ...] = (
    ("Apple", "0000320193", "AAPL"),
    ("Meta", "0001326801", "META"),
    ("Alphabet", "0001652044", "GOOGL"),
    ("Amazon", "0001018724", "AMZN"),
    ("Netflix", "0001065280", "NFLX"),
    ("Goldman Sachs", "0000886982", "GS"),
)

password_hash = PasswordHash.recommended()
jwt_generator = JwtGenerator()
user_service = UserService()
company_service = CompanyService()


def seed() -> None:
    ensure_database_exists()
    Base.metadata.create_all(
        bind=engine,
        tables=[
            cast(Table, UserRecord.__table__),
            cast(Table, CompanyRecord.__table__),
            cast(Table, ReportFileRecord.__table__),
            cast(Table, DownloadHistoryRecord.__table__),
        ],
    )
    _seed_companies()
    _seed_user()


def _seed_companies() -> None:
    with SessionLocal() as session:
        for name, cik, ticker in SEEDED_COMPANIES:
            _ = company_service.update_or_create(
                session,
                name=name,
                cik=cik,
                ticker=ticker,
            )


def _seed_user() -> None:
    with SessionLocal() as session:
        user = user_service.find_by_email(session, SEEDED_USER_EMAIL)
        if user is None:
            user = user_service.create(
                session,
                email=SEEDED_USER_EMAIL,
                password_hash=password_hash.hash(SEEDED_USER_PASSWORD),
                auth_token="",
            )

        user.auth_token = jwt_generator.generate(user_id=user.id, email=user.email)
        user = user_service.save(session, user)
        print(f"Seeded user email: {user.email}", flush=True)
        print(f"Seeded user password: {SEEDED_USER_PASSWORD}", flush=True)
        print(f"Seeded user token: {user.auth_token}", flush=True)


if __name__ == "__main__":
    seed()
