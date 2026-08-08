from __future__ import annotations

from risk_platform.application.dto.financial_metrics_dto import FinancialMetricsResult
from risk_platform.application.use_cases.financial_ratio_service import FinancialRatioService
from risk_platform.domain.value_objects.canonical_financial_metric import CanonicalFinancialMetric


def _build_metrics_result(
    overrides: dict[CanonicalFinancialMetric, float | None],
) -> FinancialMetricsResult:
    metrics = {metric: None for metric in CanonicalFinancialMetric}
    metrics.update(overrides)
    return FinancialMetricsResult(
        ticker="AAPL",
        fiscal_year=2024,
        fiscal_period="FY",
        metrics=metrics,
    )


def test_net_profit_margin() -> None:
    result = FinancialRatioService.calculate_from_financial_metrics(
        _build_metrics_result(
            {
                CanonicalFinancialMetric.NET_INCOME: 250.0,
                CanonicalFinancialMetric.REVENUE: 1000.0,
            }
        )
    )

    assert result.ratios["net_profit_margin"] == 0.25


def test_operating_margin() -> None:
    result = FinancialRatioService.calculate_from_financial_metrics(
        _build_metrics_result(
            {
                CanonicalFinancialMetric.OPERATING_INCOME: 180.0,
                CanonicalFinancialMetric.REVENUE: 900.0,
            }
        )
    )

    assert result.ratios["operating_margin"] == 0.2


def test_roa() -> None:
    result = FinancialRatioService.calculate_from_financial_metrics(
        _build_metrics_result(
            {
                CanonicalFinancialMetric.NET_INCOME: 120.0,
                CanonicalFinancialMetric.TOTAL_ASSETS: 600.0,
            }
        )
    )

    assert result.ratios["roa"] == 0.2


def test_roe() -> None:
    result = FinancialRatioService.calculate_from_financial_metrics(
        _build_metrics_result(
            {
                CanonicalFinancialMetric.NET_INCOME: 90.0,
                CanonicalFinancialMetric.SHAREHOLDERS_EQUITY: 300.0,
            }
        )
    )

    assert result.ratios["roe"] == 0.3


def test_current_ratio() -> None:
    result = FinancialRatioService.calculate_from_financial_metrics(
        _build_metrics_result(
            {
                CanonicalFinancialMetric.CURRENT_ASSETS: 800.0,
                CanonicalFinancialMetric.CURRENT_LIABILITIES: 400.0,
            }
        )
    )

    assert result.ratios["current_ratio"] == 2.0


def test_cash_ratio() -> None:
    result = FinancialRatioService.calculate_from_financial_metrics(
        _build_metrics_result(
            {
                CanonicalFinancialMetric.CASH: 200.0,
                CanonicalFinancialMetric.CURRENT_LIABILITIES: 500.0,
            }
        )
    )

    assert result.ratios["cash_ratio"] == 0.4


def test_debt_to_equity() -> None:
    result = FinancialRatioService.calculate_from_financial_metrics(
        _build_metrics_result(
            {
                CanonicalFinancialMetric.LONG_TERM_DEBT: 150.0,
                CanonicalFinancialMetric.CURRENT_DEBT: 50.0,
                CanonicalFinancialMetric.SHAREHOLDERS_EQUITY: 400.0,
            }
        )
    )

    assert result.ratios["debt_to_equity"] == 0.5


def test_debt_to_assets() -> None:
    result = FinancialRatioService.calculate_from_financial_metrics(
        _build_metrics_result(
            {
                CanonicalFinancialMetric.LONG_TERM_DEBT: 180.0,
                CanonicalFinancialMetric.CURRENT_DEBT: 20.0,
                CanonicalFinancialMetric.TOTAL_ASSETS: 1000.0,
            }
        )
    )

    assert result.ratios["debt_to_assets"] == 0.2


def test_operating_cash_flow_margin() -> None:
    result = FinancialRatioService.calculate_from_financial_metrics(
        _build_metrics_result(
            {
                CanonicalFinancialMetric.OPERATING_CASH_FLOW: 300.0,
                CanonicalFinancialMetric.REVENUE: 1200.0,
            }
        )
    )

    assert result.ratios["operating_cash_flow_margin"] == 0.25


def test_free_cash_flow() -> None:
    result = FinancialRatioService.calculate_from_financial_metrics(
        _build_metrics_result(
            {
                CanonicalFinancialMetric.OPERATING_CASH_FLOW: 500.0,
                CanonicalFinancialMetric.CAPITAL_EXPENDITURES: 120.0,
            }
        )
    )

    assert result.ratios["free_cash_flow"] == 380.0


def test_operating_cash_flow_to_debt() -> None:
    result = FinancialRatioService.calculate_from_financial_metrics(
        _build_metrics_result(
            {
                CanonicalFinancialMetric.OPERATING_CASH_FLOW: 210.0,
                CanonicalFinancialMetric.LONG_TERM_DEBT: 150.0,
                CanonicalFinancialMetric.CURRENT_DEBT: 60.0,
            }
        )
    )

    assert result.ratios["operating_cash_flow_to_debt"] == 1.0


def test_returns_none_when_denominator_is_zero() -> None:
    result = FinancialRatioService.calculate_from_financial_metrics(
        _build_metrics_result(
            {
                CanonicalFinancialMetric.NET_INCOME: 100.0,
                CanonicalFinancialMetric.REVENUE: 0.0,
            }
        )
    )

    assert result.ratios["net_profit_margin"] is None


def test_returns_none_when_required_input_is_missing() -> None:
    result = FinancialRatioService.calculate_from_financial_metrics(
        _build_metrics_result(
            {
                CanonicalFinancialMetric.OPERATING_CASH_FLOW: 100.0,
                CanonicalFinancialMetric.LONG_TERM_DEBT: 50.0,
                # CURRENT_DEBT intentionally missing (None)
            }
        )
    )

    assert result.ratios["operating_cash_flow_to_debt"] is None


def test_returns_none_for_free_cash_flow_when_inputs_missing() -> None:
    result = FinancialRatioService.calculate_from_financial_metrics(
        _build_metrics_result(
            {
                CanonicalFinancialMetric.OPERATING_CASH_FLOW: 100.0,
            }
        )
    )

    assert result.ratios["free_cash_flow"] is None
