from __future__ import annotations

import os
import sys
from pathlib import Path

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


def main() -> None:
    ticker = os.getenv("SEC_TICKER", "AAPL")
    user_agent = os.getenv("SEC_USER_AGENT", "risk-platform/0.1")
    database_url = os.getenv("DATABASE_URL")

    client = SecEdgarClient(user_agent=user_agent)
    repository = PostgresSecStatementRepository(database_url=database_url)
    use_case = IngestSecFinancialStatementsUseCase(client=client, repository=repository)

    count = use_case.execute(ticker)
    if database_url:
        print(f"Persisted {count} SEC financial statement rows for {ticker} into PostgreSQL")
    else:
        print(f"Persisted {count} SEC financial statement rows for {ticker} in memory (no DATABASE_URL configured)")


if __name__ == "__main__":
    main()
