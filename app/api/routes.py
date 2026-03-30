from fastapi import APIRouter

from app.services.health_service import HealthService

router = APIRouter()
health_service = HealthService()


@router.get("/")
def health_check() -> dict[str, str]:
    return health_service.get_status()
