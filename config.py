"""Configuration helpers for the NovaMind content pipeline."""

from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional convenience dependency
    load_dotenv = None


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUTS_DIR = BASE_DIR / "outputs"
PROMPTS_DIR = BASE_DIR / "prompts"

CONTACTS_FILE = DATA_DIR / "contacts.json"
SEGMENT_DEFINITIONS_FILE = DATA_DIR / "segment_definitions.json"
GENERATED_CONTENT_FILE = DATA_DIR / "generated_content.json"
CAMPAIGN_LOGS_FILE = DATA_DIR / "campaign_logs.json"
PERFORMANCE_HISTORY_FILE = DATA_DIR / "performance_history.json"
LATEST_SUMMARY_FILE = OUTPUTS_DIR / "latest_run_summary.md"

PERSONAS = [
    "Creative Agency Owner",
    "Operations Manager at a Small Agency",
    "Freelance Creative Professional",
]


def load_config() -> dict:
    """Load environment variables and return a simple runtime config."""
    if load_dotenv:
        load_dotenv()
    return {
        "groq_api_key": os.getenv("GROQ_API_KEY", "").strip(),
        "groq_model": os.getenv("GROQ_MODEL", "openai/gpt-oss-20b").strip(),
    }


def ensure_directories() -> None:
    """Ensure required directories exist before file operations."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
