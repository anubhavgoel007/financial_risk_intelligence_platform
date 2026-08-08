from __future__ import annotations

from dataclasses import dataclass

from risk_platform.application.dto.financial_metrics_dto import FinancialMetricsResult
from risk_platform.application.dto.financial_ratio_history_dto import (
    FinancialRatioHistoryPoint,
    FinancialRatioHistoryResult,
)
from risk_platform.application.dto.financial_ratios_dto import FinancialRatiosResult
from risk_platform.application.use_cases.financial_statement_service import FinancialStatementService
from risk_platform.domain.services.financial_ratio_engine import DeterministicFinancialRatioEngine
from risk_platform.domain.value_objects.canonical_financial_metric import CanonicalFinancialMetric


@dataclass(slots=True, frozen=True)
class _YearlyContext:
    metrics_result: FinancialMetricsResult
    ratios_result: FinancialRatiosResult


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

    def get_historical_financial_ratios(
        self,
        ticker: str,
        start_fiscal_year: int,
        end_fiscal_year: int,
        fiscal_period: str = "FY",
    ) -> FinancialRatioHistoryResult:
        if start_fiscal_year <= 0 or end_fiscal_year <= 0:
            raise ValueError("fiscal years must be positive integers")
        if start_fiscal_year > end_fiscal_year:
            raise ValueError("start_fiscal_year must be less than or equal to end_fiscal_year")

        yearly_contexts: list[_YearlyContext] = []
        for fiscal_year in range(start_fiscal_year, end_fiscal_year + 1):
            metrics_result = self._financial_statement_service.get_financial_metrics(
                ticker=ticker,
                fiscal_year=fiscal_year,
                fiscal_period=fiscal_period,
            )
            ratios_result = self.calculate_from_financial_metrics(metrics_result)
            yearly_contexts.append(_YearlyContext(metrics_result=metrics_result, ratios_result=ratios_result))

        points = self._build_history_points(yearly_contexts)
        normalized_ticker = ticker.strip().upper()
        normalized_period = fiscal_period.strip().upper()
        return FinancialRatioHistoryResult(
            ticker=normalized_ticker,
            fiscal_period=normalized_period,
            start_fiscal_year=start_fiscal_year,
            end_fiscal_year=end_fiscal_year,
            points=points,
        )

    @staticmethod
    def calculate_from_financial_metrics(metrics_result: FinancialMetricsResult) -> FinancialRatiosResult:
        ratios = DeterministicFinancialRatioEngine.calculate(metrics_result.metrics)
        return FinancialRatiosResult(
            ticker=metrics_result.ticker,
            fiscal_year=metrics_result.fiscal_year,
            fiscal_period=metrics_result.fiscal_period,
            ratios=ratios,
        )

    @staticmethod
    def _build_history_points(yearly_contexts: list[_YearlyContext]) -> list[FinancialRatioHistoryPoint]:
        points: list[FinancialRatioHistoryPoint] = []

        for index, context in enumerate(yearly_contexts):
            previous = yearly_contexts[index - 1] if index > 0 else None

            revenue = context.metrics_result.metrics.get(CanonicalFinancialMetric.REVENUE)
            net_income = context.metrics_result.metrics.get(CanonicalFinancialMetric.NET_INCOME)
            operating_cash_flow = context.metrics_result.metrics.get(
                CanonicalFinancialMetric.OPERATING_CASH_FLOW
            )
            free_cash_flow = context.ratios_result.ratios.get("free_cash_flow")

            previous_revenue = None
            previous_net_income = None
            previous_operating_cash_flow = None
            previous_free_cash_flow = None
            previous_operating_margin = None
            previous_net_profit_margin = None
            previous_debt_to_equity = None
            previous_current_ratio = None

            if previous is not None:
                previous_revenue = previous.metrics_result.metrics.get(CanonicalFinancialMetric.REVENUE)
                previous_net_income = previous.metrics_result.metrics.get(
                    CanonicalFinancialMetric.NET_INCOME
                )
                previous_operating_cash_flow = previous.metrics_result.metrics.get(
                    CanonicalFinancialMetric.OPERATING_CASH_FLOW
                )
                previous_free_cash_flow = previous.ratios_result.ratios.get("free_cash_flow")
                previous_operating_margin = previous.ratios_result.ratios.get("operating_margin")
                previous_net_profit_margin = previous.ratios_result.ratios.get("net_profit_margin")
                previous_debt_to_equity = previous.ratios_result.ratios.get("debt_to_equity")
                previous_current_ratio = previous.ratios_result.ratios.get("current_ratio")

            trend_features = {
                "revenue_growth": FinancialRatioService._safe_growth(revenue, previous_revenue),
                "net_income_growth": FinancialRatioService._safe_growth(
                    net_income,
                    previous_net_income,
                ),
                "operating_margin_change": FinancialRatioService._safe_change(
                    context.ratios_result.ratios.get("operating_margin"),
                    previous_operating_margin,
                ),
                "net_profit_margin_change": FinancialRatioService._safe_change(
                    context.ratios_result.ratios.get("net_profit_margin"),
                    previous_net_profit_margin,
                ),
                "debt_to_equity_change": FinancialRatioService._safe_change(
                    context.ratios_result.ratios.get("debt_to_equity"),
                    previous_debt_to_equity,
                ),
                "current_ratio_change": FinancialRatioService._safe_change(
                    context.ratios_result.ratios.get("current_ratio"),
                    previous_current_ratio,
                ),
                "operating_cash_flow_growth": FinancialRatioService._safe_growth(
                    operating_cash_flow,
                    previous_operating_cash_flow,
                ),
                "free_cash_flow_growth": FinancialRatioService._safe_growth(
                    free_cash_flow,
                    previous_free_cash_flow,
                ),
            }

            points.append(
                FinancialRatioHistoryPoint(
                    fiscal_year=context.metrics_result.fiscal_year,
                    fiscal_period=context.metrics_result.fiscal_period,
                    ratios=context.ratios_result.ratios,
                    trend_features=trend_features,
                )
            )

        return points

    @staticmethod
    def _safe_change(current_value: float | None, previous_value: float | None) -> float | None:
        if current_value is None or previous_value is None:
            return None
        return float(current_value - previous_value)

    @staticmethod
    def _safe_growth(current_value: float | None, previous_value: float | None) -> float | None:
        if current_value is None or previous_value is None or previous_value == 0:
            return None
        return float((current_value - previous_value) / previous_value)
