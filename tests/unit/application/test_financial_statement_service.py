from __future__ import annotations

import pytest

from risk_platform.application.use_cases.financial_statement_service import FinancialStatementService
from risk_platform.domain.entities.sec_financial_statement_fact import SecFinancialStatementFact
from risk_platform.domain.services.financial_metric_mapping import METRIC_CONCEPT_MAPPINGS
from risk_platform.domain.value_objects.canonical_financial_metric import CanonicalFinancialMetric


class FakeFactRepository:
    def __init__(self, facts: list[SecFinancialStatementFact]) -> None:
        self._facts = facts

    def get_facts_for_period(
        self,
        *,
        ticker: str,
        fiscal_year: int,
        fiscal_period: str,
        statement_type: str,
        concepts: list[str],
    ) -> list[SecFinancialStatementFact]:
        concept_set = set(concepts)
        return [
            fact
            for fact in self._facts
            if fact.ticker == ticker
            and fact.fiscal_year == fiscal_year
            and fact.fiscal_period == fiscal_period
            and fact.statement_type == statement_type
            and fact.concept in concept_set
        ]


def test_mapping_configuration_includes_all_canonical_metrics() -> None:
    mapped = {mapping.metric for mapping in METRIC_CONCEPT_MAPPINGS}
    assert mapped == set(CanonicalFinancialMetric)


def test_prefers_exact_concept_over_fallback_even_if_fallback_is_later() -> None:
    facts = [
        SecFinancialStatementFact(
            id=1,
            ticker="AAPL",
            concept="RevenueFromContractWithCustomerExcludingAssessedTax",
            value=100.0,
            unit="USD",
            fiscal_year=2024,
            fiscal_period="FY",
            filed_on="2025-01-01",
            statement_type="income_statement",
        ),
        SecFinancialStatementFact(
            id=2,
            ticker="AAPL",
            concept="Revenues",
            value=999.0,
            unit="USD",
            fiscal_year=2024,
            fiscal_period="FY",
            filed_on="2025-02-01",
            statement_type="income_statement",
        ),
    ]

    result = FinancialStatementService(FakeFactRepository(facts)).get_financial_metrics(
        ticker="AAPL",
        fiscal_year=2024,
        fiscal_period="FY",
    )

    assert result.metrics[CanonicalFinancialMetric.REVENUE] == 100.0


def test_fallback_concept_is_used_when_primary_is_absent() -> None:
    facts = [
        SecFinancialStatementFact(
            id=1,
            ticker="AAPL",
            concept="SalesRevenueNet",
            value=321.0,
            unit="USD",
            fiscal_year=2024,
            fiscal_period="Q1",
            filed_on="2024-05-01",
            statement_type="income_statement",
        )
    ]

    result = FinancialStatementService(FakeFactRepository(facts)).get_financial_metrics(
        ticker="AAPL",
        fiscal_year=2024,
        fiscal_period="Q1",
    )

    assert result.metrics[CanonicalFinancialMetric.REVENUE] == 321.0


def test_within_same_concept_prefers_latest_filed_on_then_highest_id() -> None:
    facts = [
        SecFinancialStatementFact(
            id=10,
            ticker="AAPL",
            concept="NetIncomeLoss",
            value=10.0,
            unit="USD",
            fiscal_year=2024,
            fiscal_period="FY",
            filed_on="2025-01-01",
            statement_type="income_statement",
        ),
        SecFinancialStatementFact(
            id=11,
            ticker="AAPL",
            concept="NetIncomeLoss",
            value=15.0,
            unit="USD",
            fiscal_year=2024,
            fiscal_period="FY",
            filed_on="2025-02-01",
            statement_type="income_statement",
        ),
        SecFinancialStatementFact(
            id=12,
            ticker="AAPL",
            concept="NetIncomeLoss",
            value=20.0,
            unit="USD",
            fiscal_year=2024,
            fiscal_period="FY",
            filed_on="2025-02-01",
            statement_type="income_statement",
        ),
    ]

    result = FinancialStatementService(FakeFactRepository(facts)).get_financial_metrics(
        ticker="AAPL",
        fiscal_year=2024,
        fiscal_period="FY",
    )

    assert result.metrics[CanonicalFinancialMetric.NET_INCOME] == 20.0


def test_unavailable_metric_returns_none() -> None:
    facts: list[SecFinancialStatementFact] = []

    result = FinancialStatementService(FakeFactRepository(facts)).get_financial_metrics(
        ticker="AAPL",
        fiscal_year=2024,
        fiscal_period="FY",
    )

    assert result.metrics[CanonicalFinancialMetric.CAPITAL_EXPENDITURES] is None


def test_gross_profit_uses_balance_sheet_statement_type_fallback() -> None:
    facts = [
        SecFinancialStatementFact(
            id=1,
            ticker="AAPL",
            concept="GrossProfit",
            value=180683000000.0,
            unit="USD",
            fiscal_year=2024,
            fiscal_period="FY",
            filed_on="2024-11-01",
            statement_type="balance_sheet",
        )
    ]

    result = FinancialStatementService(FakeFactRepository(facts)).get_financial_metrics(
        ticker="AAPL",
        fiscal_year=2024,
        fiscal_period="FY",
    )

    assert result.metrics[CanonicalFinancialMetric.GROSS_PROFIT] == 180683000000.0


def test_cash_uses_cash_flow_statement_type_fallback() -> None:
    facts = [
        SecFinancialStatementFact(
            id=1,
            ticker="AAPL",
            concept="CashAndCashEquivalentsAtCarryingValue",
            value=29943000000.0,
            unit="USD",
            fiscal_year=2024,
            fiscal_period="FY",
            filed_on="2024-11-01",
            statement_type="cash_flow",
        )
    ]

    result = FinancialStatementService(FakeFactRepository(facts)).get_financial_metrics(
        ticker="AAPL",
        fiscal_year=2024,
        fiscal_period="FY",
    )

    assert result.metrics[CanonicalFinancialMetric.CASH] == 29943000000.0


def test_operating_cash_flow_uses_balance_sheet_statement_type_fallback() -> None:
    facts = [
        SecFinancialStatementFact(
            id=1,
            ticker="AAPL",
            concept="NetCashProvidedByUsedInOperatingActivities",
            value=118254000000.0,
            unit="USD",
            fiscal_year=2024,
            fiscal_period="FY",
            filed_on="2024-11-01",
            statement_type="balance_sheet",
        )
    ]

    result = FinancialStatementService(FakeFactRepository(facts)).get_financial_metrics(
        ticker="AAPL",
        fiscal_year=2024,
        fiscal_period="FY",
    )

    assert result.metrics[CanonicalFinancialMetric.OPERATING_CASH_FLOW] == 118254000000.0


def test_validation_rules_for_required_inputs() -> None:
    service = FinancialStatementService(FakeFactRepository([]))

    with pytest.raises(ValueError):
        service.get_financial_metrics(ticker="", fiscal_year=2024, fiscal_period="FY")

    with pytest.raises(ValueError):
        service.get_financial_metrics(ticker="AAPL", fiscal_year=0, fiscal_period="FY")

    with pytest.raises(ValueError):
        service.get_financial_metrics(ticker="AAPL", fiscal_year=2024, fiscal_period="Q4")
