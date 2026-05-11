"""Application settings loaded from environment variables.

This module loads all configuration from a .env file using python-dotenv
and exposes them as typed constants. It validates that required variables
are set on import and raises a clear error if any are missing.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load .env file from project root
_project_root = Path(__file__).resolve().parent.parent
_env_path = _project_root / ".env"
load_dotenv(dotenv_path=_env_path)


def _get_required(key: str) -> str:
    """Get a required environment variable or raise an error.

    Args:
        key: The environment variable name.

    Returns:
        The environment variable value.

    Raises:
        SystemExit: If the variable is not set.
    """
    value = os.getenv(key)
    if value is None or value.strip() == "":
        print(
            f"[ERREUR] Variable d'environnement requise manquante: {key}. "
            f"Veuillez configurer le fichier .env (voir .env.example).",
            file=sys.stderr,
        )
        sys.exit(1)
    return value


def _get_optional(key: str, default: str = "") -> str:
    """Get an optional environment variable with a default value.

    Args:
        key: The environment variable name.
        default: Default value if not set.

    Returns:
        The environment variable value or the default.
    """
    return os.getenv(key, default)


# --- MySQL Database ---
DB_HOST: str = _get_required("DB_HOST")
DB_PORT: int = int(_get_optional("DB_PORT", "3306"))
DB_NAME: str = _get_required("DB_NAME")
DB_USER: str = _get_required("DB_USER")
DB_PASSWORD: str = _get_optional("DB_PASSWORD", "")

# --- Gemini LLM ---
LLM_PROVIDER: str = _get_optional("LLM_PROVIDER", "gemini")
GEMINI_API_KEY: str = _get_optional("GEMINI_API_KEY", "")
LLM_MODEL: str = _get_optional("LLM_MODEL", "gemini-1.5-flash")
LLM_MAX_TOKENS: int = int(_get_optional("LLM_MAX_TOKENS", "1000"))
LLM_TEMPERATURE: float = float(_get_optional("LLM_TEMPERATURE", "0.3"))

# --- Security ---
JWT_SECRET_KEY: str = _get_required("JWT_SECRET_KEY")
SESSION_TIMEOUT_MINUTES: int = int(_get_optional("SESSION_TIMEOUT_MINUTES", "30"))
MAX_LOGIN_ATTEMPTS: int = int(_get_optional("MAX_LOGIN_ATTEMPTS", "5"))

# --- Application ---
LOG_LEVEL: str = _get_optional("LOG_LEVEL", "INFO")
MAX_FILE_SIZE_MB: int = int(_get_optional("MAX_FILE_SIZE_MB", "50"))
EXPORT_DIR: str = _get_optional("EXPORT_DIR", "./exports")
LOG_DIR: str = _get_optional("LOG_DIR", "./logs")


def get_db_url() -> str:
    """Build and return the SQLAlchemy database connection URL.

    Returns:
        A MySQL connection string compatible with SQLAlchemy using PyMySQL driver.
    """
    return (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        f"?charset=utf8mb4"
    )


# Ensure export and log directories exist
Path(EXPORT_DIR).mkdir(parents=True, exist_ok=True)
Path(LOG_DIR).mkdir(parents=True, exist_ok=True)
