from __future__ import annotations

from dataclasses import dataclass

from risk_platform.domain.value_objects.canonical_financial_metric import CanonicalFinancialMetric


@dataclass(slots=True, frozen=True)
class MetricConceptMapping:
    metric: CanonicalFinancialMetric
    statement_types: tuple[str, ...]
    concepts: tuple[str, ...]


METRIC_CONCEPT_MAPPINGS: tuple[MetricConceptMapping, ...] = (
    MetricConceptMapping(
        metric=CanonicalFinancialMetric.REVENUE,
        statement_types=("income_statement",),
        concepts=(
            "RevenueFromContractWithCustomerExcludingAssessedTax",
            "Revenues",
            "SalesRevenueNet",
        ),
    ),
    MetricConceptMapping(
        metric=CanonicalFinancialMetric.NET_INCOME,
        statement_types=("income_statement",),
        concepts=("NetIncomeLoss",),
    ),
    MetricConceptMapping(
        metric=CanonicalFinancialMetric.OPERATING_INCOME,
        statement_types=("income_statement",),
        concepts=("OperatingIncomeLoss",),
    ),
    MetricConceptMapping(
        metric=CanonicalFinancialMetric.OPERATING_EXPENSES,
        statement_types=("income_statement",),
        concepts=("OperatingExpenses",),
    ),
    MetricConceptMapping(
        metric=CanonicalFinancialMetric.GROSS_PROFIT,
        statement_types=("income_statement", "balance_sheet"),
        concepts=("GrossProfit",),
    ),
    MetricConceptMapping(
        metric=CanonicalFinancialMetric.INTEREST_EXPENSE,
        statement_types=("income_statement",),
        concepts=("InterestExpense", "InterestExpenseDebt"),
    ),
    MetricConceptMapping(
        metric=CanonicalFinancialMetric.INCOME_TAX_EXPENSE,
        statement_types=("income_statement",),
        concepts=("IncomeTaxExpenseBenefit",),
    ),
    MetricConceptMapping(
        metric=CanonicalFinancialMetric.TOTAL_ASSETS,
        statement_types=("balance_sheet",),
        concepts=("Assets",),
    ),
    MetricConceptMapping(
        metric=CanonicalFinancialMetric.CURRENT_ASSETS,
        statement_types=("balance_sheet",),
        concepts=("AssetsCurrent",),
    ),
    MetricConceptMapping(
        metric=CanonicalFinancialMetric.TOTAL_LIABILITIES,
        statement_types=("balance_sheet",),
        concepts=("Liabilities",),
    ),
    MetricConceptMapping(
        metric=CanonicalFinancialMetric.CURRENT_LIABILITIES,
        statement_types=("balance_sheet",),
        concepts=("LiabilitiesCurrent",),
    ),
    MetricConceptMapping(
        metric=CanonicalFinancialMetric.SHAREHOLDERS_EQUITY,
        statement_types=("balance_sheet",),
        concepts=("StockholdersEquity",),
    ),
    MetricConceptMapping(
        metric=CanonicalFinancialMetric.CASH,
        statement_types=("balance_sheet", "cash_flow"),
        concepts=("CashAndCashEquivalentsAtCarryingValue", "Cash"),
    ),
    MetricConceptMapping(
        metric=CanonicalFinancialMetric.ACCOUNTS_RECEIVABLE,
        statement_types=("balance_sheet",),
        concepts=("AccountsReceivableNetCurrent",),
    ),
    MetricConceptMapping(
        metric=CanonicalFinancialMetric.INVENTORY,
        statement_types=("balance_sheet",),
        concepts=("InventoryNet",),
    ),
    MetricConceptMapping(
        metric=CanonicalFinancialMetric.LONG_TERM_DEBT,
        statement_types=("balance_sheet",),
        concepts=("LongTermDebtNoncurrent", "LongTermDebt"),
    ),
    MetricConceptMapping(
        metric=CanonicalFinancialMetric.CURRENT_DEBT,
        statement_types=("balance_sheet",),
        concepts=("LongTermDebtCurrent",),
    ),
    MetricConceptMapping(
        metric=CanonicalFinancialMetric.OPERATING_CASH_FLOW,
        statement_types=("cash_flow", "balance_sheet"),
        concepts=(
            "NetCashProvidedByUsedInOperatingActivities",
            "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations",
        ),
    ),
    MetricConceptMapping(
        metric=CanonicalFinancialMetric.INVESTING_CASH_FLOW,
        statement_types=("cash_flow", "balance_sheet"),
        concepts=(
            "NetCashProvidedByUsedInInvestingActivities",
            "NetCashProvidedByUsedInInvestingActivitiesContinuingOperations",
        ),
    ),
    MetricConceptMapping(
        metric=CanonicalFinancialMetric.FINANCING_CASH_FLOW,
        statement_types=("cash_flow", "balance_sheet"),
        concepts=(
            "NetCashProvidedByUsedInFinancingActivities",
            "NetCashProvidedByUsedInFinancingActivitiesContinuingOperations",
        ),
    ),
    MetricConceptMapping(
        metric=CanonicalFinancialMetric.CAPITAL_EXPENDITURES,
        statement_types=("cash_flow", "balance_sheet"),
        concepts=("PaymentsToAcquirePropertyPlantAndEquipment",),
    ),
)
