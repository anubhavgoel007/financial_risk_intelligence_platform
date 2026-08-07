from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class SecFinancialStatement:
    """Normalized SEC financial statement fact for persistence and downstream use."""

    ticker: str
    cik: str
    company_name: str
    concept: str
    value: float
    unit: str
    fiscal_year: int | None = None
    fiscal_period: str | None = None
    filed_on: str | None = None
    statement_type: str = "other"
    source: str = "sec_edgar"

    def to_dict(self) -> dict[str, object]:
        return {
            "ticker": self.ticker,
            "cik": self.cik,
            "company_name": self.company_name,
            "concept": self.concept,
            "value": self.value,
            "unit": self.unit,
            "fiscal_year": self.fiscal_year,
            "fiscal_period": self.fiscal_period,
            "filed_on": self.filed_on,
            "statement_type": self.statement_type,
            "source": self.source,
        }
