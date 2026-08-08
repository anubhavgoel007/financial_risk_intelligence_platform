from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class FinancialRatiosResult:
    ticker: str
    fiscal_year: int
    fiscal_period: str
    ratios: dict[str, float | None]

    def to_dict(self) -> dict[str, object]:
        return {
            "ticker": self.ticker,
            "fiscal_year": self.fiscal_year,
            "fiscal_period": self.fiscal_period,
            "ratios": self.ratios,
        }
