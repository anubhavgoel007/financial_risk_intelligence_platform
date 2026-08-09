from __future__ import annotations

import pytest

from risk_platform.domain.entities.sec_financial_statement import SecFinancialStatement
from risk_platform.infrastructure.database.repositories.sec_statement_repository import (
    PostgresSecStatementRepository,
)


def test_get_facts_for_period_in_memory_ignores_null_fiscal_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    repository = PostgresSecStatementRepository(database_url=None)
    repository.save_many(
        [
            SecFinancialStatement(
                ticker="AAPL",
                cik="320193",
                company_name="Apple Inc.",
                concept="Assets",
                value=100.0,
                unit="USD",
                fiscal_year=2024,
                fiscal_period="FY",
                filed_on="2025-01-01",
                statement_type="balance_sheet",
            ),
            SecFinancialStatement(
                ticker="AAPL",
                cik="320193",
                company_name="Apple Inc.",
                concept="Assets",
                value=200.0,
                unit="USD",
                fiscal_year=None,
                fiscal_period="FY",
                filed_on="2025-01-01",
                statement_type="balance_sheet",
            ),
            SecFinancialStatement(
                ticker="AAPL",
                cik="320193",
                company_name="Apple Inc.",
                concept="Assets",
                value=300.0,
                unit="USD",
                fiscal_year=2024,
                fiscal_period=None,
                filed_on="2025-01-01",
                statement_type="balance_sheet",
            ),
        ]
    )

    facts = repository.get_facts_for_period(
        ticker="AAPL",
        fiscal_year=2024,
        fiscal_period="FY",
        statement_type="balance_sheet",
        concepts=["Assets"],
    )

    assert len(facts) == 1
    assert facts[0].value == 100.0


def test_list_available_tickers_in_memory_filters_by_min_distinct_years(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    repository = PostgresSecStatementRepository(database_url=None)
    repository.save_many(
        [
            SecFinancialStatement(
                ticker="AAPL",
                cik="320193",
                company_name="Apple Inc.",
                concept="Assets",
                value=100.0,
                unit="USD",
                fiscal_year=2023,
                fiscal_period="FY",
                filed_on="2024-01-01",
                statement_type="balance_sheet",
            ),
            SecFinancialStatement(
                ticker="AAPL",
                cik="320193",
                company_name="Apple Inc.",
                concept="Assets",
                value=110.0,
                unit="USD",
                fiscal_year=2024,
                fiscal_period="FY",
                filed_on="2025-01-01",
                statement_type="balance_sheet",
            ),
            SecFinancialStatement(
                ticker="MSFT",
                cik="0000789019",
                company_name="Microsoft Corp",
                concept="Assets",
                value=200.0,
                unit="USD",
                fiscal_year=2024,
                fiscal_period="FY",
                filed_on="2025-01-01",
                statement_type="balance_sheet",
            ),
        ]
    )

    tickers = repository.list_available_tickers(fiscal_period="FY", min_distinct_years=2, limit=10)

    assert tickers == ["AAPL"]


def test_list_available_fiscal_years_for_ticker_in_memory_returns_sorted_years(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    repository = PostgresSecStatementRepository(database_url=None)
    repository.save_many(
        [
            SecFinancialStatement(
                ticker="AAPL",
                cik="320193",
                company_name="Apple Inc.",
                concept="Assets",
                value=100.0,
                unit="USD",
                fiscal_year=2024,
                fiscal_period="FY",
                filed_on="2025-01-01",
                statement_type="balance_sheet",
            ),
            SecFinancialStatement(
                ticker="AAPL",
                cik="320193",
                company_name="Apple Inc.",
                concept="Assets",
                value=90.0,
                unit="USD",
                fiscal_year=2022,
                fiscal_period="FY",
                filed_on="2023-01-01",
                statement_type="balance_sheet",
            ),
            SecFinancialStatement(
                ticker="AAPL",
                cik="320193",
                company_name="Apple Inc.",
                concept="Assets",
                value=95.0,
                unit="USD",
                fiscal_year=2023,
                fiscal_period="FY",
                filed_on="2024-01-01",
                statement_type="balance_sheet",
            ),
        ]
    )

    years = repository.list_available_fiscal_years_for_ticker(ticker="aapl", fiscal_period="FY")

    assert years == [2022, 2023, 2024]
