from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class RiskFeatureSet:
    ticker: str
    fiscal_year: int
    fiscal_period: str
    liquidity: dict[str, float | None]
    leverage: dict[str, float | None]
    profitability: dict[str, float | None]
    cash_flow: dict[str, float | None]
    growth: dict[str, float | None]

    def to_dict(self) -> dict[str, object]:
        return {
            "ticker": self.ticker,
            "fiscal_year": self.fiscal_year,
            "fiscal_period": self.fiscal_period,
            "liquidity": self.liquidity,
            "leverage": self.leverage,
            "profitability": self.profitability,
            "cash_flow": self.cash_flow,
            "growth": self.growth,
        }


@dataclass(slots=True, frozen=True)
class RiskFeatureHistoryResult:
    ticker: str
    fiscal_period: str
    start_fiscal_year: int
    end_fiscal_year: int
    features: list[RiskFeatureSet]

    def to_dict(self) -> dict[str, object]:
        return {
            "ticker": self.ticker,
            "fiscal_period": self.fiscal_period,
            "start_fiscal_year": self.start_fiscal_year,
            "end_fiscal_year": self.end_fiscal_year,
            "features": [feature.to_dict() for feature in self.features],
        }
