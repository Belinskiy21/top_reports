from app.services.health_service import HealthService


def test_get_status_returns_ok() -> None:
    service = HealthService()

    assert service.get_status() == {"status": "ok"}
