from __future__ import annotations

from collections.abc import Mapping


class DeterministicRiskFeatureEngine:
    """Pure deterministic grouping of ratios/trend features into risk feature categories."""

    @staticmethod
    def calculate(
        ratios: Mapping[str, float | None],
        trend_features: Mapping[str, float | None],
    ) -> dict[str, dict[str, float | None]]:
        return {
            "liquidity": {
                "current_ratio": ratios.get("current_ratio"),
                "current_ratio_change": trend_features.get("current_ratio_change"),
                "cash_ratio": ratios.get("cash_ratio"),
            },
            "leverage": {
                "debt_to_equity": ratios.get("debt_to_equity"),
                "debt_to_equity_change": trend_features.get("debt_to_equity_change"),
                "debt_to_assets": ratios.get("debt_to_assets"),
            },
            "profitability": {
                "net_profit_margin": ratios.get("net_profit_margin"),
                "net_profit_margin_change": trend_features.get("net_profit_margin_change"),
                "operating_margin": ratios.get("operating_margin"),
                "operating_margin_change": trend_features.get("operating_margin_change"),
                "roa": ratios.get("roa"),
                "roe": ratios.get("roe"),
            },
            "cash_flow": {
                "operating_cash_flow_margin": ratios.get("operating_cash_flow_margin"),
                "operating_cash_flow_to_debt": ratios.get("operating_cash_flow_to_debt"),
                "free_cash_flow": ratios.get("free_cash_flow"),
                "free_cash_flow_growth": trend_features.get("free_cash_flow_growth"),
            },
            "growth": {
                "revenue_growth": trend_features.get("revenue_growth"),
                "net_income_growth": trend_features.get("net_income_growth"),
            },
        }
