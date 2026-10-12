from datetime import datetime, timezone
from typing import Any

from legal_notify.matter_notifications import LegalNotice, publish_notice


class RecordingPublisher:
    def __init__(self) -> None:
        self.call: dict[str, Any] = {}

    def publish(self, **kwargs: Any) -> dict[str, Any]:
        self.call = kwargs
        return {"message_id": "msg-41"}


def test_deadline_inside_48_hours_is_published_as_urgent() -> None:
    publisher = RecordingPublisher()
    notice = LegalNotice(
        request_id="req-41",
        account_id="firm-8",
        user_id="lawyer-17",
        matter_id="matter-203",
        kind="deadline_follow_up",
        deadline_at="2026-09-07T09:00:00Z",
    )

    receipt = publish_notice(
        notice,
        publisher,
        now=datetime(2026, 9, 5, 10, 0, tzinfo=timezone.utc),
    )

    assert receipt.event == "deadline.urgent"
    assert publisher.call == {
        "channel": "legal-user-lawyer-17",
        "event": "deadline.urgent",
        "data": {
            "matter_id": "matter-203",
            "kind": "deadline_follow_up",
            "deadline_at": "2026-09-07T09:00:00+00:00",
        },
        "account_id": "firm-8",
        "request_id": "req-41",
    }

