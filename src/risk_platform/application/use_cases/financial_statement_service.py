from __future__ import annotations

from datetime import date
from typing import Protocol

from risk_platform.application.dto.financial_metrics_dto import FinancialMetricsResult
from risk_platform.domain.entities.sec_financial_statement_fact import SecFinancialStatementFact
from risk_platform.domain.services.financial_metric_mapping import METRIC_CONCEPT_MAPPINGS, MetricConceptMapping
from risk_platform.domain.value_objects.canonical_financial_metric import CanonicalFinancialMetric

SUPPORTED_FISCAL_PERIODS = {"FY", "Q1", "Q2", "Q3"}


class SecStatementFactRepository(Protocol):
    def get_facts_for_period(
        self,
        *,
        ticker: str,
        fiscal_year: int,
        fiscal_period: str,
        statement_type: str,
        concepts: list[str],
    ) -> list[SecFinancialStatementFact]:
        """Return SEC facts filtered to a ticker/fiscal period plus concept shortlist."""


class FinancialStatementService:
    """Maps raw SEC/XBRL concepts into canonical financial metrics."""

    def __init__(self, repository: SecStatementFactRepository) -> None:
        self._repository = repository

    def get_financial_metrics(
        self,
        ticker: str,
        fiscal_year: int,
        fiscal_period: str,
    ) -> FinancialMetricsResult:
        normalized_ticker = ticker.strip().upper()
        if not normalized_ticker:
            raise ValueError("ticker is required")
        if fiscal_year <= 0:
            raise ValueError("fiscal_year must be a positive integer")

        normalized_period = fiscal_period.strip().upper()
        if normalized_period not in SUPPORTED_FISCAL_PERIODS:
            raise ValueError("fiscal_period must be one of FY, Q1, Q2, Q3")

        values: dict[CanonicalFinancialMetric, float | None] = {}
        for mapping in METRIC_CONCEPT_MAPPINGS:
            facts_by_statement_type: dict[str, list[SecFinancialStatementFact]] = {}
            for statement_type in mapping.statement_types:
                facts_by_statement_type[statement_type] = self._repository.get_facts_for_period(
                    ticker=normalized_ticker,
                    fiscal_year=fiscal_year,
                    fiscal_period=normalized_period,
                    statement_type=statement_type,
                    concepts=list(mapping.concepts),
                )
            values[mapping.metric] = self._select_metric_value(facts_by_statement_type, mapping)

        return FinancialMetricsResult(
            ticker=normalized_ticker,
            fiscal_year=fiscal_year,
            fiscal_period=normalized_period,
            metrics=values,
        )

    @staticmethod
    def _select_metric_value(
        facts_by_statement_type: dict[str, list[SecFinancialStatementFact]],
        mapping: MetricConceptMapping,
    ) -> float | None:
        for concept in mapping.concepts:
            for statement_type in mapping.statement_types:
                concept_facts = [
                    fact
                    for fact in facts_by_statement_type.get(statement_type, [])
                    if fact.concept == concept
                ]
                if not concept_facts:
                    continue

                selected = max(
                    concept_facts,
                    key=lambda fact: (FinancialStatementService._filed_date(fact.filed_on), fact.id),
                )
                return selected.value
        return None

    @staticmethod
    def _filed_date(filed_on: str | None) -> date:
        if not filed_on:
            return date.min
        try:
            return date.fromisoformat(filed_on)
        except ValueError:
            return date.min
