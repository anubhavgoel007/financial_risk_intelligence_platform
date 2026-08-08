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
from risk_platform.infrastructure.database.repositories.sec_statement_repository import PostgresSecStatementRepository


def main() -> None:
    ticker = os.getenv("DEMO_TICKER", "AAPL")
    fiscal_year = int(os.getenv("DEMO_FISCAL_YEAR", "2024"))
    fiscal_period = os.getenv("DEMO_FISCAL_PERIOD", "FY")
    database_url = os.getenv("DATABASE_URL")

    repository = PostgresSecStatementRepository(database_url=database_url)
    service = FinancialStatementService(repository)
    ratio_service = FinancialRatioService(service)

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


if __name__ == "__main__":
    main()
