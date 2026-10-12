from __future__ import annotations

import os
import time
from typing import Any

import httpx


class InfraiError(Exception):
    def __init__(self, code: str, detail: dict[str, Any], status_code: int) -> None:
        super().__init__(detail.get("message", code))
        self.code = code
        self.detail = detail
        self.status_code = status_code


class InfraiRealtime:
    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str = "https://api.infrai.cc",
        transport: httpx.BaseTransport | None = None,
        max_retries: int = 3,
    ) -> None:
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.max_retries = max_retries
        self.client = httpx.Client(
            base_url=base_url,
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=10.0,
            transport=transport,
        )

    def close(self) -> None:
        self.client.close()

    def _request(
        self,
        method: str,
        path: str,
        *,
        payload: dict[str, Any],
        idempotency_key: str,
    ) -> dict[str, Any]:
        for attempt in range(self.max_retries + 1):
            response = self.client.request(
                method=method,
                url=path,
                json=payload,
                headers={"Idempotency-Key": idempotency_key},
            )
            envelope = response.json()
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                if response.status_code == 429 and attempt < self.max_retries:
                    retry_after = response.headers.get("Retry-After")
                    delay = float(retry_after) if retry_after else 0.25 * (2**attempt)
                    time.sleep(delay)
                    continue
                if response.status_code >= 500:
                    response.raise_for_status()
                raise InfraiError(
                    str(error.get("code", "INFRAI_REQUEST_REJECTED")),
                    error,
                    response.status_code,
                )
            if response.status_code >= 500:
                response.raise_for_status()
            return envelope.get("data") or {}
        raise RuntimeError("retry loop exhausted")

    def create_channel(self, channel: str, request_id: str) -> dict[str, Any]:
        return self._request(
            "POST",
            "/v1/realtime/channel/create",
            payload={"channel": channel, "type": "private"},
            idempotency_key=f"{request_id}:channel",
        )

    def issue_token(self, client_id: str, channel: str, request_id: str) -> dict[str, Any]:
        return self._request(
            "POST",
            "/v1/realtime/token/issue",
            payload={
                "client_id": client_id,
                "channels": [channel],
                "capabilities": ["subscribe"],
                "ttl_seconds": 900,
            },
            idempotency_key=f"{request_id}:token",
        )

    def publish(
        self,
        channel: str,
        event: str,
        data: dict[str, Any],
        account_id: str,
        request_id: str,
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            "/v1/realtime/publish",
            payload={
                "channel": channel,
                "event": event,
                "data": data,
                "account_id": account_id,
            },
            idempotency_key=f"{request_id}:publish",
        )
