import logging
from collections.abc import Sequence
from typing import Annotated, cast

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.v1.current_user import get_current_user
from app.db import get_session
from app.exceptions.sec import SecRequestError
from app.models.user import UserRecord
from app.schema.sec import GetReportRequest
from app.schema.user import AuthenticatedUser, UserSignInRequest, UserSignUpRequest
from app.services.auth import AuthService, InvalidCredentialsError, UserAlreadyExistsError
from app.services.sec import SecReportService
from app.services.validations import RequestValidationService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1")
auth_service = AuthService()
request_validation_service = RequestValidationService()
sec_report_service = SecReportService()


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


@router.post("/get-report-urls", response_model=dict[str, str])
async def get_report_urls(
    payload: GetReportRequest,
    request: Request,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[UserRecord, Depends(get_current_user)],
) -> dict[str, str]:
    validated_report_type = request_validation_service.get_validated_report_type(
        payload.report_type,
        sec_report_service.get_supported_report_types(),
    )
    validated_company_names = request_validation_service.get_validated_company_names(
        session,
        payload.companies,
    )
    try:
        return await sec_report_service.get_recent_report_urls(
            session=session,
            report_type=validated_report_type,
            company_names=cast(Sequence[str], validated_company_names),
            public_base_url=str(request.base_url),
            created_by=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except SecRequestError as exc:
        logger.exception(
            "SEC request failed",
            extra={
                "upstream_status_code": exc.upstream_status_code,
                "upstream_url": exc.upstream_url,
                "upstream_message": exc.upstream_message,
            },
        )
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.detail,
        ) from exc


@router.get("/files/{file_name}", name="download_file")
def download_file(
    file_name: str,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[UserRecord, Depends(get_current_user)],
) -> Response:
    try:
        return sec_report_service.download_file(
            session=session,
            file_name=file_name,
            downloaded_by=current_user.id,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found") from exc
