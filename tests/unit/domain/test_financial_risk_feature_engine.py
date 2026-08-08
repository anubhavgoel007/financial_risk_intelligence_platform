from __future__ import annotations

from risk_platform.domain.services.financial_risk_feature_engine import DeterministicRiskFeatureEngine


def test_calculate_groups_all_requested_features_by_category() -> None:
    ratios = {
        "current_ratio": 2.0,
        "cash_ratio": 0.4,
        "debt_to_equity": 0.5,
        "debt_to_assets": 0.2,
        "net_profit_margin": 0.25,
        "operating_margin": 0.2,
        "roa": 0.2,
        "roe": 0.3,
        "operating_cash_flow_margin": 0.25,
        "operating_cash_flow_to_debt": 1.0,
        "free_cash_flow": 380.0,
    }
    trend_features = {
        "current_ratio_change": 0.1,
        "debt_to_equity_change": -0.05,
        "net_profit_margin_change": 0.01,
        "operating_margin_change": 0.02,
        "free_cash_flow_growth": 0.1,
        "revenue_growth": 0.1,
        "net_income_growth": 0.21,
    }

    result = DeterministicRiskFeatureEngine.calculate(ratios, trend_features)

    assert result["liquidity"] == {
        "current_ratio": 2.0,
        "current_ratio_change": 0.1,
        "cash_ratio": 0.4,
    }
    assert result["leverage"] == {
        "debt_to_equity": 0.5,
        "debt_to_equity_change": -0.05,
        "debt_to_assets": 0.2,
    }
    assert result["profitability"] == {
        "net_profit_margin": 0.25,
        "net_profit_margin_change": 0.01,
        "operating_margin": 0.2,
        "operating_margin_change": 0.02,
        "roa": 0.2,
        "roe": 0.3,
    }
    assert result["cash_flow"] == {
        "operating_cash_flow_margin": 0.25,
        "operating_cash_flow_to_debt": 1.0,
        "free_cash_flow": 380.0,
        "free_cash_flow_growth": 0.1,
    }
    assert result["growth"] == {
        "revenue_growth": 0.1,
        "net_income_growth": 0.21,
    }


def test_calculate_handles_missing_ratio_and_trend_keys_safely() -> None:
    result = DeterministicRiskFeatureEngine.calculate({}, {})

    for category in ("liquidity", "leverage", "profitability", "cash_flow", "growth"):
        assert all(value is None for value in result[category].values())


def test_calculate_handles_none_values_without_raising() -> None:
    ratios = {"current_ratio": None, "debt_to_equity": None, "net_profit_margin": None}
    trend_features = {"revenue_growth": None, "current_ratio_change": None}

    result = DeterministicRiskFeatureEngine.calculate(ratios, trend_features)

    assert result["liquidity"]["current_ratio"] is None
    assert result["liquidity"]["current_ratio_change"] is None
    assert result["growth"]["revenue_growth"] is None
