from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Iterable

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

load_dotenv(ROOT / ".env")
load_dotenv(ROOT / ".env.local", override=False)

from risk_platform.application.use_cases.sec_ingest_use_case import IngestSecFinancialStatementsUseCase
from risk_platform.infrastructure.database.repositories.sec_statement_repository import PostgresSecStatementRepository
from risk_platform.infrastructure.external.sec.edgar_service import SecEdgarClient


def resolve_tickers_from_env() -> list[str]:
    raw_tickers = os.getenv("SEC_TICKERS", "")
    if raw_tickers.strip():
        parsed = [ticker.strip().upper() for ticker in raw_tickers.split(",") if ticker.strip()]
        deduplicated = list(dict.fromkeys(parsed))
        if deduplicated:
            return deduplicated

    fallback = os.getenv("SEC_TICKER", "AAPL").strip().upper()
    if not fallback:
        raise ValueError("SEC_TICKER or SEC_TICKERS must provide at least one ticker")
    return [fallback]


def resolve_legacy_cik_overrides_from_env() -> dict[str, list[str]]:
    raw_overrides = os.getenv("SEC_LEGACY_CIK_OVERRIDES", "")
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


def _print_ingestion_summary(*, tickers: Iterable[str], counts: dict[str, int], database_url: str | None) -> None:
    ticker_list = list(tickers)
    total_rows = sum(counts.values())
    for ticker in ticker_list:
        count = counts.get(ticker, 0)
        if database_url:
            print(f"Persisted {count} SEC financial statement rows for {ticker} into PostgreSQL")
        else:
            print(f"Persisted {count} SEC financial statement rows for {ticker} in memory (no DATABASE_URL configured)")
    print(f"Total persisted rows across {len(ticker_list)} ticker(s): {total_rows}")


def main() -> None:
    tickers = resolve_tickers_from_env()
    user_agent = os.getenv("SEC_USER_AGENT", "risk-platform/0.1")
    request_delay_seconds = float(os.getenv("SEC_REQUEST_DELAY_SECONDS", "0.35"))
    max_retries = int(os.getenv("SEC_MAX_RETRIES", "3"))
    retry_backoff_seconds = float(os.getenv("SEC_RETRY_BACKOFF_SECONDS", "0.5"))
    retry_backoff_multiplier = float(os.getenv("SEC_RETRY_BACKOFF_MULTIPLIER", "2.0"))
    legacy_cik_overrides = resolve_legacy_cik_overrides_from_env()
    database_url = os.getenv("DATABASE_URL")

    client = SecEdgarClient(
        user_agent=user_agent,
        request_delay_seconds=request_delay_seconds,
        max_retries=max_retries,
        retry_backoff_seconds=retry_backoff_seconds,
        retry_backoff_multiplier=retry_backoff_multiplier,
        legacy_cik_overrides=legacy_cik_overrides,
    )
    repository = PostgresSecStatementRepository(database_url=database_url)
    use_case = IngestSecFinancialStatementsUseCase(client=client, repository=repository)

    counts = use_case.execute_many(tickers)
    _print_ingestion_summary(tickers=tickers, counts=counts, database_url=database_url)


if __name__ == "__main__":
    main()
