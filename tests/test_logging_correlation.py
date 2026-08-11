"""R1 — Logging & PII: correlation ID, response header va log enrichment."""

from __future__ import annotations

import json
import re
from pathlib import Path

from fastapi.testclient import TestClient

from app import logging_config
from app.main import app
from app.middleware import normalize_correlation_id

CORRELATION_ID_FORMAT = re.compile(r"^req-[0-9a-f]{8}$")

CHAT_PAYLOAD = {
    "user_id": "student-01",
    "session_id": "session-01",
    "feature": "qa",
    "message": "Explain observability",
}


def _read_events(log_path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in log_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_response_exposes_correlation_id_and_processing_time(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(logging_config, "LOG_PATH", tmp_path / "logs.jsonl")

    with TestClient(app) as client:
        response = client.post("/chat", json=CHAT_PAYLOAD)

    assert response.status_code == 200
    assert CORRELATION_ID_FORMAT.match(response.headers["x-request-id"])
    assert response.headers["x-request-id"] == response.json()["correlation_id"]
    assert float(response.headers["x-response-time-ms"]) >= 0


def test_correlation_id_is_unique_per_request(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(logging_config, "LOG_PATH", tmp_path / "logs.jsonl")

    with TestClient(app) as client:
        first = client.post("/chat", json=CHAT_PAYLOAD).headers["x-request-id"]
        second = client.post("/chat", json=CHAT_PAYLOAD).headers["x-request-id"]

    assert first != second


def test_incoming_correlation_id_is_reused_for_end_to_end_tracing(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(logging_config, "LOG_PATH", tmp_path / "logs.jsonl")

    with TestClient(app) as client:
        response = client.post(
            "/chat", json=CHAT_PAYLOAD, headers={"x-request-id": "req-1a2b3c4d"}
        )

    assert response.headers["x-request-id"] == "req-1a2b3c4d"


def test_malformed_incoming_correlation_id_is_replaced() -> None:
    for malformed in ("", "   ", "not-an-id", "req-XYZ", "req-1a2b3c4d5e", "<script>"):
        generated = normalize_correlation_id(malformed)
        assert generated != malformed
        assert CORRELATION_ID_FORMAT.match(generated)


def test_api_logs_carry_enrichment_and_correlation_id(monkeypatch, tmp_path: Path) -> None:
    log_path = tmp_path / "logs.jsonl"
    monkeypatch.setattr(logging_config, "LOG_PATH", log_path)

    with TestClient(app) as client:
        response = client.post("/chat", json=CHAT_PAYLOAD)

    api_events = [event for event in _read_events(log_path) if event.get("service") == "api"]
    assert {event["event"] for event in api_events} == {"request_received", "response_sent"}

    for event in api_events:
        assert event["correlation_id"] == response.headers["x-request-id"]
        for field in ("ts", "level", "user_id_hash", "session_id", "feature", "model", "env"):
            assert field in event, f"{event['event']} thieu truong {field}"


def test_raw_user_id_never_reaches_the_log(monkeypatch, tmp_path: Path) -> None:
    log_path = tmp_path / "logs.jsonl"
    monkeypatch.setattr(logging_config, "LOG_PATH", log_path)

    with TestClient(app) as client:
        client.post("/chat", json={**CHAT_PAYLOAD, "user_id": "student@vinuni.edu.vn"})

    raw_log = log_path.read_text(encoding="utf-8")
    assert "student@vinuni.edu.vn" not in raw_log
    api_events = [event for event in _read_events(log_path) if event.get("service") == "api"]
    assert all(len(event["user_id_hash"]) == 12 for event in api_events)
