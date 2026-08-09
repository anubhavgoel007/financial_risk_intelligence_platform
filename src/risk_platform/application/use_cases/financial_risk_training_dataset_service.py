from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol

from risk_platform.application.dto.risk_feature_set_dto import RiskFeatureHistoryResult
from risk_platform.application.dto.risk_training_dataset_dto import RiskTrainingDataset, RiskTrainingDatasetRow


class RiskFeatureHistoryProvider(Protocol):
    def get_risk_feature_history(
        self,
        ticker: str,
        start_fiscal_year: int,
        end_fiscal_year: int,
        fiscal_period: str = "FY",
    ) -> RiskFeatureHistoryResult:
        """Return deterministic risk features by fiscal year for one ticker."""


class FinancialRiskTrainingDatasetService:
    """Builds deterministic ML-training rows from risk features without model training."""

    def __init__(self, risk_feature_provider: RiskFeatureHistoryProvider) -> None:
        self._risk_feature_provider = risk_feature_provider

    def build_dataset(
        self,
        *,
        tickers: list[str],
        start_fiscal_year: int,
        end_fiscal_year: int,
        fiscal_period: str = "FY",
        target_labels: Mapping[tuple[str, int], float | int | str | None] | None = None,
    ) -> RiskTrainingDataset:
        normalized_period = fiscal_period.strip().upper()
        normalized_tickers = [ticker.strip().upper() for ticker in tickers if ticker.strip()]

        if start_fiscal_year <= 0 or end_fiscal_year <= 0:
            raise ValueError("fiscal years must be positive integers")
        if start_fiscal_year > end_fiscal_year:
            raise ValueError("start_fiscal_year must be less than or equal to end_fiscal_year")

        rows: list[RiskTrainingDatasetRow] = []
        for ticker in normalized_tickers:
            history = self._risk_feature_provider.get_risk_feature_history(
                ticker=ticker,
                start_fiscal_year=start_fiscal_year,
                end_fiscal_year=end_fiscal_year,
                fiscal_period=normalized_period,
            )
            for feature_set in history.features:
                label_key = (feature_set.ticker, feature_set.fiscal_year)
                target_label = None if target_labels is None else target_labels.get(label_key)
                rows.append(
                    RiskTrainingDatasetRow(
                        ticker=feature_set.ticker,
                        fiscal_year=feature_set.fiscal_year,
                        fiscal_period=feature_set.fiscal_period,
                        current_ratio=feature_set.liquidity.get("current_ratio"),
                        current_ratio_change=feature_set.liquidity.get("current_ratio_change"),
                        cash_ratio=feature_set.liquidity.get("cash_ratio"),
                        debt_to_equity=feature_set.leverage.get("debt_to_equity"),
                        debt_to_equity_change=feature_set.leverage.get("debt_to_equity_change"),
                        debt_to_assets=feature_set.leverage.get("debt_to_assets"),
                        net_profit_margin=feature_set.profitability.get("net_profit_margin"),
                        net_profit_margin_change=feature_set.profitability.get("net_profit_margin_change"),
                        operating_margin=feature_set.profitability.get("operating_margin"),
                        operating_margin_change=feature_set.profitability.get("operating_margin_change"),
                        roa=feature_set.profitability.get("roa"),
                        roe=feature_set.profitability.get("roe"),
                        operating_cash_flow_margin=feature_set.cash_flow.get("operating_cash_flow_margin"),
                        operating_cash_flow_to_debt=feature_set.cash_flow.get("operating_cash_flow_to_debt"),
                        free_cash_flow=feature_set.cash_flow.get("free_cash_flow"),
                        free_cash_flow_growth=feature_set.cash_flow.get("free_cash_flow_growth"),
                        revenue_growth=feature_set.growth.get("revenue_growth"),
                        net_income_growth=feature_set.growth.get("net_income_growth"),
                        target_label=target_label,
                    )
                )

        rows.sort(key=lambda row: (row.ticker, row.fiscal_year))
        return RiskTrainingDataset(fiscal_period=normalized_period, rows=rows)
