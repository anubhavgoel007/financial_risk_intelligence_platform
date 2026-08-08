from __future__ import annotations

import pytest

from risk_platform.application.dto.financial_metrics_dto import FinancialMetricsResult
from risk_platform.application.use_cases.financial_ratio_service import FinancialRatioService
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


def test_historical_ratios_and_trend_features_for_consecutive_years() -> None:
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

    service = FinancialRatioService(FakeFinancialStatementService(yearly_metrics))
    history = service.get_historical_financial_ratios("AAPL", 2020, 2021, "FY")

    assert history.ticker == "AAPL"
    assert history.fiscal_period == "FY"
    assert len(history.points) == 2

    first_year = history.points[0]
    second_year = history.points[1]

    assert first_year.fiscal_year == 2020
    assert first_year.trend_features["revenue_growth"] is None

    assert second_year.fiscal_year == 2021
    assert second_year.ratios["net_profit_margin"] == 0.11
    assert second_year.ratios["operating_margin"] == 0.16
    assert second_year.ratios["debt_to_equity"] == pytest.approx(0.4545454545)
    assert second_year.ratios["current_ratio"] == 2.1
    assert second_year.ratios["free_cash_flow"] == 110.0

    assert second_year.trend_features["revenue_growth"] == 0.1
    assert second_year.trend_features["net_income_growth"] == 0.21
    assert second_year.trend_features["operating_margin_change"] == pytest.approx(0.01)
    assert second_year.trend_features["net_profit_margin_change"] == pytest.approx(0.01)
    assert second_year.trend_features["debt_to_equity_change"] == pytest.approx(-0.0454545455)
    assert second_year.trend_features["current_ratio_change"] == pytest.approx(0.1)
    assert second_year.trend_features["operating_cash_flow_growth"] == 0.1
    assert second_year.trend_features["free_cash_flow_growth"] == 0.1


def test_growth_is_none_when_previous_year_value_is_missing() -> None:
    yearly_metrics = {
        2020: {
            CanonicalFinancialMetric.REVENUE: 1000.0,
            CanonicalFinancialMetric.NET_INCOME: 100.0,
        },
        2021: {
            CanonicalFinancialMetric.REVENUE: None,
            CanonicalFinancialMetric.NET_INCOME: None,
        },
        2022: {
            CanonicalFinancialMetric.REVENUE: 1300.0,
            CanonicalFinancialMetric.NET_INCOME: 130.0,
        },
    }

    service = FinancialRatioService(FakeFinancialStatementService(yearly_metrics))
    history = service.get_historical_financial_ratios("AAPL", 2020, 2022, "FY")

    year_2022 = history.points[2]
    assert year_2022.fiscal_year == 2022
    assert year_2022.trend_features["revenue_growth"] is None
    assert year_2022.trend_features["net_income_growth"] is None


def test_growth_is_none_when_previous_year_value_is_zero() -> None:
    yearly_metrics = {
        2023: {
            CanonicalFinancialMetric.OPERATING_CASH_FLOW: 0.0,
            CanonicalFinancialMetric.CAPITAL_EXPENDITURES: 0.0,
        },
        2024: {
            CanonicalFinancialMetric.OPERATING_CASH_FLOW: 100.0,
            CanonicalFinancialMetric.CAPITAL_EXPENDITURES: 20.0,
        },
    }

    service = FinancialRatioService(FakeFinancialStatementService(yearly_metrics))
    history = service.get_historical_financial_ratios("AAPL", 2023, 2024, "FY")

    year_2024 = history.points[1]
    assert year_2024.trend_features["operating_cash_flow_growth"] is None
    assert year_2024.trend_features["free_cash_flow_growth"] is None


def test_missing_years_are_not_interpolated_and_produce_none_features() -> None:
    yearly_metrics = {
        2020: {
            CanonicalFinancialMetric.REVENUE: 1000.0,
        },
        2022: {
            CanonicalFinancialMetric.REVENUE: 1200.0,
        },
    }

    service = FinancialRatioService(FakeFinancialStatementService(yearly_metrics))
    history = service.get_historical_financial_ratios("AAPL", 2020, 2022, "FY")

    assert [point.fiscal_year for point in history.points] == [2020, 2021, 2022]
    assert history.points[1].ratios["net_profit_margin"] is None
    assert history.points[2].trend_features["revenue_growth"] is None


def test_validation_rules_for_year_range() -> None:
    service = FinancialRatioService(FakeFinancialStatementService({}))

    with pytest.raises(ValueError):
        service.get_historical_financial_ratios("AAPL", 0, 2024, "FY")

    with pytest.raises(ValueError):
        service.get_historical_financial_ratios("AAPL", 2025, 2024, "FY")
