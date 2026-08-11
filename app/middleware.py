from __future__ import annotations

import os
import re
import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from structlog.contextvars import bind_contextvars, clear_contextvars

CORRELATION_ID_HEADER = "x-request-id"
RESPONSE_TIME_HEADER = "x-response-time-ms"

# Hop dong voi R3/R4 (TEAMWORK.md 2.1): correlation ID luon la req-<8 ky tu hex>.
CORRELATION_ID_PATTERN = re.compile(r"^req-[0-9a-f]{8}$")


def new_correlation_id() -> str:
    return f"req-{uuid.uuid4().hex[:8]}"


def normalize_correlation_id(raw: str | None) -> str:
    """Nhan lai ID cua caller neu dung dinh dang, nguoc lai sinh ID moi.

    Khong tin tuong header cua client mot cach vo dieu kien: gia tri sai dinh dang
    se lam vo contract log va cho phep chen ky tu la vao response header.
    """
    if raw and CORRELATION_ID_PATTERN.match(raw.strip()):
        return raw.strip()
    return new_correlation_id()


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Xoa context cu de khong ro ri metadata giua cac request.
        clear_contextvars()

        correlation_id = normalize_correlation_id(request.headers.get(CORRELATION_ID_HEADER))

        # Bind vao structlog contextvars -> moi log trong request tu dong co correlation_id.
        bind_contextvars(
            correlation_id=correlation_id,
            env=os.getenv("APP_ENV", "dev"),
        )

        request.state.correlation_id = correlation_id

        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000

        # Tra correlation ID + thoi gian xu ly ve client de noi log <-> trace <-> response.
        response.headers[CORRELATION_ID_HEADER] = correlation_id
        response.headers[RESPONSE_TIME_HEADER] = f"{elapsed_ms:.2f}"

        return response
