from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

load_dotenv(ROOT / ".env")
load_dotenv(ROOT / ".env.local", override=False)

from risk_platform.application.use_cases.financial_statement_service import FinancialStatementService
from risk_platform.application.use_cases.financial_ratio_service import FinancialRatioService
from risk_platform.application.use_cases.financial_risk_feature_service import FinancialRiskFeatureService
from risk_platform.infrastructure.database.repositories.sec_statement_repository import PostgresSecStatementRepository


def main() -> None:
    ticker = os.getenv("DEMO_TICKER", "AAPL")
    fiscal_year = int(os.getenv("DEMO_FISCAL_YEAR", "2024"))
    fiscal_period = os.getenv("DEMO_FISCAL_PERIOD", "FY")
    history_start_year = int(os.getenv("DEMO_HISTORY_START_YEAR", "2020"))
    history_end_year = int(os.getenv("DEMO_HISTORY_END_YEAR", "2024"))
    database_url = os.getenv("DATABASE_URL")

    repository = PostgresSecStatementRepository(database_url=database_url)
    service = FinancialStatementService(repository)
    ratio_service = FinancialRatioService(service)
    risk_feature_service = FinancialRiskFeatureService(ratio_service)

    result = service.get_financial_metrics(ticker, fiscal_year, fiscal_period)
    ratio_result = ratio_service.calculate_from_financial_metrics(result)

    print(f"Financial metrics for {result.ticker} {result.fiscal_period} {result.fiscal_year}")
    print("-" * 48)
    for metric, value in result.metrics.items():
        display_value = "N/A" if value is None else f"{value:,.2f}"
        print(f"{metric.value:<24} {display_value:>20}")

    unavailable = [metric.value for metric, value in result.metrics.items() if value is None]
    if unavailable:
        print("-" * 48)
        print(f"Unavailable metrics ({len(unavailable)}): {', '.join(unavailable)}")

    print("\nDeterministic financial ratios")
    print("-" * 48)
    for ratio_name, value in ratio_result.ratios.items():
        display_value = "N/A" if value is None else f"{value:,.4f}"
        print(f"{ratio_name:<32} {display_value:>12}")

    unavailable_ratios = [name for name, value in ratio_result.ratios.items() if value is None]
    if unavailable_ratios:
        print("-" * 48)
        print(f"Unavailable ratios ({len(unavailable_ratios)}): {', '.join(unavailable_ratios)}")

    history_result = ratio_service.get_historical_financial_ratios(
        ticker=ticker,
        start_fiscal_year=history_start_year,
        end_fiscal_year=history_end_year,
        fiscal_period=fiscal_period,
    )

    print(f"\nHistorical deterministic ratios for {history_result.ticker} {history_result.fiscal_period}")
    print(f"Fiscal years: {history_result.start_fiscal_year}-{history_result.end_fiscal_year}")
    print("-" * 92)
    print(
        f"{'Year':<6} {'NPM':>10} {'OpMargin':>10} {'D/E':>10} {'CurrRatio':>10} {'RevGrow':>10} {'FCFGrow':>10}"
    )
    print("-" * 92)
    for point in history_result.points:
        net_profit_margin = point.ratios.get("net_profit_margin")
        operating_margin = point.ratios.get("operating_margin")
        debt_to_equity = point.ratios.get("debt_to_equity")
        current_ratio = point.ratios.get("current_ratio")
        revenue_growth = point.trend_features.get("revenue_growth")
        free_cash_flow_growth = point.trend_features.get("free_cash_flow_growth")

        def fmt(value: float | None) -> str:
            return "N/A" if value is None else f"{value:.4f}"

        print(
            f"{point.fiscal_year:<6} {fmt(net_profit_margin):>10} {fmt(operating_margin):>10} "
            f"{fmt(debt_to_equity):>10} {fmt(current_ratio):>10} {fmt(revenue_growth):>10} "
            f"{fmt(free_cash_flow_growth):>10}"
        )

    print("-" * 92)
    print("Trend feature keys per year:")
    print(
        "revenue_growth, net_income_growth, operating_margin_change, "
        "net_profit_margin_change, debt_to_equity_change, current_ratio_change, "
        "operating_cash_flow_growth, free_cash_flow_growth"
    )

    risk_feature_history = risk_feature_service.get_risk_feature_history(
        ticker=ticker,
        start_fiscal_year=history_start_year,
        end_fiscal_year=history_end_year,
        fiscal_period=fiscal_period,
    )

    def fmt(value: float | None) -> str:
        return "N/A" if value is None else f"{value:.4f}"

    print(f"\nDeterministic risk features for {risk_feature_history.ticker} {risk_feature_history.fiscal_period}")
    print(f"Fiscal years: {risk_feature_history.start_fiscal_year}-{risk_feature_history.end_fiscal_year}")
    for feature_set in risk_feature_history.features:
        print("-" * 92)
        print(f"FY{feature_set.fiscal_year}")
        for category in ("liquidity", "leverage", "profitability", "cash_flow", "growth"):
            category_values = getattr(feature_set, category)
            rendered = ", ".join(f"{name}={fmt(value)}" for name, value in category_values.items())
            print(f"  {category:<14} {rendered}")


if __name__ == "__main__":
    main()
