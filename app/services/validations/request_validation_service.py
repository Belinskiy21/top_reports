from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.services.company import CompanyService


class RequestValidationService:
    def __init__(self) -> None:
        self._company_service: CompanyService = CompanyService()

    def get_validated_report_type(
        self,
        report_type: str,
        supported_report_types: list[str],
    ) -> str:
        if report_type not in supported_report_types:
            detail = (
                f"Invalid value of report type. Supported report types: {supported_report_types}"
            )
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=detail,
            )
        return report_type

    def get_validated_company_names(
        self,
        session: Session,
        company_names: list[str],
    ) -> list[str]:
        valid_company_names = self._company_service.find_all_names(session)
        normalized_company_names = self.normalize_company_names(company_names)
        if not normalized_company_names:
            raise self._invalid_company_names_error(valid_company_names)

        has_invalid_company_name = any(
            not company_name or company_name not in valid_company_names
            for company_name in normalized_company_names
        )
        if has_invalid_company_name:
            raise self._invalid_company_names_error(valid_company_names)

        return normalized_company_names

    def normalize_company_names(self, company_names: list[str]) -> list[str]:
        normalized_company_names = [company_name.strip() for company_name in company_names]
        return list(dict.fromkeys(normalized_company_names))

    def _invalid_company_names_error(
        self,
        valid_company_names: list[str],
    ) -> HTTPException:
        detail = f"Invalid value of company name. Supported companies names: {valid_company_names}"
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
        )
