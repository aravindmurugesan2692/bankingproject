"""Conferencing providers — pick mock or Microsoft Graph from settings."""

from app.config import Settings, get_settings
from app.services.conferencing.base import ConferencingProvider
from app.services.conferencing.mock_provider import MockConferencingProvider
from app.services.conferencing.teams_graph import TeamsGraphProvider


def get_conferencing_provider(
    settings: Settings | None = None,
) -> ConferencingProvider:
    settings = settings or get_settings()
    if settings.use_live_teams:
        return TeamsGraphProvider(settings)
    return MockConferencingProvider()


__all__ = [
    "ConferencingProvider",
    "MockConferencingProvider",
    "TeamsGraphProvider",
    "get_conferencing_provider",
]
