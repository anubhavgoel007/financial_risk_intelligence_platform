from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class SecFinancialStatementFact:
    """Persisted SEC fact row used for metric selection."""

    id: int
    ticker: str
    concept: str
    value: float
    unit: str
    fiscal_year: int
    fiscal_period: str
    filed_on: str | None
    statement_type: str
