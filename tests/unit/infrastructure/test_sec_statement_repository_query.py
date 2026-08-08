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
