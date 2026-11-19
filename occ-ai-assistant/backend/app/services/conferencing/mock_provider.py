"""MOCK conferencing provider — no Microsoft Graph calls."""

from __future__ import annotations

import hashlib
from typing import Any

from app.services.conferencing.base import InviteResult, MeetingResult


class MockConferencingProvider:
    name = "mock"

    async def create_meeting(
        self,
        *,
        title: str,
        bridge_code: str,
        occ_incident_id: str,
        description: str,
    ) -> MeetingResult:
        digest = hashlib.sha1(
            f"{occ_incident_id}:{bridge_code}:{title}".encode()
        ).hexdigest()[:10].upper()
        meeting_id = f"MOCK-MTG-{bridge_code}-{digest}"
        meeting_url = (
            f"https://teams.microsoft.com/l/meetup-join/mock/{meeting_id}"
        )
        return MeetingResult(
            meeting_id=meeting_id,
            meeting_url=meeting_url,
            provider=self.name,
            is_mock=True,
            raw={
                "mock": True,
                "title": title,
                "bridge_code": bridge_code,
                "occ_incident_id": occ_incident_id,
                "description": description[:500],
            },
        )

    async def invite_responders(
        self,
        *,
        meeting_id: str,
        meeting_url: str,
        responders: list[dict[str, Any]],
    ) -> InviteResult:
        invited = []
        for row in responders:
            invited.append(
                {
                    **row,
                    "invite_status": "mock_sent",
                    "meeting_id": meeting_id,
                }
            )
        return InviteResult(
            invited=invited,
            is_mock=True,
            raw={"mock": True, "meeting_url": meeting_url, "count": len(invited)},
        )
