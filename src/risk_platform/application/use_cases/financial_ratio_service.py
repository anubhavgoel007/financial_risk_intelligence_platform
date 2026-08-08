from __future__ import annotations

from risk_platform.application.dto.financial_metrics_dto import FinancialMetricsResult
from risk_platform.application.dto.financial_ratios_dto import FinancialRatiosResult
from risk_platform.application.use_cases.financial_statement_service import FinancialStatementService
from risk_platform.domain.services.financial_ratio_engine import DeterministicFinancialRatioEngine


class FinancialRatioService:
    """Application use case for deterministic financial ratio calculations."""

    def __init__(self, financial_statement_service: FinancialStatementService) -> None:
        self._financial_statement_service = financial_statement_service

    def get_financial_ratios(
        self,
        ticker: str,
        fiscal_year: int,
        fiscal_period: str,
    ) -> FinancialRatiosResult:
        metrics_result = self._financial_statement_service.get_financial_metrics(
            ticker=ticker,
            fiscal_year=fiscal_year,
            fiscal_period=fiscal_period,
        )
        return self.calculate_from_financial_metrics(metrics_result)

    @staticmethod
    def calculate_from_financial_metrics(metrics_result: FinancialMetricsResult) -> FinancialRatiosResult:
        ratios = DeterministicFinancialRatioEngine.calculate(metrics_result.metrics)
        return FinancialRatiosResult(
            ticker=metrics_result.ticker,
            fiscal_year=metrics_result.fiscal_year,
            fiscal_period=metrics_result.fiscal_period,
            ratios=ratios,
        )
