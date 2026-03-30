from sqlalchemy.orm import Session

from app.services.company import CompanyService


def test_create_and_find_by_name(db_session: Session) -> None:
    service = CompanyService()

    company = service.create(
        db_session,
        name="Apple",
        cik="0000320193",
        ticker="AAPL",
    )
    found_company = service.find_by_name(db_session, "Apple")

    assert company.id > 0
    assert found_company is not None
    assert found_company.cik == "0000320193"
    assert found_company.ticker == "AAPL"
