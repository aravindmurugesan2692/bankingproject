"""Modular conferencing provider interface (Teams / mock / future vendors)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class MeetingResult:
    meeting_id: str
    meeting_url: str
    provider: str
    is_mock: bool
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class InviteResult:
    invited: list[dict[str, Any]]
    is_mock: bool
    raw: dict[str, Any] = field(default_factory=dict)


class ConferencingProvider(Protocol):
    name: str

    async def create_meeting(
        self,
        *,
        title: str,
        bridge_code: str,
        occ_incident_id: str,
        description: str,
    ) -> MeetingResult: ...

    async def invite_responders(
        self,
        *,
        meeting_id: str,
        meeting_url: str,
        responders: list[dict[str, Any]],
    ) -> InviteResult: ...
