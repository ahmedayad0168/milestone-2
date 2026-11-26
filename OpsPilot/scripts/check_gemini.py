"""Small provider smoke test; uses the configured model and does not expose the key."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from opspilot.agent import build_chat_model, _content_to_text  # noqa: E402
from opspilot.config import get_settings  # noqa: E402


def main():
    settings = get_settings()
    try:
        model = build_chat_model()
    except RuntimeError as exc:
        raise SystemExit(str(exc))
    print(f"Model: {settings.gemini_model}")
    response = model.invoke("Reply with exactly: OpsPilot connection OK")
    print(_content_to_text(response.content))


if __name__ == "__main__":
    main()
