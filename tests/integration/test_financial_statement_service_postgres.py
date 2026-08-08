from __future__ import annotations

import os
from urllib.parse import urlparse
from uuid import uuid4

import pytest

from risk_platform.application.use_cases.financial_statement_service import FinancialStatementService
from risk_platform.domain.entities.sec_financial_statement import SecFinancialStatement
from risk_platform.domain.value_objects.canonical_financial_metric import CanonicalFinancialMetric
from risk_platform.infrastructure.database.repositories.sec_statement_repository import (
    PostgresSecStatementRepository,
)


@pytest.mark.integration
def test_financial_statement_service_postgres_round_trip() -> None:
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

    ticker = f"IT{uuid4().hex[:8].upper()}"
    repository = PostgresSecStatementRepository(database_url=database_url)

    repository.save_many(
        [
            SecFinancialStatement(
                ticker=ticker,
                cik="0000000000",
                company_name="Integration Test Co",
                concept="RevenueFromContractWithCustomerExcludingAssessedTax",
                value=111.0,
                unit="USD",
                fiscal_year=2024,
                fiscal_period="FY",
                filed_on="2025-01-15",
                statement_type="income_statement",
            ),
            SecFinancialStatement(
                ticker=ticker,
                cik="0000000000",
                company_name="Integration Test Co",
                concept="Revenues",
                value=999.0,
                unit="USD",
                fiscal_year=2024,
                fiscal_period="FY",
                filed_on="2025-02-15",
                statement_type="income_statement",
            ),
            SecFinancialStatement(
                ticker=ticker,
                cik="0000000000",
                company_name="Integration Test Co",
                concept="Assets",
                value=222.0,
                unit="USD",
                fiscal_year=2024,
                fiscal_period="FY",
                filed_on="2025-01-15",
                statement_type="balance_sheet",
            ),
            SecFinancialStatement(
                ticker=ticker,
                cik="0000000000",
                company_name="Integration Test Co",
                concept="NetCashProvidedByUsedInOperatingActivities",
                value=333.0,
                unit="USD",
                fiscal_year=2024,
                fiscal_period="FY",
                filed_on="2025-01-15",
                statement_type="cash_flow",
            ),
            SecFinancialStatement(
                ticker=ticker,
                cik="0000000000",
                company_name="Integration Test Co",
                concept="Assets",
                value=999999.0,
                unit="USD",
                fiscal_year=None,
                fiscal_period="FY",
                filed_on="2025-01-15",
                statement_type="balance_sheet",
            ),
        ]
    )

    service = FinancialStatementService(repository)
    result = service.get_financial_metrics(
        ticker=ticker,
        fiscal_year=2024,
        fiscal_period="FY",
    )

    assert result.metrics[CanonicalFinancialMetric.REVENUE] == 111.0
    assert result.metrics[CanonicalFinancialMetric.TOTAL_ASSETS] == 222.0
    assert result.metrics[CanonicalFinancialMetric.OPERATING_CASH_FLOW] == 333.0
