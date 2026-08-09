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

from risk_platform.application.use_cases.financial_ratio_service import FinancialRatioService
from risk_platform.application.use_cases.financial_risk_feature_service import FinancialRiskFeatureService
from risk_platform.application.use_cases.financial_risk_training_dataset_service import (
    FinancialRiskTrainingDatasetService,
)
from risk_platform.application.use_cases.financial_statement_service import FinancialStatementService
from risk_platform.infrastructure.database.repositories.sec_statement_repository import PostgresSecStatementRepository


def main() -> None:
    fiscal_period = os.getenv("DEMO_DATASET_FISCAL_PERIOD", "FY")
    start_fiscal_year = int(os.getenv("DEMO_DATASET_START_YEAR", "2020"))
    end_fiscal_year = int(os.getenv("DEMO_DATASET_END_YEAR", "2024"))
    max_tickers = int(os.getenv("DEMO_DATASET_MAX_TICKERS", "3"))
    min_years = int(os.getenv("DEMO_DATASET_MIN_YEARS", "1"))
    database_url = os.getenv("DATABASE_URL")

    repository = PostgresSecStatementRepository(database_url=database_url)
    statement_service = FinancialStatementService(repository)
    ratio_service = FinancialRatioService(statement_service)
    risk_feature_service = FinancialRiskFeatureService(ratio_service)
    dataset_service = FinancialRiskTrainingDatasetService(risk_feature_service)

    tickers = repository.list_available_tickers(
        fiscal_period=fiscal_period,
        min_distinct_years=min_years,
        limit=max_tickers,
    )
    if not tickers:
        print("No eligible tickers found for dataset demo.")
        return

    dataset = dataset_service.build_dataset(
        tickers=tickers,
        start_fiscal_year=start_fiscal_year,
        end_fiscal_year=end_fiscal_year,
        fiscal_period=fiscal_period,
    )

    print("Deterministic risk training dataset demo")
    print(f"fiscal_period={dataset.fiscal_period}")
    print(f"tickers={', '.join(tickers)}")
    print(f"years={start_fiscal_year}-{end_fiscal_year}")
    print(f"rows={len(dataset.rows)}")
    print("-" * 120)
    print(
        f"{'ticker':<10} {'year':<6} {'curr_ratio':>11} {'d/e':>9} {'npm':>9} "
        f"{'op_margin':>10} {'rev_growth':>11} {'fcf_growth':>11} {'target_label':>13}"
    )
    print("-" * 120)

    def fmt(value: float | int | str | None) -> str:
        if value is None:
            return "N/A"
        if isinstance(value, float):
            return f"{value:.4f}"
        return str(value)

    for row in dataset.rows:
        print(
            f"{row.ticker:<10} {row.fiscal_year:<6} {fmt(row.current_ratio):>11} {fmt(row.debt_to_equity):>9} "
            f"{fmt(row.net_profit_margin):>9} {fmt(row.operating_margin):>10} {fmt(row.revenue_growth):>11} "
            f"{fmt(row.free_cash_flow_growth):>11} {fmt(row.target_label):>13}"
        )


if __name__ == "__main__":
    main()
