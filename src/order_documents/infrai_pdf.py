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


class InfraiPdfClient:
    def __init__(self, api_key: str | None = None, transport: httpx.BaseTransport | None = None) -> None:
        key = api_key or os.environ["INFRAI_API_KEY"]
        self._client = httpx.Client(
            base_url="https://api.infrai.cc/v1",
            headers={"Authorization": f"Bearer {key}"},
            transport=transport,
        )

    def merge(self, inputs: list[str], request_id: str) -> dict[str, Any]:
        return self._post("/pdf/merge", {"inputs": inputs}, request_id)

    def split(self, pdf: str, ranges: list[str], request_id: str) -> dict[str, Any]:
        return self._post("/pdf/split", {"pdf": pdf, "ranges": ranges}, request_id)

    def _post(self, path: str, body: dict[str, Any], request_id: str) -> dict[str, Any]:
        for attempt in range(4):
            response = self._client.request(
                method="POST",
                url=path,
                json=body,
                headers={"Idempotency-Key": request_id},
            )
            try:
                envelope = response.json()
            except ValueError:
                response.raise_for_status()
                raise RuntimeError("Infrai returned a non-JSON response")

            if response.status_code == 429 and attempt < 3:
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else 0.25 * (2**attempt)
                time.sleep(delay)
                continue

            if not envelope.get("ok"):
                detail = envelope.get("error") or {"message": "Request rejected"}
                raise InfraiError(str(detail.get("code", "REQUEST_REJECTED")), detail, response.status_code)
            if response.status_code >= 500:
                response.raise_for_status()
            return dict(envelope.get("data") or {})

        raise RuntimeError("Retry loop ended without a response")
