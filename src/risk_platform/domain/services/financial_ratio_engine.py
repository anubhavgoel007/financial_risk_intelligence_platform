from __future__ import annotations

from collections.abc import Mapping

from risk_platform.domain.value_objects.canonical_financial_metric import CanonicalFinancialMetric


class DeterministicFinancialRatioEngine:
    """Pure deterministic ratio calculations over canonical financial metrics."""

    @staticmethod
    def calculate(
        metrics: Mapping[CanonicalFinancialMetric, float | None],
    ) -> dict[str, float | None]:
        revenue = metrics.get(CanonicalFinancialMetric.REVENUE)
        net_income = metrics.get(CanonicalFinancialMetric.NET_INCOME)
        operating_income = metrics.get(CanonicalFinancialMetric.OPERATING_INCOME)
        total_assets = metrics.get(CanonicalFinancialMetric.TOTAL_ASSETS)
        shareholders_equity = metrics.get(CanonicalFinancialMetric.SHAREHOLDERS_EQUITY)
        current_assets = metrics.get(CanonicalFinancialMetric.CURRENT_ASSETS)
        current_liabilities = metrics.get(CanonicalFinancialMetric.CURRENT_LIABILITIES)
        cash = metrics.get(CanonicalFinancialMetric.CASH)
        long_term_debt = metrics.get(CanonicalFinancialMetric.LONG_TERM_DEBT)
        current_debt = metrics.get(CanonicalFinancialMetric.CURRENT_DEBT)
        operating_cash_flow = metrics.get(CanonicalFinancialMetric.OPERATING_CASH_FLOW)
        capital_expenditures = metrics.get(CanonicalFinancialMetric.CAPITAL_EXPENDITURES)

        total_debt = DeterministicFinancialRatioEngine._sum_if_all_present(long_term_debt, current_debt)

        return {
            "net_profit_margin": DeterministicFinancialRatioEngine._safe_divide(net_income, revenue),
            "operating_margin": DeterministicFinancialRatioEngine._safe_divide(
                operating_income,
                revenue,
            ),
            "roa": DeterministicFinancialRatioEngine._safe_divide(net_income, total_assets),
            "roe": DeterministicFinancialRatioEngine._safe_divide(net_income, shareholders_equity),
            "current_ratio": DeterministicFinancialRatioEngine._safe_divide(
                current_assets,
                current_liabilities,
            ),
            "cash_ratio": DeterministicFinancialRatioEngine._safe_divide(cash, current_liabilities),
            "debt_to_equity": DeterministicFinancialRatioEngine._safe_divide(
                total_debt,
                shareholders_equity,
            ),
            "debt_to_assets": DeterministicFinancialRatioEngine._safe_divide(total_debt, total_assets),
            "operating_cash_flow_margin": DeterministicFinancialRatioEngine._safe_divide(
                operating_cash_flow,
                revenue,
            ),
            "free_cash_flow": DeterministicFinancialRatioEngine._safe_subtract(
                operating_cash_flow,
                capital_expenditures,
            ),
            "operating_cash_flow_to_debt": DeterministicFinancialRatioEngine._safe_divide(
                operating_cash_flow,
                total_debt,
            ),
        }

    @staticmethod
    def _sum_if_all_present(*values: float | None) -> float | None:
        if any(value is None for value in values):
            return None
        return float(sum(values))

    @staticmethod
    def _safe_subtract(minuend: float | None, subtrahend: float | None) -> float | None:
        if minuend is None or subtrahend is None:
            return None
        return float(minuend - subtrahend)

    @staticmethod
    def _safe_divide(numerator: float | None, denominator: float | None) -> float | None:
        if numerator is None or denominator is None or denominator == 0:
            return None
        return float(numerator / denominator)
