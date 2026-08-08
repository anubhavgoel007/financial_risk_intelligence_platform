from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class FinancialRatioHistoryPoint:
    fiscal_year: int
    fiscal_period: str
    ratios: dict[str, float | None]
    trend_features: dict[str, float | None]


@dataclass(slots=True, frozen=True)
class FinancialRatioHistoryResult:
    ticker: str
    fiscal_period: str
    start_fiscal_year: int
    end_fiscal_year: int
    points: list[FinancialRatioHistoryPoint]

    def to_dict(self) -> dict[str, object]:
        return {
            "ticker": self.ticker,
            "fiscal_period": self.fiscal_period,
            "start_fiscal_year": self.start_fiscal_year,
            "end_fiscal_year": self.end_fiscal_year,
            "points": [
                {
                    "fiscal_year": point.fiscal_year,
                    "fiscal_period": point.fiscal_period,
                    "ratios": point.ratios,
                    "trend_features": point.trend_features,
                }
                for point in self.points
            ],
        }
