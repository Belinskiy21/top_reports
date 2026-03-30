from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.company import CompanyRecord


class CompanyService:
    def find_all(self, session: Session) -> list[CompanyRecord]:
        return list(session.scalars(select(CompanyRecord).order_by(CompanyRecord.name)).all())

    def find_by_name(self, session: Session, company_name: str) -> CompanyRecord | None:
        return session.scalar(select(CompanyRecord).where(CompanyRecord.name == company_name))

    def create(
        self,
        session: Session,
        *,
        name: str,
        cik: str,
        ticker: str,
    ) -> CompanyRecord:
        company = CompanyRecord(name=name, cik=cik, ticker=ticker)
        session.add(company)
        session.commit()
        session.refresh(company)
        return company

    def update_or_create(
        self,
        session: Session,
        *,
        name: str,
        cik: str,
        ticker: str,
    ) -> CompanyRecord:
        existing_company = self.find_by_name(session, name)
        if existing_company is None:
            return self.create(session, name=name, cik=cik, ticker=ticker)

        existing_company.cik = cik
        existing_company.ticker = ticker
        session.commit()
        session.refresh(existing_company)
        return existing_company
