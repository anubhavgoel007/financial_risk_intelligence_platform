from __future__ import annotations

import pytest

from risk_platform.application.dto.risk_feature_set_dto import RiskFeatureHistoryResult, RiskFeatureSet
from risk_platform.application.use_cases.financial_risk_training_dataset_service import (
    FinancialRiskTrainingDatasetService,
)


class FakeRiskFeatureService:
    def __init__(self, by_ticker: dict[str, list[RiskFeatureSet]]) -> None:
        self._by_ticker = by_ticker

    def get_risk_feature_history(
        self,
        ticker: str,
        start_fiscal_year: int,
        end_fiscal_year: int,
        fiscal_period: str = "FY",
    ) -> RiskFeatureHistoryResult:
        ticker_key = ticker.strip().upper()
        selected = [
            row
            for row in self._by_ticker.get(ticker_key, [])
            if start_fiscal_year <= row.fiscal_year <= end_fiscal_year
            and row.fiscal_period == fiscal_period
        ]
        return RiskFeatureHistoryResult(
            ticker=ticker_key,
            fiscal_period=fiscal_period,
            start_fiscal_year=start_fiscal_year,
            end_fiscal_year=end_fiscal_year,
            features=selected,
        )


def _risk_feature_set(
    *,
    ticker: str,
    fiscal_year: int,
    fiscal_period: str,
    current_ratio: float | None,
    current_ratio_change: float | None,
    cash_ratio: float | None,
    debt_to_equity: float | None,
    debt_to_equity_change: float | None,
    debt_to_assets: float | None,
    net_profit_margin: float | None,
    net_profit_margin_change: float | None,
    operating_margin: float | None,
    operating_margin_change: float | None,
    roa: float | None,
    roe: float | None,
    operating_cash_flow_margin: float | None,
    operating_cash_flow_to_debt: float | None,
    free_cash_flow: float | None,
    free_cash_flow_growth: float | None,
    revenue_growth: float | None,
    net_income_growth: float | None,
) -> RiskFeatureSet:
    return RiskFeatureSet(
        ticker=ticker,
        fiscal_year=fiscal_year,
        fiscal_period=fiscal_period,
        liquidity={
            "current_ratio": current_ratio,
            "current_ratio_change": current_ratio_change,
            "cash_ratio": cash_ratio,
        },
        leverage={
            "debt_to_equity": debt_to_equity,
            "debt_to_equity_change": debt_to_equity_change,
            "debt_to_assets": debt_to_assets,
        },
        profitability={
            "net_profit_margin": net_profit_margin,
            "net_profit_margin_change": net_profit_margin_change,
            "operating_margin": operating_margin,
            "operating_margin_change": operating_margin_change,
            "roa": roa,
            "roe": roe,
        },
        cash_flow={
            "operating_cash_flow_margin": operating_cash_flow_margin,
            "operating_cash_flow_to_debt": operating_cash_flow_to_debt,
            "free_cash_flow": free_cash_flow,
            "free_cash_flow_growth": free_cash_flow_growth,
        },
        growth={
            "revenue_growth": revenue_growth,
            "net_income_growth": net_income_growth,
        },
    )


def test_build_dataset_aligns_rows_by_ticker_and_fiscal_year() -> None:
    service = FinancialRiskTrainingDatasetService(
        FakeRiskFeatureService(
            {
                "AAPL": [
                    _risk_feature_set(
                        ticker="AAPL",
                        fiscal_year=2021,
                        fiscal_period="FY",
                        current_ratio=1.1,
                        current_ratio_change=0.1,
                        cash_ratio=0.2,
                        debt_to_equity=1.5,
                        debt_to_equity_change=0.2,
                        debt_to_assets=0.3,
                        net_profit_margin=0.25,
                        net_profit_margin_change=0.01,
                        operating_margin=0.29,
                        operating_margin_change=0.02,
                        roa=0.2,
                        roe=1.1,
                        operating_cash_flow_margin=0.28,
                        operating_cash_flow_to_debt=0.9,
                        free_cash_flow=100.0,
                        free_cash_flow_growth=0.1,
                        revenue_growth=0.3,
                        net_income_growth=0.2,
                    ),
                    _risk_feature_set(
                        ticker="AAPL",
                        fiscal_year=2020,
                        fiscal_period="FY",
                        current_ratio=1.0,
                        current_ratio_change=None,
                        cash_ratio=0.3,
                        debt_to_equity=1.4,
                        debt_to_equity_change=None,
                        debt_to_assets=0.32,
                        net_profit_margin=0.2,
                        net_profit_margin_change=None,
                        operating_margin=0.24,
                        operating_margin_change=None,
                        roa=0.18,
                        roe=0.9,
                        operating_cash_flow_margin=0.29,
                        operating_cash_flow_to_debt=0.8,
                        free_cash_flow=80.0,
                        free_cash_flow_growth=None,
                        revenue_growth=None,
                        net_income_growth=None,
                    ),
                ],
                "MSFT": [
                    _risk_feature_set(
                        ticker="MSFT",
                        fiscal_year=2021,
                        fiscal_period="FY",
                        current_ratio=1.9,
                        current_ratio_change=0.2,
                        cash_ratio=0.5,
                        debt_to_equity=0.7,
                        debt_to_equity_change=-0.1,
                        debt_to_assets=0.2,
                        net_profit_margin=0.3,
                        net_profit_margin_change=0.02,
                        operating_margin=0.33,
                        operating_margin_change=0.01,
                        roa=0.15,
                        roe=0.4,
                        operating_cash_flow_margin=0.35,
                        operating_cash_flow_to_debt=1.3,
                        free_cash_flow=150.0,
                        free_cash_flow_growth=0.05,
                        revenue_growth=0.12,
                        net_income_growth=0.1,
                    )
                ],
            }
        )
    )

    dataset = service.build_dataset(
        tickers=["msft", "aapl"],
        start_fiscal_year=2020,
        end_fiscal_year=2021,
        fiscal_period="FY",
    )

    assert dataset.fiscal_period == "FY"
    assert [(row.ticker, row.fiscal_year) for row in dataset.rows] == [
        ("AAPL", 2020),
        ("AAPL", 2021),
        ("MSFT", 2021),
    ]
    assert all(row.target_label is None for row in dataset.rows)


