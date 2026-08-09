from __future__ import annotations

from dataclasses import dataclass

RISK_FEATURE_COLUMNS: tuple[str, ...] = (
    "current_ratio",
    "current_ratio_change",
    "cash_ratio",
    "debt_to_equity",
    "debt_to_equity_change",
    "debt_to_assets",
    "net_profit_margin",
    "net_profit_margin_change",
    "operating_margin",
    "operating_margin_change",
    "roa",
    "roe",
    "operating_cash_flow_margin",
    "operating_cash_flow_to_debt",
    "free_cash_flow",
    "free_cash_flow_growth",
    "revenue_growth",
    "net_income_growth",
)


@dataclass(slots=True, frozen=True)
class RiskTrainingDatasetRow:
    ticker: str
    fiscal_year: int
    fiscal_period: str
    current_ratio: float | None
    current_ratio_change: float | None
    cash_ratio: float | None
    debt_to_equity: float | None
    debt_to_equity_change: float | None
    debt_to_assets: float | None
    net_profit_margin: float | None
    net_profit_margin_change: float | None
    operating_margin: float | None
    operating_margin_change: float | None
    roa: float | None
    roe: float | None
    operating_cash_flow_margin: float | None
    operating_cash_flow_to_debt: float | None
    free_cash_flow: float | None
    free_cash_flow_growth: float | None
    revenue_growth: float | None
    net_income_growth: float | None
    target_label: float | int | str | None

    def to_dict(self) -> dict[str, object]:
        return {
            "ticker": self.ticker,
            "fiscal_year": self.fiscal_year,
            "fiscal_period": self.fiscal_period,
            "current_ratio": self.current_ratio,
            "current_ratio_change": self.current_ratio_change,
            "cash_ratio": self.cash_ratio,
            "debt_to_equity": self.debt_to_equity,
            "debt_to_equity_change": self.debt_to_equity_change,
            "debt_to_assets": self.debt_to_assets,
            "net_profit_margin": self.net_profit_margin,
            "net_profit_margin_change": self.net_profit_margin_change,
            "operating_margin": self.operating_margin,
            "operating_margin_change": self.operating_margin_change,
            "roa": self.roa,
            "roe": self.roe,
            "operating_cash_flow_margin": self.operating_cash_flow_margin,
            "operating_cash_flow_to_debt": self.operating_cash_flow_to_debt,
            "free_cash_flow": self.free_cash_flow,
            "free_cash_flow_growth": self.free_cash_flow_growth,
            "revenue_growth": self.revenue_growth,
            "net_income_growth": self.net_income_growth,
            "target_label": self.target_label,
        }


@dataclass(slots=True, frozen=True)
class RiskTrainingDataset:
    fiscal_period: str
    rows: list[RiskTrainingDatasetRow]

    def to_dict(self) -> dict[str, object]:
        return {
            "fiscal_period": self.fiscal_period,
            "columns": ["ticker", "fiscal_year", *RISK_FEATURE_COLUMNS, "target_label"],
            "rows": [row.to_dict() for row in self.rows],
        }
