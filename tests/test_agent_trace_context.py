from __future__ import annotations

from contextlib import contextmanager

from app import agent as agent_module


class ManagedPrompt:
    version = 1

    def compile(self, **variables: str) -> str:
        return "Feature={feature}\nDocs={docs}\nQuestion={message}".format(**variables)


class ContextClient:
    def __init__(self) -> None:
        self.in_scope = False
        self.trace_updates: list[dict] = []
        self.generation_updates: list[dict] = []

    @contextmanager
    def start_as_current_generation(self, **kwargs):
        self.in_scope = True
        try:
            yield self
        finally:
            self.in_scope = False

    def get_prompt(self, *_args, **_kwargs):
        return ManagedPrompt()

    def update_current_trace(self, **kwargs) -> None:
        assert self.in_scope
        self.trace_updates.append(kwargs)

    def update_current_generation(self, **kwargs) -> None:
        assert self.in_scope
        self.generation_updates.append(kwargs)

    def get_current_trace_id(self) -> str:
        assert self.in_scope
        return "trace-r2-context"


def test_agent_uses_one_explicit_langfuse_context(monkeypatch) -> None:
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "test-public-key")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "test-secret-key")
    client = ContextClient()
    monkeypatch.setattr(agent_module, "get_langfuse_client", lambda: client)

    result = agent_module.LabAgent().run(
        user_id="student-01",
        feature="qa",
        session_id="session-01",
        message="Explain traces",
    )

    assert result.trace_id == "trace-r2-context"
    assert client.trace_updates[-1]["metadata"]["prompt_version"] == "1"
    assert client.generation_updates[-1]["prompt"].version == 1
