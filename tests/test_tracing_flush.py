from __future__ import annotations

from app import tracing


class RecordingClient:
    def __init__(self) -> None:
        self.flushed = False

    def flush(self) -> None:
        self.flushed = True


def test_flush_langfuse_flushes_buffered_events(monkeypatch) -> None:
    client = RecordingClient()
    monkeypatch.setattr(tracing, "tracing_enabled", lambda: True)
    monkeypatch.setattr(tracing, "get_langfuse_client", lambda: client)

    tracing.flush_langfuse()

    assert client.flushed is True


def test_flush_langfuse_ignores_clients_without_flush(monkeypatch) -> None:
    monkeypatch.setattr(tracing, "tracing_enabled", lambda: True)
    monkeypatch.setattr(tracing, "get_langfuse_client", lambda: object())

    assert tracing.flush_langfuse() is None


def test_flush_langfuse_does_not_initialize_a_client_when_disabled(monkeypatch) -> None:
    monkeypatch.setattr(tracing, "tracing_enabled", lambda: False)
    monkeypatch.setattr(
        tracing,
        "get_langfuse_client",
        lambda: (_ for _ in ()).throw(AssertionError("client must not be initialized")),
    )

    assert tracing.flush_langfuse() is None
