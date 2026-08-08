from __future__ import annotations

import os
from math import isclose
from urllib.parse import urlparse
from uuid import uuid4

import pytest

from risk_platform.application.use_cases.financial_statement_service import FinancialStatementService
from risk_platform.application.use_cases.financial_ratio_service import FinancialRatioService
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


@pytest.mark.integration
def test_aapl_fy2020_operating_margin_regression() -> None:
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

    repository = PostgresSecStatementRepository(database_url=database_url)
    metrics_service = FinancialStatementService(repository)
    ratio_service = FinancialRatioService(metrics_service)

    metrics = metrics_service.get_financial_metrics("AAPL", 2020, "FY")
    revenue = metrics.metrics[CanonicalFinancialMetric.REVENUE]
    operating_income = metrics.metrics[CanonicalFinancialMetric.OPERATING_INCOME]

    if revenue is None or operating_income is None:
        pytest.skip("AAPL FY2020 canonical facts are not available in this database")

    ratios = ratio_service.calculate_from_financial_metrics(metrics)
    operating_margin = ratios.ratios["operating_margin"]
    assert operating_margin is not None

    # Expected annual AAPL FY2020 canonical values from SEC comparative disclosure.
    assert isclose(revenue, 274515000000.0, rel_tol=0.0, abs_tol=1.0)
    assert isclose(operating_income, 66288000000.0, rel_tol=0.0, abs_tol=1.0)
    expected_margin = operating_income / revenue
    assert isclose(operating_margin, expected_margin, rel_tol=0.0, abs_tol=1e-12)


@pytest.mark.integration
def test_aapl_fy2020_net_profit_margin_and_2021_revenue_growth_regression() -> None:
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

    repository = PostgresSecStatementRepository(database_url=database_url)
    metrics_service = FinancialStatementService(repository)
    ratio_service = FinancialRatioService(metrics_service)

    metrics_2020 = metrics_service.get_financial_metrics("AAPL", 2020, "FY")
    revenue_2020 = metrics_2020.metrics[CanonicalFinancialMetric.REVENUE]
    net_income_2020 = metrics_2020.metrics[CanonicalFinancialMetric.NET_INCOME]
    gross_profit_2020 = metrics_2020.metrics[CanonicalFinancialMetric.GROSS_PROFIT]

    if revenue_2020 is None or net_income_2020 is None or gross_profit_2020 is None:
        pytest.skip("AAPL FY2020 canonical facts are not available in this database")

    ratios_2020 = ratio_service.calculate_from_financial_metrics(metrics_2020)
    net_profit_margin_2020 = ratios_2020.ratios["net_profit_margin"]
    assert net_profit_margin_2020 is not None

    assert isclose(revenue_2020, 274515000000.0, rel_tol=0.0, abs_tol=1.0)
    assert isclose(net_income_2020, 57411000000.0, rel_tol=0.0, abs_tol=1.0)
    assert isclose(gross_profit_2020, 104956000000.0, rel_tol=0.0, abs_tol=1.0)
    assert isclose(net_profit_margin_2020, net_income_2020 / revenue_2020, rel_tol=0.0, abs_tol=1e-12)

    history = ratio_service.get_historical_financial_ratios(
        ticker="AAPL",
        start_fiscal_year=2020,
        end_fiscal_year=2021,
        fiscal_period="FY",
    )
    revenue_growth_2021 = history.points[1].trend_features["revenue_growth"]
    assert revenue_growth_2021 is not None

    expected_growth = (365817000000.0 - 274515000000.0) / 274515000000.0
    assert isclose(revenue_growth_2021, expected_growth, rel_tol=0.0, abs_tol=1e-12)
