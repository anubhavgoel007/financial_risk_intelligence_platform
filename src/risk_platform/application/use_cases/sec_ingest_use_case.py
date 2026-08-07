from __future__ import annotations

from typing import Protocol

from risk_platform.domain.entities.sec_financial_statement import SecFinancialStatement


class SecStatementRepository(Protocol):
    def save_many(self, statements: list[SecFinancialStatement]) -> int:
        """Persist a batch of normalized statements."""


class IngestSecFinancialStatementsUseCase:
    """Orchestrates SEC EDGAR ingestion and persistence."""

    def __init__(self, client: object, repository: SecStatementRepository) -> None:
        self._client = client
        self._repository = repository

    def execute(self, ticker: str) -> int:
        statements = self._client.fetch_company_facts(ticker)
        if not statements:
            return 0
        persisted_count = self._repository.save_many(statements)
        return persisted_count if persisted_count is not None else len(statements)
