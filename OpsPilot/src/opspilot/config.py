"""Environment-backed configuration. No secrets are stored in source code."""
from dataclasses import dataclass
from pathlib import Path
import os

try:
    from dotenv import load_dotenv
    # Load .env from the project root regardless of the current working directory.
    load_dotenv(Path(__file__).resolve().parents[2] / ".env")
except ImportError:
    pass

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"


def _path_env(name: str, default: str) -> Path:
    value = Path(os.getenv(name, default)).expanduser()
    return value if value.is_absolute() else (PROJECT_ROOT / value).resolve()


def _api_key() -> str:
    """Accept GEMINI_API_KEY (preferred) or GOOGLE_API_KEY (Google SDK default)."""
    return (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "").strip()


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str
    gemini_model: str
    gemini_temperature: float
    gemini_max_tokens: int
    gemini_max_retries: int
    gemini_timeout: float
    database_path: Path
    chroma_path: Path
    approvals_dir: Path
    reports_dir: Path
    knowledge_dir: Path
    embedding_model: str
    top_k: int


def get_settings() -> Settings:
    data_dir = os.getenv("OPSILOT_DATA_DIR", "./data")
    return Settings(
        gemini_api_key=_api_key(),
        gemini_model=os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL).strip() or DEFAULT_GEMINI_MODEL,
        gemini_temperature=float(os.getenv("GEMINI_TEMPERATURE", "0.1")),
        gemini_max_tokens=int(os.getenv("GEMINI_MAX_TOKENS", "2500")),
        gemini_max_retries=max(0, int(os.getenv("GEMINI_MAX_RETRIES", "4"))),
        gemini_timeout=float(os.getenv("GEMINI_TIMEOUT_SECONDS", "60")),
        database_path=_path_env("OPSILOT_DB_PATH", f"{data_dir}/opspilot.db"),
        chroma_path=_path_env("OPSILOT_CHROMA_PATH", f"{data_dir}/chroma"),
        approvals_dir=_path_env("OPSILOT_APPROVALS_DIR", f"{data_dir}/approvals"),
        reports_dir=_path_env("OPSILOT_REPORTS_DIR", f"{data_dir}/reports"),
        knowledge_dir=_path_env("OPSILOT_KNOWLEDGE_DIR", "./knowledge"),
        embedding_model=os.getenv("OPSILOT_EMBED_MODEL", "BAAI/bge-small-en-v1.5"),
        top_k=max(1, min(int(os.getenv("OPSILOT_TOP_K", "4")), 10)),
    )
