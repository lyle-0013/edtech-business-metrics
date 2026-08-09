"""Focused client contract tests; no network access."""

import unittest

from infrai import InfraiError, MetricsClient
from learning_metrics import report_lesson_completed


class FakeResponse:
    def __init__(self, status_code: int, body: dict, headers: dict | None = None) -> None:
        self.status_code = status_code
        self._body = body
        self.headers = headers or {}

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self) -> dict:
        return self._body


class FakeSession:
    def __init__(self, responses: list[FakeResponse]) -> None:
        self.responses = responses
        self.calls: list[dict] = []

    def request(self, **kwargs) -> FakeResponse:
        self.calls.append(kwargs)
        return self.responses.pop(0)


class MetricsClientTest(unittest.TestCase):
    def test_completion_retries_429_with_same_event_key(self) -> None:
        session = FakeSession(
            [
                FakeResponse(429, {}, {"Retry-After": "3"}),
                FakeResponse(200, {"ok": True, "data": {"accepted": True}}),
            ]
        )
        sleeps: list[float] = []
        client = MetricsClient("test-key", session=session, sleep=sleeps.append)

        result = report_lesson_completed(
            client, course="python-basics", plan="starter", event_id="lesson-event-17"
        )

        self.assertEqual(result, {"accepted": True})
        self.assertEqual(sleeps, [3.0])
        self.assertEqual(session.calls[0]["method"], "POST")
        self.assertEqual(
            session.calls[0]["json"]["idempotency_key"],
            session.calls[1]["json"]["idempotency_key"],
        )
        self.assertEqual(
            session.calls[0]["headers"]["Authorization"], "Bearer test-key"
        )

    def test_unsuccessful_envelope_surfaces_error(self) -> None:
        session = FakeSession(
            [FakeResponse(200, {"ok": False, "error": {"message": "invalid metric"}})]
        )
        client = MetricsClient("test-key", session=session)

        with self.assertRaisesRegex(InfraiError, "invalid metric"):
            report_lesson_completed(
                client, course="python-basics", plan="starter", event_id="event-18"
            )


if __name__ == "__main__":
    unittest.main()
