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

    def list_available_tickers(
        self,
        *,
        fiscal_period: str = "FY",
        min_distinct_years: int = 1,
        limit: int = 20,
    ) -> list[str]:
        if min_distinct_years <= 0:
            raise ValueError("min_distinct_years must be a positive integer")
        if limit <= 0:
            raise ValueError("limit must be a positive integer")

        normalized_period = fiscal_period.upper()
        if not self._database_url:
            return self._list_available_tickers_in_memory(
                fiscal_period=normalized_period,
                min_distinct_years=min_distinct_years,
                limit=limit,
            )
        return asyncio.run(
            self._list_available_tickers(
                fiscal_period=normalized_period,
                min_distinct_years=min_distinct_years,
                limit=limit,
            )
        )

    def list_available_fiscal_years_for_ticker(
        self,
        *,
        ticker: str,
        fiscal_period: str = "FY",
    ) -> list[int]:
        normalized_ticker = ticker.strip().upper()
        normalized_period = fiscal_period.upper()
        if not normalized_ticker:
            return []

        if not self._database_url:
            return self._list_available_fiscal_years_for_ticker_in_memory(
                ticker=normalized_ticker,
                fiscal_period=normalized_period,
            )
        return asyncio.run(
            self._list_available_fiscal_years_for_ticker(
                ticker=normalized_ticker,
                fiscal_period=normalized_period,
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

    def _list_available_tickers_in_memory(
        self,
        *,
        fiscal_period: str,
        min_distinct_years: int,
        limit: int,
    ) -> list[str]:
        by_ticker: dict[str, set[int]] = {}
        for statement in self._memory_store:
            if statement.fiscal_year is None or statement.fiscal_period is None:
                continue
            if statement.fiscal_period.upper() != fiscal_period:
                continue
            ticker = statement.ticker.upper()
            by_ticker.setdefault(ticker, set()).add(statement.fiscal_year)

        eligible = [
            ticker
            for ticker, years in by_ticker.items()
            if len(years) >= min_distinct_years
        ]
        eligible.sort()
        return eligible[:limit]

    def _list_available_fiscal_years_for_ticker_in_memory(
        self,
        *,
        ticker: str,
        fiscal_period: str,
    ) -> list[int]:
        years = {
            statement.fiscal_year
            for statement in self._memory_store
            if statement.fiscal_year is not None
            and statement.fiscal_period is not None
            and statement.ticker.upper() == ticker
            and statement.fiscal_period.upper() == fiscal_period
        }
        return sorted(years)

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
            await conn.execute(
                """
                WITH ranked AS (
                    SELECT
                        id,
                        ROW_NUMBER() OVER (
                            PARTITION BY
                                UPPER(ticker),
                                cik,
                                company_name,
                                concept,
                                value,
                                unit,
                                COALESCE(fiscal_year, -1),
                                COALESCE(fiscal_period, ''),
                                COALESCE(filed_on, ''),
                                statement_type,
                                source
                            ORDER BY id
                        ) AS rn
                    FROM sec_financial_statements
                )
                DELETE FROM sec_financial_statements target
                USING ranked
                WHERE target.id = ranked.id
                  AND ranked.rn > 1
                """
            )
            await conn.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS ux_sec_financial_statements_dedup
                ON sec_financial_statements (
                    UPPER(ticker),
                    cik,
                    company_name,
                    concept,
                    value,
                    unit,
                    COALESCE(fiscal_year, -1),
                    COALESCE(fiscal_period, ''),
                    COALESCE(filed_on, ''),
                    statement_type,
                    source
                )
                """
            )
            inserted_count = 0
            for statement in statements:
                status = await conn.execute(
                    """
                    INSERT INTO sec_financial_statements (
                        ticker, cik, company_name, concept, value, unit,
                        fiscal_year, fiscal_period, filed_on, statement_type, source
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                    ON CONFLICT DO NOTHING
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
                try:
                    inserted_count += int(status.split()[-1])
                except (ValueError, IndexError):
                    # Defensive fallback: command tags should end with row count.
                    pass
            return inserted_count
        finally:
            await conn.close()

    async def _list_available_tickers(
        self,
        *,
        fiscal_period: str,
        min_distinct_years: int,
        limit: int,
    ) -> list[str]:
        conn: asyncpg.Connection = await asyncpg.connect(self._database_url)
        try:
            rows = await conn.fetch(
                """
                SELECT UPPER(ticker) AS ticker
                FROM sec_financial_statements
                WHERE fiscal_year IS NOT NULL
                  AND fiscal_period = $1
                GROUP BY UPPER(ticker)
                HAVING COUNT(DISTINCT fiscal_year) >= $2
                ORDER BY UPPER(ticker)
                LIMIT $3
                """,
                fiscal_period,
                min_distinct_years,
                limit,
            )
            return [str(row["ticker"]) for row in rows]
        finally:
            await conn.close()

    async def _list_available_fiscal_years_for_ticker(
        self,
        *,
        ticker: str,
        fiscal_period: str,
    ) -> list[int]:
        conn: asyncpg.Connection = await asyncpg.connect(self._database_url)
        try:
            rows = await conn.fetch(
                """
                SELECT DISTINCT fiscal_year
                FROM sec_financial_statements
                WHERE UPPER(ticker) = UPPER($1)
                  AND fiscal_year IS NOT NULL
                  AND fiscal_period = $2
                ORDER BY fiscal_year
                """,
                ticker,
                fiscal_period,
            )
            return [int(row["fiscal_year"]) for row in rows]
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
