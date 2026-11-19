from fastapi import APIRouter

from app.config import get_settings
from app.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        app=settings.app_name,
        mock_mode=settings.mock_mode,
        llm_configured=bool(settings.openai_api_key.strip()),
        servicenow_configured=settings.servicenow_configured,
        pagerduty_configured=settings.pagerduty_configured,
    )
