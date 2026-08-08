"""Shared pytest fixtures and bootstrap used by unit and integration tests.

Loads .env and .env.local so DATABASE_URL and related settings are available
without requiring manual export in each test run.
"""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv


def _load_test_environment() -> None:
	root = Path(__file__).resolve().parents[1]
	load_dotenv(root / ".env")
	load_dotenv(root / ".env.local", override=False)


_load_test_environment()
