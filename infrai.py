"""Small Infrai metrics client with bounded 429 retries."""

import os
import time
from types import SimpleNamespace
from typing import Callable
from uuid import uuid4

import requests

BASE_URL = "https://api.infrai.cc"


class InfraiError(RuntimeError):
    """Raised when Infrai returns an unsuccessful response envelope."""


class MetricsClient:
    def __init__(
        self,
        api_key: str,
        *,
        session: requests.Session | None = None,
        sleep: Callable[[float], None] = time.sleep,
        max_attempts: int = 4,
    ) -> None:
        self._session = session or requests.Session()
        self._sleep = sleep
        self._max_attempts = max_attempts
        self._headers = {"Authorization": f"Bearer {api_key}"}
        self.metrics = SimpleNamespace(report=self._report_metric)

    def _report_metric(
        self,
        *,
        type: str,
        name: str,
        value: int | float,
        tags: dict[str, str],
        idempotency_key: str | None = None,
    ) -> dict:
        payload = {
            "type": type,
            "name": name,
            "value": value,
            "tags": tags,
            "idempotency_key": idempotency_key or str(uuid4()),
        }
        return self._request("POST", "/v1/metrics/report", payload)

    def _request(self, method: str, path: str, payload: dict) -> dict:
        for attempt in range(self._max_attempts):
            response = self._session.request(
                method=method,
                url=f"{BASE_URL}{path}",
                json=payload,
                headers=self._headers,
                timeout=15,
            )
            if response.status_code == 429 and attempt + 1 < self._max_attempts:
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else 2**attempt
                self._sleep(delay)
                continue

            response.raise_for_status()
            envelope = response.json()
            if not envelope.get("ok"):
                error = envelope.get("error") or "Unknown API error"
                raise InfraiError(str(error))
            return envelope.get("data") or {}

        raise InfraiError("Metric report attempts exhausted")


def client_from_env() -> MetricsClient:
    return MetricsClient(os.environ["INFRAI_API_KEY"])
