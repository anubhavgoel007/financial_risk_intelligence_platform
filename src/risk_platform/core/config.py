"""Application configuration and environment-based settings."""

from __future__ import annotations

import os


def _resolve_sec_tickers(raw_tickers: str, fallback_ticker: str) -> list[str]:
    """Parse a comma-separated ticker list, deduplicating while preserving order."""
    parsed = [ticker.strip().upper() for ticker in raw_tickers.split(",") if ticker.strip()]
    if parsed:
        return list(dict.fromkeys(parsed))
    fallback = fallback_ticker.strip().upper()
    return [fallback] if fallback else []


class Settings:
    """Minimal runtime settings for SEC ingestion and related services."""

    def __init__(self) -> None:
        self.database_url = os.getenv("DATABASE_URL", "")
        self.sec_user_agent = os.getenv("SEC_USER_AGENT", "risk-platform/0.1")
        self.sec_ticker = os.getenv("SEC_TICKER", "AAPL")
        self.sec_tickers = _resolve_sec_tickers(os.getenv("SEC_TICKERS", ""), self.sec_ticker)
        self.sec_request_delay_seconds = float(os.getenv("SEC_REQUEST_DELAY_SECONDS", "0.35"))
        self.sec_max_retries = int(os.getenv("SEC_MAX_RETRIES", "3"))
        self.sec_retry_backoff_seconds = float(os.getenv("SEC_RETRY_BACKOFF_SECONDS", "0.5"))
        self.sec_retry_backoff_multiplier = float(os.getenv("SEC_RETRY_BACKOFF_MULTIPLIER", "2.0"))
