"""Tests for agent helpers that need no network or API key."""
import pytest

from opspilot import agent
from opspilot.config import get_settings


def test_history_keeps_only_recent_plain_text_turns():
    history = [{"role": "user", "content": f"q{i}"} for i in range(20)]
    history.append({"role": "system", "content": "ignored"})
    history.append({"role": "assistant", "content": ["not", "text"]})
    history.append("not a dict")
    out = agent._history_to_messages(history)
    assert all(m["role"] in {"user", "assistant"} for m in out)
    assert all(isinstance(m["content"], str) for m in out)
    assert len(out) <= 12


def test_content_to_text_handles_gemini_block_lists():
    blocks = [
        {"type": "thinking", "thinking": "hidden reasoning"},
        {"type": "text", "text": "Revenue was 100."},
        {"type": "text", "text": "Orders: 4."},
    ]
    assert agent._content_to_text(blocks) == "Revenue was 100.\nOrders: 4."
    assert agent._content_to_text("plain") == "plain"


def test_run_agent_rejects_empty_query():
    assert agent.run_agent("   ") == "Please enter a question."


def test_missing_api_key_gives_clear_message(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setattr(agent, "_AGENT", None)
    monkeypatch.setattr("opspilot.config._api_key", lambda: "")
    reply = agent.run_agent("hello")
    assert "GEMINI_API_KEY" in reply


@pytest.mark.parametrize(
    "error, expected",
    [
        (RuntimeError("429 RESOURCE_EXHAUSTED quota"), "rate limit"),
        (RuntimeError("API key not valid. Please pass a valid API key."), "rejected the API key"),
        (RuntimeError("404 models/foo is not found for model"), "model was not found"),
        (RuntimeError("503 service unavailable"), "temporarily unreachable"),
        (ValueError("something else"), "Error type: ValueError"),
    ],
)
def test_friendly_error_mapping(error, expected):
    assert expected.lower() in agent._friendly_error(error).lower()


def test_gemini_settings_and_key_aliases(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("GOOGLE_API_KEY", "google-key")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-2.5-pro")
    settings = get_settings()
    assert settings.gemini_api_key == "google-key"
    assert settings.gemini_model == "gemini-2.5-pro"
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-key")
    assert get_settings().gemini_api_key == "gemini-key"


def test_agent_graph_builds_with_dummy_key(monkeypatch):
    pytest.importorskip("langchain_google_genai")
    pytest.importorskip("langchain")
    monkeypatch.setenv("GEMINI_API_KEY", "dummy-key-for-construction-only")
    # The RAG tool module imports only langchain_core at import time, so this stays offline.
    built = agent.build_agent()
    assert built is not None
