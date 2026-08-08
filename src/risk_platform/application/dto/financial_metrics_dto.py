from __future__ import annotations

from dataclasses import dataclass

from risk_platform.domain.value_objects.canonical_financial_metric import CanonicalFinancialMetric


@dataclass(slots=True, frozen=True)
class FinancialMetricsResult:
    ticker: str
    fiscal_year: int
    fiscal_period: str
    metrics: dict[CanonicalFinancialMetric, float | None]

    def to_dict(self) -> dict[str, object]:
        return {
            "ticker": self.ticker,
            "fiscal_year": self.fiscal_year,
            "fiscal_period": self.fiscal_period,
            "metrics": {metric.value: value for metric, value in self.metrics.items()},
        }
