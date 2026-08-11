"""R1 — Logging & PII: pattern PII bo sung va processor scrub_event."""

from __future__ import annotations

from app.logging_config import scrub_event
from app.pii import scrub_text


def test_scrub_vietnamese_passport() -> None:
    out = scrub_text("Ho chieu cua toi la B1234567")
    assert "B1234567" not in out
    assert "REDACTED_PASSPORT" in out


def test_scrub_vietnamese_address() -> None:
    address = "Số nhà 25 Đường Nguyễn Trãi, Phường Bến Thành, Quận 1"
    out = scrub_text(f"Giao hang toi {address}")
    for fragment in ("Nguyễn Trãi", "Bến Thành", "Số nhà 25"):
        assert fragment not in out
    assert "REDACTED_ADDRESS_VN" in out


def test_scrub_cccd_and_credit_card() -> None:
    out = scrub_text("CCCD 001199012345 va the 4111 1111 1111 1111")
    assert "001199012345" not in out
    assert "4111 1111 1111 1111" not in out
    assert "REDACTED_CCCD" in out
    assert "REDACTED_CREDIT_CARD" in out


def test_lab_vocabulary_is_not_over_redacted() -> None:
    """Tranh false positive: tu khoa cua lab khong duoc coi la dia chi/PII."""
    for text in (
        "Khả năng quan sát và phương pháp monitoring",
        "Explain why metrics traces and logs work together",
        "How should alerts be designed?",
    ):
        assert "REDACTED" not in scrub_text(text)


def test_scrub_event_redacts_nested_payload() -> None:
    event_dict = {
        "event": "request_received",
        "payload": {
            "message_preview": "mail toi student@vinuni.edu.vn",
            "context": {"notes": ["goi 0901234567 nhe"]},
        },
    }

    scrubbed = scrub_event(None, "info", event_dict)

    assert "student@vinuni.edu.vn" not in str(scrubbed)
    assert "0901234567" not in str(scrubbed)
    assert "REDACTED_EMAIL" in scrubbed["payload"]["message_preview"]
    assert "REDACTED_PHONE_VN" in scrubbed["payload"]["context"]["notes"][0]


def test_scrub_event_also_covers_fields_outside_payload() -> None:
    """validate_logs.py quet toan bo record, nen PII ngoai payload cung phai bi che."""
    event_dict = {
        "event": "request_received",
        "session_id": "student@vinuni.edu.vn",
        "payload": {},
    }

    scrubbed = scrub_event(None, "info", event_dict)

    assert "student@vinuni.edu.vn" not in str(scrubbed)


def test_scrub_event_keeps_technical_identifiers_intact() -> None:
    event_dict = {
        "ts": "2026-08-11T00:00:00.000000Z",
        "level": "info",
        "correlation_id": "req-1a2b3c4d",
        "event": "response_sent",
    }

    scrubbed = scrub_event(None, "info", dict(event_dict))

    assert scrubbed["ts"] == event_dict["ts"]
    assert scrubbed["level"] == "info"
    assert scrubbed["correlation_id"] == "req-1a2b3c4d"