def test_build_dataset_applies_target_label_placeholder_without_inventing() -> None:
    service = FinancialRiskTrainingDatasetService(
        FakeRiskFeatureService(
            {
                "AAPL": [
                    _risk_feature_set(
                        ticker="AAPL",
                        fiscal_year=2020,
                        fiscal_period="FY",
                        current_ratio=1.0,
                        current_ratio_change=None,
                        cash_ratio=0.3,
                        debt_to_equity=1.4,
                        debt_to_equity_change=None,
                        debt_to_assets=0.32,
                        net_profit_margin=0.2,
                        net_profit_margin_change=None,
                        operating_margin=0.24,
                        operating_margin_change=None,
                        roa=0.18,
                        roe=0.9,
                        operating_cash_flow_margin=0.29,
                        operating_cash_flow_to_debt=0.8,
                        free_cash_flow=80.0,
                        free_cash_flow_growth=None,
                        revenue_growth=None,
                        net_income_growth=None,
                    ),
                    _risk_feature_set(
                        ticker="AAPL",
                        fiscal_year=2021,
                        fiscal_period="FY",
                        current_ratio=1.1,
                        current_ratio_change=0.1,
                        cash_ratio=0.2,
                        debt_to_equity=1.5,
                        debt_to_equity_change=0.2,
                        debt_to_assets=0.3,
                        net_profit_margin=0.25,
                        net_profit_margin_change=0.01,
                        operating_margin=0.29,
                        operating_margin_change=0.02,
                        roa=0.2,
                        roe=1.1,
                        operating_cash_flow_margin=0.28,
                        operating_cash_flow_to_debt=0.9,
                        free_cash_flow=100.0,
                        free_cash_flow_growth=0.1,
                        revenue_growth=0.3,
                        net_income_growth=0.2,
                    ),
                ],
            }
        )
    )

    dataset = service.build_dataset(
        tickers=["AAPL"],
        start_fiscal_year=2020,
        end_fiscal_year=2021,
        fiscal_period="FY",
        target_labels={("AAPL", 2021): 1},
    )

    assert dataset.rows[0].target_label is None
    assert dataset.rows[1].target_label == 1


def test_build_dataset_preserves_missing_feature_values_explicitly() -> None:
    service = FinancialRiskTrainingDatasetService(
        FakeRiskFeatureService(
            {
                "AAPL": [
                    _risk_feature_set(
                        ticker="AAPL",
                        fiscal_year=2020,
                        fiscal_period="FY",
                        current_ratio=None,
                        current_ratio_change=None,
                        cash_ratio=None,
                        debt_to_equity=None,
                        debt_to_equity_change=None,
                        debt_to_assets=None,
                        net_profit_margin=None,
                        net_profit_margin_change=None,
                        operating_margin=None,
                        operating_margin_change=None,
                        roa=None,
                        roe=None,
                        operating_cash_flow_margin=None,
                        operating_cash_flow_to_debt=None,
                        free_cash_flow=None,
                        free_cash_flow_growth=None,
                        revenue_growth=None,
                        net_income_growth=None,
                    ),
                ]
            }
        )
    )

    dataset = service.build_dataset(
        tickers=["AAPL"],
        start_fiscal_year=2020,
        end_fiscal_year=2020,
    )

    row = dataset.rows[0]
    assert row.current_ratio is None
    assert row.revenue_growth is None
    assert row.target_label is None


def test_build_dataset_validates_fiscal_year_range() -> None:
    service = FinancialRiskTrainingDatasetService(FakeRiskFeatureService({}))

    with pytest.raises(ValueError):
        service.build_dataset(tickers=["AAPL"], start_fiscal_year=0, end_fiscal_year=2024)

    with pytest.raises(ValueError):
        service.build_dataset(tickers=["AAPL"], start_fiscal_year=2025, end_fiscal_year=2024)
