from __future__ import annotations

import pytest

from risk_platform.application.dto.financial_metrics_dto import FinancialMetricsResult
from risk_platform.application.dto.financial_ratio_history_dto import (
    FinancialRatioHistoryPoint,
    FinancialRatioHistoryResult,
)
from risk_platform.application.use_cases.financial_ratio_service import FinancialRatioService
from risk_platform.application.use_cases.financial_risk_feature_service import FinancialRiskFeatureService
from risk_platform.domain.value_objects.canonical_financial_metric import CanonicalFinancialMetric


class FakeFinancialStatementService:
    def __init__(self, yearly_metrics: dict[int, dict[CanonicalFinancialMetric, float | None]]) -> None:
        self._yearly_metrics = yearly_metrics

    def get_financial_metrics(
        self,
        ticker: str,
        fiscal_year: int,
        fiscal_period: str,
    ) -> FinancialMetricsResult:
        metrics = {metric: None for metric in CanonicalFinancialMetric}
        metrics.update(self._yearly_metrics.get(fiscal_year, {}))
        return FinancialMetricsResult(
            ticker=ticker.strip().upper(),
            fiscal_year=fiscal_year,
            fiscal_period=fiscal_period.strip().upper(),
            metrics=metrics,
        )


def test_calculate_from_ratio_history_builds_one_risk_feature_set_per_point() -> None:
    ratio_history = FinancialRatioHistoryResult(
        ticker="AAPL",
        fiscal_period="FY",
        start_fiscal_year=2020,
        end_fiscal_year=2021,
        points=[
            FinancialRatioHistoryPoint(
                fiscal_year=2020,
                fiscal_period="FY",
                ratios={"current_ratio": 1.5, "net_profit_margin": 0.2},
                trend_features={"revenue_growth": None},
            ),
            FinancialRatioHistoryPoint(
                fiscal_year=2021,
                fiscal_period="FY",
                ratios={"current_ratio": 1.8, "net_profit_margin": 0.25},
                trend_features={"revenue_growth": 0.1},
            ),
        ],
    )

    result = FinancialRiskFeatureService.calculate_from_ratio_history(ratio_history)

    assert result.ticker == "AAPL"
    assert result.fiscal_period == "FY"
    assert result.start_fiscal_year == 2020
    assert result.end_fiscal_year == 2021
    assert len(result.features) == 2

    first, second = result.features
    assert first.fiscal_year == 2020
    assert first.liquidity["current_ratio"] == 1.5
    assert first.growth["revenue_growth"] is None
    assert first.profitability["net_profit_margin"] == 0.2

    assert second.fiscal_year == 2021
    assert second.liquidity["current_ratio"] == 1.8
    assert second.growth["revenue_growth"] == 0.1


def test_get_risk_feature_history_reuses_existing_historical_ratio_engine() -> None:
    yearly_metrics = {
        2020: {
            CanonicalFinancialMetric.REVENUE: 1000.0,
            CanonicalFinancialMetric.NET_INCOME: 100.0,
            CanonicalFinancialMetric.OPERATING_INCOME: 150.0,
            CanonicalFinancialMetric.TOTAL_ASSETS: 500.0,
            CanonicalFinancialMetric.SHAREHOLDERS_EQUITY: 200.0,
            CanonicalFinancialMetric.CURRENT_ASSETS: 200.0,
            CanonicalFinancialMetric.CURRENT_LIABILITIES: 100.0,
            CanonicalFinancialMetric.LONG_TERM_DEBT: 60.0,
            CanonicalFinancialMetric.CURRENT_DEBT: 40.0,
            CanonicalFinancialMetric.OPERATING_CASH_FLOW: 120.0,
            CanonicalFinancialMetric.CAPITAL_EXPENDITURES: 20.0,
        },
        2021: {
            CanonicalFinancialMetric.REVENUE: 1100.0,
            CanonicalFinancialMetric.NET_INCOME: 121.0,
            CanonicalFinancialMetric.OPERATING_INCOME: 176.0,
            CanonicalFinancialMetric.TOTAL_ASSETS: 550.0,
            CanonicalFinancialMetric.SHAREHOLDERS_EQUITY: 220.0,
            CanonicalFinancialMetric.CURRENT_ASSETS: 210.0,
            CanonicalFinancialMetric.CURRENT_LIABILITIES: 100.0,
            CanonicalFinancialMetric.LONG_TERM_DEBT: 70.0,
            CanonicalFinancialMetric.CURRENT_DEBT: 30.0,
            CanonicalFinancialMetric.OPERATING_CASH_FLOW: 132.0,
            CanonicalFinancialMetric.CAPITAL_EXPENDITURES: 22.0,
        },
    }

    ratio_service = FinancialRatioService(FakeFinancialStatementService(yearly_metrics))
    risk_feature_service = FinancialRiskFeatureService(ratio_service)

    result = risk_feature_service.get_risk_feature_history("AAPL", 2020, 2021, "FY")

    assert len(result.features) == 2
    second_year = result.features[1]

    assert second_year.profitability["net_profit_margin"] == 0.11
    assert second_year.profitability["operating_margin"] == 0.16
    assert second_year.liquidity["current_ratio"] == 2.1
    assert second_year.leverage["debt_to_equity"] == pytest.approx(0.4545454545)
    assert second_year.cash_flow["free_cash_flow"] == 110.0
    assert second_year.growth["revenue_growth"] == 0.1
    assert second_year.growth["net_income_growth"] == 0.21


def test_missing_ratios_and_trend_features_produce_none_risk_features_safely() -> None:
    yearly_metrics: dict[int, dict[CanonicalFinancialMetric, float | None]] = {2020: {}, 2021: {}}

    ratio_service = FinancialRatioService(FakeFinancialStatementService(yearly_metrics))
    risk_feature_service = FinancialRiskFeatureService(ratio_service)

    result = risk_feature_service.get_risk_feature_history("AAPL", 2020, 2021, "FY")

    for feature_set in result.features:
        assert all(value is None for value in feature_set.liquidity.values())
        assert all(value is None for value in feature_set.leverage.values())
        assert all(value is None for value in feature_set.profitability.values())
        assert all(value is None for value in feature_set.cash_flow.values())
        assert all(value is None for value in feature_set.growth.values())
