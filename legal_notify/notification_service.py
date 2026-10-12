from __future__ import annotations

from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException

from .infrai_realtime import InfraiError, InfraiRealtime
from .matter_notifications import LegalNotice, PublishReceipt, publish_notice

app = FastAPI(title="Legal realtime notification service")


def realtime_client() -> InfraiRealtime:
    client = InfraiRealtime()
    try:
        yield client
    finally:
        client.close()


@app.post("/notifications", response_model=PublishReceipt)
def send_notification(
    notice: LegalNotice,
    realtime: InfraiRealtime = Depends(realtime_client),
) -> PublishReceipt:
    try:
        return publish_notice(notice, realtime, datetime.now(timezone.utc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except InfraiError as exc:
        status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(status_code=status, detail={"code": exc.code, "message": str(exc)}) from exc

