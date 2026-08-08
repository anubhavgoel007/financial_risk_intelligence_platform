from __future__ import annotations

from risk_platform.application.dto.financial_ratio_history_dto import FinancialRatioHistoryResult
from risk_platform.application.dto.risk_feature_set_dto import RiskFeatureHistoryResult, RiskFeatureSet
from risk_platform.application.use_cases.financial_ratio_service import FinancialRatioService
from risk_platform.domain.services.financial_risk_feature_engine import DeterministicRiskFeatureEngine


class FinancialRiskFeatureService:
    """Application use case for deterministic risk feature engineering.

    Builds on top of the existing historical ratio engine; does not compute a
    risk score and does not modify ratio calculations or raw SEC data.
    """

    def __init__(self, financial_ratio_service: FinancialRatioService) -> None:
        self._financial_ratio_service = financial_ratio_service

    def get_risk_feature_history(
        self,
        ticker: str,
        start_fiscal_year: int,
        end_fiscal_year: int,
        fiscal_period: str = "FY",
    ) -> RiskFeatureHistoryResult:
        ratio_history = self._financial_ratio_service.get_historical_financial_ratios(
            ticker=ticker,
            start_fiscal_year=start_fiscal_year,
            end_fiscal_year=end_fiscal_year,
            fiscal_period=fiscal_period,
        )
        return self.calculate_from_ratio_history(ratio_history)

    @staticmethod
    def calculate_from_ratio_history(ratio_history: FinancialRatioHistoryResult) -> RiskFeatureHistoryResult:
        features = [
            RiskFeatureSet(
                ticker=ratio_history.ticker,
                fiscal_year=point.fiscal_year,
                fiscal_period=point.fiscal_period,
                **DeterministicRiskFeatureEngine.calculate(point.ratios, point.trend_features),
            )
            for point in ratio_history.points
        ]
        return RiskFeatureHistoryResult(
            ticker=ratio_history.ticker,
            fiscal_period=ratio_history.fiscal_period,
            start_fiscal_year=ratio_history.start_fiscal_year,
            end_fiscal_year=ratio_history.end_fiscal_year,
            features=features,
        )
