from __future__ import annotations

import asyncio
import os
from typing import Any

import asyncpg

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
