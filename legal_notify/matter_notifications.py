from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Protocol

from pydantic import BaseModel, Field


class NoticeKind(str, Enum):
    MATTER_INTAKE = "matter_intake"
    SIGNED_DOCUMENT = "signed_document"
    DEADLINE_FOLLOW_UP = "deadline_follow_up"


class LegalNotice(BaseModel):
    request_id: str = Field(min_length=1)
    account_id: str = Field(min_length=1)
    user_id: str = Field(min_length=1)
    matter_id: str = Field(min_length=1)
    kind: NoticeKind
    document_name: str | None = None
    deadline_at: datetime | None = None


class PublishReceipt(BaseModel):
    channel: str
    event: str
    request_id: str
    result: dict[str, Any]


class Publisher(Protocol):
    def publish(
        self,
        channel: str,
        event: str,
        data: dict[str, Any],
        account_id: str,
        request_id: str,
    ) -> dict[str, Any]:
        raise RuntimeError("publisher protocol method called directly")


def select_event(notice: LegalNotice, now: datetime) -> str:
    if notice.kind == NoticeKind.MATTER_INTAKE:
        return "matter.intake.received"
    if notice.kind == NoticeKind.SIGNED_DOCUMENT:
        return "document.signed.available"
    if notice.deadline_at is None:
        raise ValueError("deadline_at is required for deadline follow-up")
    deadline = notice.deadline_at.astimezone(timezone.utc)
    current = now.astimezone(timezone.utc)
    return "deadline.urgent" if (deadline - current).total_seconds() <= 48 * 3600 else "deadline.reminder"


def publish_notice(notice: LegalNotice, publisher: Publisher, now: datetime) -> PublishReceipt:
    event = select_event(notice, now)
    channel = f"legal-user-{notice.user_id}"
    data: dict[str, Any] = {
        "matter_id": notice.matter_id,
        "kind": notice.kind.value,
    }
    if notice.document_name is not None:
        data["document_name"] = notice.document_name
    if notice.deadline_at is not None:
        data["deadline_at"] = notice.deadline_at.isoformat()
    result = publisher.publish(
        channel=channel,
        event=event,
        data=data,
        account_id=notice.account_id,
        request_id=notice.request_id,
    )
    return PublishReceipt(channel=channel, event=event, request_id=notice.request_id, result=result)
