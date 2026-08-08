from __future__ import annotations

from enum import StrEnum


class CanonicalFinancialMetric(StrEnum):
    REVENUE = "revenue"
    NET_INCOME = "net_income"
    OPERATING_INCOME = "operating_income"
    OPERATING_EXPENSES = "operating_expenses"
    GROSS_PROFIT = "gross_profit"
    INTEREST_EXPENSE = "interest_expense"
    INCOME_TAX_EXPENSE = "income_tax_expense"
    TOTAL_ASSETS = "total_assets"
    CURRENT_ASSETS = "current_assets"
    TOTAL_LIABILITIES = "total_liabilities"
    CURRENT_LIABILITIES = "current_liabilities"
    SHAREHOLDERS_EQUITY = "shareholders_equity"
    CASH = "cash"
    ACCOUNTS_RECEIVABLE = "accounts_receivable"
    INVENTORY = "inventory"
    LONG_TERM_DEBT = "long_term_debt"
    CURRENT_DEBT = "current_debt"
    OPERATING_CASH_FLOW = "operating_cash_flow"
    INVESTING_CASH_FLOW = "investing_cash_flow"
    FINANCING_CASH_FLOW = "financing_cash_flow"
    CAPITAL_EXPENDITURES = "capital_expenditures"
