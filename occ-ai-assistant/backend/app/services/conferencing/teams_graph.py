"""Microsoft Graph Teams online meeting provider (live path)."""

from __future__ import annotations

from typing import Any

import httpx

from app.config import Settings
from app.services.conferencing.base import InviteResult, MeetingResult
from app.services.conferencing.mock_provider import MockConferencingProvider


class TeamsGraphProvider:
    name = "microsoft_graph"

    def __init__(self, settings: Settings):
        self.settings = settings
        self._fallback = MockConferencingProvider()

    async def _token(self) -> str | None:
        tenant = self.settings.microsoft_tenant_id.strip()
        client_id = self.settings.microsoft_client_id.strip()
        client_secret = self.settings.microsoft_client_secret.strip()
        if not (tenant and client_id and client_secret):
            return None
        url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
        data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": "https://graph.microsoft.com/.default",
            "grant_type": "client_credentials",
        }
        async with httpx.AsyncClient(
            timeout=self.settings.microsoft_graph_timeout_seconds
        ) as client:
            response = await client.post(url, data=data)
            response.raise_for_status()
            return response.json().get("access_token")

    async def create_meeting(
        self,
        *,
        title: str,
        bridge_code: str,
        occ_incident_id: str,
        description: str,
    ) -> MeetingResult:
        # App-only Graph onlineMeetings typically need an application-hosted user
        # context. Without a configured organizer UPN we fall back to MOCK rather
        # than inventing a broken live call.
        token = await self._token()
        if not token:
            result = await self._fallback.create_meeting(
                title=title,
                bridge_code=bridge_code,
                occ_incident_id=occ_incident_id,
                description=description,
            )
            result.raw["fallback_reason"] = "missing_graph_token"
            return result

        base = self.settings.microsoft_graph_base_url.rstrip("/")
        body = {
            "subject": f"[{bridge_code}] {occ_incident_id}: {title}",
            "lobbyBypassSettings": {"scope": "everyone", "isDialInBypassEnabled": True},
        }
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        try:
            async with httpx.AsyncClient(
                timeout=self.settings.microsoft_graph_timeout_seconds
            ) as client:
                # Requires OnlineMeetings.ReadWrite.All + a user path in many tenants;
                # if the call fails, fall back to mock so OCC workflow is not blocked.
                response = await client.post(
                    f"{base}/me/onlineMeetings",
                    headers=headers,
                    json=body,
                )
                if response.status_code >= 400:
                    result = await self._fallback.create_meeting(
                        title=title,
                        bridge_code=bridge_code,
                        occ_incident_id=occ_incident_id,
                        description=description,
                    )
                    result.raw["fallback_reason"] = "graph_create_failed"
                    result.raw["graph_status"] = response.status_code
                    result.raw["graph_body"] = response.text[:500]
                    return result
                data = response.json()
                return MeetingResult(
                    meeting_id=str(data.get("id") or data.get("joinWebUrl") or ""),
                    meeting_url=str(data.get("joinWebUrl") or ""),
                    provider=self.name,
                    is_mock=False,
                    raw=data,
                )
        except httpx.HTTPError as exc:
            result = await self._fallback.create_meeting(
                title=title,
                bridge_code=bridge_code,
                occ_incident_id=occ_incident_id,
                description=description,
            )
            result.raw["fallback_reason"] = "graph_http_error"
            result.raw["error"] = str(exc)
            return result

    async def invite_responders(
        self,
        *,
        meeting_id: str,
        meeting_url: str,
        responders: list[dict[str, Any]],
    ) -> InviteResult:
        # Calendar attendee invites need a mailbox; keep modular and mock-safe.
        return await self._fallback.invite_responders(
            meeting_id=meeting_id,
            meeting_url=meeting_url,
            responders=responders,
        )
