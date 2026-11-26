"""Single-agent orchestration using LangChain's LangGraph-backed create_agent with Gemini."""
from datetime import datetime
from typing import Any

from opspilot.config import get_settings
from opspilot.logging_config import get_logger
from opspilot.prompts.system_prompt import build_system_prompt
from opspilot.tools.business_tools import BUSINESS_TOOLS
from opspilot.rag.tools import search_company_policies

logger = get_logger("opspilot.agent")
_AGENT = None


MISSING_KEY_MESSAGE = (
    "GEMINI_API_KEY is missing. Copy .env.example to .env and add a Gemini API key "
    "(create one at https://aistudio.google.com/apikey)."
)


def build_chat_model():
    """Create the Gemini chat model from settings (shared by the agent and the smoke test)."""
    settings = get_settings()
    if not settings.gemini_api_key:
        raise RuntimeError(MISSING_KEY_MESSAGE)
    from langchain_google_genai import ChatGoogleGenerativeAI

    return ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        api_key=settings.gemini_api_key,
        temperature=settings.gemini_temperature,
        max_tokens=settings.gemini_max_tokens,
        max_retries=settings.gemini_max_retries,  # built-in exponential backoff on 429/5xx
        timeout=settings.gemini_timeout,
    )


def build_agent():
    from langchain.agents import create_agent

    model = build_chat_model()
    tools = [*BUSINESS_TOOLS, search_company_policies]
    return create_agent(
        model=model,
        tools=tools,
        system_prompt=build_system_prompt(),
        name="opspilot_business_operations_agent",
    )


def get_agent():
    global _AGENT
    if _AGENT is None:
        _AGENT = build_agent()
    return _AGENT


def _history_to_messages(history: list[dict[str, Any]] | None) -> list[dict[str, str]]:
    """Keep only recent plain-text user/assistant turns; ignore UI-specific payloads."""
    messages: list[dict[str, str]] = []
    for item in (history or [])[-12:]:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        content = item.get("content")
        if role not in {"user", "assistant"} or not isinstance(content, str):
            continue
        if content.strip():
            messages.append({"role": role, "content": content[:6000]})
    return messages


def _content_to_text(content: Any) -> str:
    """Flatten message content. Gemini may return a list of typed blocks (text, thinking, ...)."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                # Skip non-text blocks such as reasoning/thinking or signatures.
                if block.get("type", "text") == "text" and isinstance(block.get("text"), str):
                    parts.append(block["text"])
            elif isinstance(block, str):
                parts.append(block)
        return "\n".join(p for p in parts if p)
    return str(content)


def _friendly_error(exc: Exception) -> str:
    """Map provider failures to a safe, actionable message (never echo secrets)."""
    text = f"{type(exc).__name__} {exc}".lower()
    if "gemini_api_key" in text:
        return str(exc)
    if any(s in text for s in ("429", "resource_exhausted", "quota", "rate limit", "ratelimit")):
        return ("Gemini rate limit or quota reached. Wait a minute and try again, "
                "or check your quota in Google AI Studio.")
    if any(s in text for s in ("api key not valid", "api_key_invalid", "permission_denied", "401", "403")):
        return "Gemini rejected the API key. Check GEMINI_API_KEY in your .env file."
    if any(s in text for s in ("not found", "404")) and "model" in text:
        return "The configured Gemini model was not found. Check GEMINI_MODEL in your .env file."
    if any(s in text for s in ("timeout", "timed out", "503", "unavailable", "connection")):
        return "Gemini is temporarily unreachable. Please try again shortly."
    return ("I couldn't complete that request. Check the application log and your API/provider configuration. "
            f"Error type: {type(exc).__name__}.")


def run_agent(query: str, history: list[dict[str, Any]] | None = None) -> str:
    if not isinstance(query, str) or not query.strip():
        return "Please enter a question."
    try:
        agent = get_agent()
        messages = _history_to_messages(history)
        messages.append({"role": "user", "content": query.strip()[:6000]})
        started = datetime.now()
        result = agent.invoke(
            {"messages": messages},
            config={"recursion_limit": 24},
        )
        elapsed = (datetime.now() - started).total_seconds()
        result_messages = result.get("messages", [])
        final_text = ""
        used_tools = []
        for msg in result_messages:
            msg_type = getattr(msg, "type", "")
            if msg_type == "tool":
                name = getattr(msg, "name", None)
                if name and name not in used_tools:
                    used_tools.append(name)
            if msg_type == "ai" and not getattr(msg, "tool_calls", None):
                candidate = _content_to_text(getattr(msg, "content", ""))
                if candidate.strip():
                    final_text = candidate
        if not final_text:
            final_text = "I could not produce a final answer from the available tool results. Please try a narrower request."
        if used_tools:
            final_text += "\n\n---\n*Tools used: " + ", ".join(used_tools) + f" · {elapsed:.1f}s*"
        logger.info("agent_completed tools=%s elapsed_seconds=%.2f", used_tools, elapsed)
        return final_text
    except Exception as exc:
        logger.exception("Agent request failed")
        return _friendly_error(exc)
