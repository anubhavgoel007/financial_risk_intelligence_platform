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


def _resolve_sec_legacy_cik_overrides(raw_overrides: str) -> dict[str, list[str]]:
    """Parse SEC legacy CIK overrides like 'XOM:0000034088;ABC:0000123456|0000654321'."""
    if not raw_overrides.strip():
        return {}

    normalized: dict[str, list[str]] = {}
    segments = [segment.strip() for segment in raw_overrides.replace(",", ";").split(";") if segment.strip()]
    for segment in segments:
        if ":" not in segment:
            continue
        ticker_part, ciks_part = segment.split(":", maxsplit=1)
        ticker = ticker_part.strip().upper()
        if not ticker:
            continue

        ciks: list[str] = []
        seen: set[str] = set()
        for raw_cik in ciks_part.split("|"):
            cik = raw_cik.strip()
            if not cik:
                continue
            normalized_cik = cik.zfill(10)
            if normalized_cik in seen:
                continue
            seen.add(normalized_cik)
            ciks.append(normalized_cik)

        if ciks:
            normalized[ticker] = ciks
    return normalized


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
        self.sec_legacy_cik_overrides = _resolve_sec_legacy_cik_overrides(
            os.getenv("SEC_LEGACY_CIK_OVERRIDES", "")
        )
