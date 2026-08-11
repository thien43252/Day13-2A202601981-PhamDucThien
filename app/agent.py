from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass
from functools import wraps
from typing import Any, Iterator

from . import metrics
from .mock_llm import FakeLLM
from .mock_rag import retrieve
from .pii import hash_user_id, summarize_text
from .prompt_management import resolve_prompt
from .tracing import get_langfuse_client, tracing_enabled


@dataclass
class AgentResult:
    answer: str
    latency_ms: int
    tokens_in: int
    tokens_out: int
    cost_usd: float
    quality_score: float
    trace_id: str | None = None


def _preserve_wrapped(func):
    """Keep a stable seam for tests without creating a second Langfuse context."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return func(*args, **kwargs)

    return wrapper


@contextmanager
def _generation_scope(client: Any, *, model: str) -> Iterator[None]:
    """Use one Langfuse client for both the generation and its trace metadata."""
    start_generation = getattr(client, "start_as_current_generation", None)
    if not callable(start_generation):
        yield
        return

    with start_generation(
        name="lab-agent.run",
        model=model,
        input=None,
        end_on_exit=True,
    ):
        yield


class LabAgent:
    def __init__(self, model: str = "claude-sonnet-4-5") -> None:
        self.model = model
        self.llm = FakeLLM(model=model)

    @_preserve_wrapped
    def run(self, user_id: str, feature: str, session_id: str, message: str) -> AgentResult:
        started = time.perf_counter()
        langfuse_client = get_langfuse_client()
        with _generation_scope(langfuse_client, model=self.model):
            docs = retrieve(message)
            prompt = resolve_prompt(
                langfuse_client,
                feature=feature,
                docs=docs,
                message=message,
                enabled=tracing_enabled(),
            )
            response = self.llm.generate(prompt.text)
            quality_score = self._heuristic_quality(message, response.text, docs)
            latency_ms = int((time.perf_counter() - started) * 1000)
            cost_usd = self._estimate_cost(response.usage.input_tokens, response.usage.output_tokens)

            langfuse_client.update_current_trace(
                user_id=hash_user_id(user_id),
                session_id=session_id,
                tags=["lab", feature, self.model],
                metadata={
                    "prompt_name": prompt.name,
                    "prompt_label": prompt.label,
                    "prompt_version": prompt.version,
                    "prompt_source": prompt.source,
                },
            )
            langfuse_client.update_current_generation(
                model=self.model,
                input={
                    "feature": feature,
                    "docs_count": len(docs),
                    "message_preview": summarize_text(message),
                },
                output={"answer_preview": summarize_text(response.text)},
                metadata={
                    "doc_count": len(docs),
                    "query_preview": summarize_text(message),
                    "prompt_name": prompt.name,
                    "prompt_label": prompt.label,
                    "prompt_version": prompt.version,
                    "prompt_source": prompt.source,
                    "prompt_fetch_error": prompt.fetch_error,
                },
                usage_details={
                    "input": response.usage.input_tokens,
                    "output": response.usage.output_tokens,
                    "total": response.usage.input_tokens + response.usage.output_tokens,
                },
                cost_details={"total": cost_usd},
                prompt=prompt.managed_prompt,
            )
            get_trace_id = getattr(langfuse_client, "get_current_trace_id", lambda: None)
            trace_id = get_trace_id()

        metrics.record_request(
            latency_ms=latency_ms,
            cost_usd=cost_usd,
            tokens_in=response.usage.input_tokens,
            tokens_out=response.usage.output_tokens,
            quality_score=quality_score,
        )

        return AgentResult(
            answer=response.text,
            latency_ms=latency_ms,
            tokens_in=response.usage.input_tokens,
            tokens_out=response.usage.output_tokens,
            cost_usd=cost_usd,
            quality_score=quality_score,
            trace_id=trace_id,
        )

    def _estimate_cost(self, tokens_in: int, tokens_out: int) -> float:
        input_cost = (tokens_in / 1_000_000) * 3
        output_cost = (tokens_out / 1_000_000) * 15
        return round(input_cost + output_cost, 6)

    def _heuristic_quality(self, question: str, answer: str, docs: list[str]) -> float:
        score = 0.5
        if docs:
            score += 0.2
        if len(answer) > 40:
            score += 0.1
        if question.lower().split()[0:1] and any(token in answer.lower() for token in question.lower().split()[:3]):
            score += 0.1
        if "[REDACTED" in answer:
            score -= 0.2
        return round(max(0.0, min(1.0, score)), 2)
