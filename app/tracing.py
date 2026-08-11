from __future__ import annotations

import atexit
import os
from typing import Any

try:
    from langfuse import get_client, observe

    LANGFUSE_SDK_AVAILABLE = True
except ImportError:  # pragma: no cover - chỉ dùng khi chưa cài requirements
    LANGFUSE_SDK_AVAILABLE = False

    def observe(*args: Any, **kwargs: Any):
        def decorator(func):
            return func

        return decorator

    class _DummyClient:
        def update_current_trace(self, **kwargs: Any) -> None:
            return None

        def update_current_generation(self, **kwargs: Any) -> None:
            return None

    def get_client():
        return _DummyClient()


_langfuse_client: Any | None = None


def get_langfuse_client():
    global _langfuse_client
    if _langfuse_client is None:
        _langfuse_client = get_client()
    return _langfuse_client


def flush_langfuse() -> None:
    """Send any buffered Langfuse events without affecting application shutdown."""
    if not tracing_enabled():
        return None
    try:
        flush = getattr(get_langfuse_client(), "flush", None)
        if callable(flush):
            flush()
    except Exception:  # pragma: no cover - tracing must never block shutdown
        return None


def tracing_enabled() -> bool:
    return LANGFUSE_SDK_AVAILABLE and bool(
        os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY")
    )


atexit.register(flush_langfuse)
