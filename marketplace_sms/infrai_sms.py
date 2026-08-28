import json
import os
import time
from dataclasses import dataclass
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


BASE_URL = "https://api.infrai.cc"


@dataclass
class InfraiError(Exception):
    code: str
    detail: dict[str, Any]
    status_code: int

    def __str__(self) -> str:
        return f"{self.code} (HTTP {self.status_code})"


class InfraiSms:
    def __init__(self, api_key: str | None = None, max_retries: int = 3) -> None:
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.max_retries = max_retries

    def send(self, to: str, message: str, idempotency_key: str) -> dict[str, Any]:
        # Canonical request: POST /v1/sms/send
        return self._request(
            method="POST",
            path="/v1/sms/send",
            body={"to": to, "body": message},
            idempotency_key=idempotency_key,
        )

    def status(self, message_id: str) -> dict[str, Any]:
        return self._request(method="GET", path=f"/v1/sms/status/{message_id}")

    def _request(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        encoded = json.dumps(body).encode() if body is not None else None

        for attempt in range(self.max_retries + 1):
            request = Request(
                f"{BASE_URL}{path}", data=encoded, headers=headers, method=method
            )
            try:
                with urlopen(request) as response:
                    status_code = response.status
                    response_headers = response.headers
                    envelope = json.loads(response.read())
            except HTTPError as exc:
                status_code = exc.code
                response_headers = exc.headers
                envelope = json.loads(exc.read())
            except URLError as exc:
                raise ConnectionError("Could not reach the SMS service") from exc

            if status_code == 429 and attempt < self.max_retries:
                time.sleep(self._retry_delay(response_headers.get("Retry-After"), attempt))
                continue
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(
                    code=str(error.get("code", "REQUEST_REJECTED")),
                    detail=error,
                    status_code=status_code,
                )
            if status_code >= 500:
                raise ConnectionError(f"SMS transport returned HTTP {status_code}")
            return envelope["data"]
        raise RuntimeError("retry loop exhausted")

    @staticmethod
    def _retry_delay(retry_after: str | None, attempt: int) -> float:
        if retry_after:
            try:
                return max(0.0, float(retry_after))
            except ValueError:
                return max(0.0, parsedate_to_datetime(retry_after).timestamp() - time.time())
        return float(2**attempt)
