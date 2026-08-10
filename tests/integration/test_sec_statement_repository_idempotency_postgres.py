from __future__ import annotations

import os
from urllib.parse import urlparse
from uuid import uuid4

import asyncpg
import pytest

from risk_platform.application.use_cases.sec_ingest_use_case import IngestSecFinancialStatementsUseCase
from risk_platform.domain.entities.sec_financial_statement import SecFinancialStatement
from risk_platform.infrastructure.database.repositories.sec_statement_repository import (
    PostgresSecStatementRepository,
)


@pytest.mark.integration
def test_save_many_is_idempotent_for_exact_duplicate_rows() -> None:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        pytest.skip("DATABASE_URL is not configured")

    parsed = urlparse(database_url)
    if parsed.username in {None, "", "USER"}:
        pytest.skip("DATABASE_URL uses placeholder credentials")
    if parsed.password == "PASSWORD":
        pytest.skip("DATABASE_URL uses placeholder credentials")
    if parsed.path.lstrip("/") in {"", "DBNAME"}:
        pytest.skip("DATABASE_URL uses placeholder database name")

    ticker = f"ID{uuid4().hex[:8].upper()}"
    repository = PostgresSecStatementRepository(database_url=database_url)
    statements = [
        SecFinancialStatement(
            ticker=ticker,
            cik="0000000000",
            company_name="Idempotency Test Co",
            concept="Assets",
            value=12345.67,
            unit="USD",
            fiscal_year=2024,
            fiscal_period="FY",
            filed_on="2025-01-31",
            statement_type="balance_sheet",
        )
    ]

    first_inserted = repository.save_many(statements)
    second_inserted = repository.save_many(statements)

    assert first_inserted == 1
    assert second_inserted == 0


@pytest.mark.integration
def test_execute_many_reports_insert_counts_independently_per_ticker() -> None:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        pytest.skip("DATABASE_URL is not configured")

    parsed = urlparse(database_url)
    if parsed.username in {None, "", "USER"}:
        pytest.skip("DATABASE_URL uses placeholder credentials")
    if parsed.password == "PASSWORD":
        pytest.skip("DATABASE_URL uses placeholder credentials")
    if parsed.path.lstrip("/") in {"", "DBNAME"}:
        pytest.skip("DATABASE_URL uses placeholder database name")

    ticker_a = f"IA{uuid4().hex[:6].upper()}"
    ticker_b = f"IB{uuid4().hex[:6].upper()}"

    class FakeClient:
        def fetch_company_facts(self, ticker: str) -> list[SecFinancialStatement]:
            if ticker == ticker_a:
                return [
                    SecFinancialStatement(
                        ticker=ticker,
                        cik="0000000000",
                        company_name="Independent Count Co A",
                        concept="Assets",
                        value=100.0,
                        unit="USD",
                        fiscal_year=2024,
                        fiscal_period="FY",
                        filed_on="2025-01-31",
                        statement_type="balance_sheet",
                    ),
                    SecFinancialStatement(
                        ticker=ticker,
                        cik="0000000000",
                        company_name="Independent Count Co A",
                        concept="Liabilities",
                        value=40.0,
                        unit="USD",
                        fiscal_year=2024,
                        fiscal_period="FY",
                        filed_on="2025-01-31",
                        statement_type="balance_sheet",
                    ),
                ]
            if ticker == ticker_b:
                return [
                    SecFinancialStatement(
                        ticker=ticker,
                        cik="0000000001",
                        company_name="Independent Count Co B",
                        concept="Assets",
                        value=200.0,
                        unit="USD",
                        fiscal_year=2024,
                        fiscal_period="FY",
                        filed_on="2025-01-31",
                        statement_type="balance_sheet",
                    )
                ]
            return []

    repository = PostgresSecStatementRepository(database_url=database_url)
    use_case = IngestSecFinancialStatementsUseCase(client=FakeClient(), repository=repository)

    first_counts = use_case.execute_many([ticker_a, ticker_b])
    second_counts = use_case.execute_many([ticker_a, ticker_b])

    assert first_counts == {ticker_a: 2, ticker_b: 1}
    assert second_counts == {ticker_a: 0, ticker_b: 0}


@pytest.mark.integration
def test_dual_cik_ingestion_is_idempotent_and_keeps_historical_fact() -> None:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        pytest.skip("DATABASE_URL is not configured")

    parsed = urlparse(database_url)
    if parsed.username in {None, "", "USER"}:
        pytest.skip("DATABASE_URL uses placeholder credentials")
    if parsed.password == "PASSWORD":
        pytest.skip("DATABASE_URL uses placeholder credentials")
    if parsed.path.lstrip("/") in {"", "DBNAME"}:
        pytest.skip("DATABASE_URL uses placeholder database name")

    ticker = f"XM{uuid4().hex[:6].upper()}"
    repository = PostgresSecStatementRepository(database_url=database_url)

    class FakeDualCikClient:
        def fetch_company_facts(self, requested_ticker: str) -> list[SecFinancialStatement]:
            assert requested_ticker == ticker
            return [
                # Simulate current CIK fact.
                SecFinancialStatement(
                    ticker=ticker,
                    cik="0002115436",
                    company_name="Exxon Mobil Corporation",
                    concept="Assets",
                    value=111.0,
                    unit="USD",
                    fiscal_year=2026,
                    fiscal_period="FY",
                    filed_on="2026-02-01",
                    statement_type="balance_sheet",
                ),
                # Simulate legacy historical CIK fact.
                SecFinancialStatement(
                    ticker=ticker,
                    cik="0000034088",
                    company_name="Exxon Mobil Corporation",
                    concept="Assets",
                    value=99.0,
                    unit="USD",
                    fiscal_year=2024,
                    fiscal_period="FY",
                    filed_on="2025-02-01",
                    statement_type="balance_sheet",
                ),
            ]

    use_case = IngestSecFinancialStatementsUseCase(client=FakeDualCikClient(), repository=repository)

    first_counts = use_case.execute_many([ticker])
    second_counts = use_case.execute_many([ticker])

    assert first_counts == {ticker: 2}
    assert second_counts == {ticker: 0}

    async_dsn = database_url.replace("postgresql+asyncpg://", "postgresql://", 1)

    async def _assert_persisted_rows() -> None:
        conn = await asyncpg.connect(async_dsn)
        try:
            rows = await conn.fetch(
                """
                SELECT cik, fiscal_year, value
                FROM sec_financial_statements
                WHERE UPPER(ticker) = UPPER($1)
                  AND concept = 'Assets'
                  AND fiscal_period = 'FY'
                ORDER BY fiscal_year
                """,
                ticker,
            )
            assert len(rows) == 2
            assert [str(row["cik"]) for row in rows] == ["0000034088", "0002115436"]
            assert [int(row["fiscal_year"]) for row in rows] == [2024, 2026]
        finally:
            await conn.close()

    import asyncio

    asyncio.run(_assert_persisted_rows())
