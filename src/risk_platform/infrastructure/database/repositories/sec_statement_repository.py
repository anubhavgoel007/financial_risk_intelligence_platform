from __future__ import annotations

import asyncio
import os
from typing import Any

import asyncpg

from risk_platform.domain.entities.sec_financial_statement_fact import SecFinancialStatementFact
from risk_platform.domain.entities.sec_financial_statement import SecFinancialStatement


class PostgresSecStatementRepository:
    """Persists normalized SEC facts into PostgreSQL, or falls back to memory when unavailable."""

    def __init__(self, database_url: str | None = None) -> None:
        raw_url = database_url or os.getenv("DATABASE_URL", "")
        self._database_url = self._to_asyncpg_dsn(raw_url)
        self._memory_store: list[SecFinancialStatement] = []

    @staticmethod
    def _to_asyncpg_dsn(url: str) -> str:
        # asyncpg.connect() requires a plain "postgresql://" DSN; SQLAlchemy-style
        # "postgresql+asyncpg://" URLs (as used in .env) must have the "+asyncpg" stripped.
        return url.replace("postgresql+asyncpg://", "postgresql://", 1)

    def save_many(self, statements: list[SecFinancialStatement]) -> int:
        if not self._database_url:
            self._memory_store.extend(statements)
            return len(statements)
        return asyncio.run(self._save_many(statements))

    def get_facts_for_period(
        self,
        *,
        ticker: str,
        fiscal_year: int,
        fiscal_period: str,
        statement_type: str,
        concepts: list[str],
    ) -> list[SecFinancialStatementFact]:
        if not concepts:
            return []
        if not self._database_url:
            return self._get_facts_for_period_in_memory(
                ticker=ticker,
                fiscal_year=fiscal_year,
                fiscal_period=fiscal_period,
                statement_type=statement_type,
                concepts=concepts,
            )
        return asyncio.run(
            self._get_facts_for_period(
                ticker=ticker,
                fiscal_year=fiscal_year,
                fiscal_period=fiscal_period,
                statement_type=statement_type,
                concepts=concepts,
            )
        )

    def _get_facts_for_period_in_memory(
        self,
        *,
        ticker: str,
        fiscal_year: int,
        fiscal_period: str,
        statement_type: str,
        concepts: list[str],
    ) -> list[SecFinancialStatementFact]:
        normalized_ticker = ticker.upper()
        normalized_period = fiscal_period.upper()
        concept_set = set(concepts)
        results: list[SecFinancialStatementFact] = []
        for index, statement in enumerate(self._memory_store, start=1):
            if statement.fiscal_year is None or statement.fiscal_period is None:
                continue
            if statement.ticker.upper() != normalized_ticker:
                continue
            if statement.fiscal_year != fiscal_year:
                continue
            if statement.fiscal_period.upper() != normalized_period:
                continue
            if statement.statement_type != statement_type:
                continue
            if statement.concept not in concept_set:
                continue

            results.append(
                SecFinancialStatementFact(
                    id=index,
                    ticker=statement.ticker,
                    concept=statement.concept,
                    value=statement.value,
                    unit=statement.unit,
                    fiscal_year=statement.fiscal_year,
                    fiscal_period=statement.fiscal_period,
                    filed_on=statement.filed_on,
                    statement_type=statement.statement_type,
                )
            )
        return results

    async def _save_many(self, statements: list[SecFinancialStatement]) -> int:
        conn: asyncpg.Connection = await asyncpg.connect(self._database_url)
        try:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sec_financial_statements (
                    id SERIAL PRIMARY KEY,
                    ticker TEXT NOT NULL,
                    cik TEXT NOT NULL,
                    company_name TEXT NOT NULL,
                    concept TEXT NOT NULL,
                    value DOUBLE PRECISION NOT NULL,
                    unit TEXT NOT NULL,
                    fiscal_year INTEGER,
                    fiscal_period TEXT,
                    filed_on TEXT,
                    statement_type TEXT NOT NULL,
                    source TEXT NOT NULL
                )
                """
            )
            for statement in statements:
                await conn.execute(
                    """
                    INSERT INTO sec_financial_statements (
                        ticker, cik, company_name, concept, value, unit,
                        fiscal_year, fiscal_period, filed_on, statement_type, source
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                    """,
                    statement.ticker,
                    statement.cik,
                    statement.company_name,
                    statement.concept,
                    statement.value,
                    statement.unit,
                    statement.fiscal_year,
                    statement.fiscal_period,
                    statement.filed_on,
                    statement.statement_type,
                    statement.source,
                )
            return len(statements)
        finally:
            await conn.close()

    async def _get_facts_for_period(
        self,
        *,
        ticker: str,
        fiscal_year: int,
        fiscal_period: str,
        statement_type: str,
        concepts: list[str],
    ) -> list[SecFinancialStatementFact]:
        conn: asyncpg.Connection = await asyncpg.connect(self._database_url)
        try:
            rows = await conn.fetch(
                """
                SELECT id, ticker, concept, value, unit, fiscal_year, fiscal_period, filed_on, statement_type
                FROM sec_financial_statements
                WHERE UPPER(ticker) = UPPER($1)
                  AND fiscal_year = $2
                  AND fiscal_period = $3
                  AND fiscal_year IS NOT NULL
                  AND fiscal_period IS NOT NULL
                  AND statement_type = $4
                  AND concept = ANY($5::text[])
                """,
                ticker,
                fiscal_year,
                fiscal_period,
                statement_type,
                concepts,
            )
            return [
                SecFinancialStatementFact(
                    id=int(row["id"]),
                    ticker=str(row["ticker"]),
                    concept=str(row["concept"]),
                    value=float(row["value"]),
                    unit=str(row["unit"]),
                    fiscal_year=int(row["fiscal_year"]),
                    fiscal_period=str(row["fiscal_period"]),
                    filed_on=str(row["filed_on"]) if row["filed_on"] is not None else None,
                    statement_type=str(row["statement_type"]),
                )
                for row in rows
            ]
        finally:
            await conn.close()
