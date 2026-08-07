"""Application configuration and environment-based settings."""

from __future__ import annotations

import os


class Settings:
    """Minimal runtime settings for SEC ingestion and related services."""

    def __init__(self) -> None:
        self.database_url = os.getenv("DATABASE_URL", "")
        self.sec_user_agent = os.getenv("SEC_USER_AGENT", "risk-platform/0.1")
        self.sec_ticker = os.getenv("SEC_TICKER", "AAPL")
