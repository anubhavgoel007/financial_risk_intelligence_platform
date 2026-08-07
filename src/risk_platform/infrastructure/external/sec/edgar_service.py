from __future__ import annotations

import json
from typing import Any

import httpx

from risk_platform.domain.entities.sec_financial_statement import SecFinancialStatement


class SecEdgarClient:
    """Fetches and normalizes SEC EDGAR company facts for a ticker."""

    def __init__(self, user_agent: str | None = None) -> None:
        self._user_agent = user_agent or "risk-platform/0.1"
        self._headers = {
            "User-Agent": self._user_agent,
            "Accept-Encoding": "gzip, deflate",
            "Accept": "application/json",
        }

    def fetch_company_facts(self, ticker: str) -> list[SecFinancialStatement]:
        if not ticker:
            raise ValueError("ticker is required")

        cik = self._resolve_cik(ticker)
        try:
            response = httpx.get(
                f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json",
                headers=self._headers,
                timeout=20.0,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            if exc.response is not None and exc.response.status_code == 404:
                raise ValueError(f"No SEC company facts found for ticker {ticker}") from exc
            raise

        payload = response.json()
        return self.normalize_company_facts(payload, ticker=ticker.upper())

    def normalize_company_facts(self, payload: dict[str, Any], *, ticker: str) -> list[SecFinancialStatement]:
        if not isinstance(payload, dict):
            raise ValueError("SEC payload must be a JSON object")

        if not payload.get("entityName"):
            raise ValueError("SEC payload is missing entityName")

        facts = payload.get("facts")
        if not isinstance(facts, dict):
            raise ValueError("SEC payload is missing facts")

        statements: list[SecFinancialStatement] = []
        for namespace, namespace_facts in facts.items():
            if not isinstance(namespace_facts, dict):
                continue
            for concept, concept_payload in namespace_facts.items():
                if not isinstance(concept_payload, dict):
                    continue

                units = concept_payload.get("units", {})
                if not isinstance(units, dict):
                    continue

                for unit, entries in units.items():
                    if not isinstance(entries, list):
                        continue
                    for entry in entries:
                        if not isinstance(entry, dict):
                            continue
                        value = entry.get("val")
                        if value is None:
                            continue
                        if not isinstance(value, (int, float)):
                            continue
                        statements.append(
                            SecFinancialStatement(
                                ticker=ticker.upper(),
                                cik=str(payload.get("cik", "")),
                                company_name=str(payload.get("entityName", "")),
                                concept=concept,
                                value=float(value),
                                unit=str(unit),
                                fiscal_year=entry.get("fy"),
                                fiscal_period=entry.get("fp"),
                                filed_on=entry.get("filed"),
                                statement_type=self._classify_statement_type(concept),
                                source="sec_edgar",
                            )
                        )

        if not statements:
            raise ValueError("No financial statement facts were found")
        return statements

    def _resolve_cik(self, ticker: str) -> str:
        response = httpx.get(
            "https://www.sec.gov/files/company_tickers.json",
            headers=self._headers,
            timeout=20.0,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("SEC ticker feed did not return a JSON object")

        for item in payload.values():
            if not isinstance(item, dict):
                continue

            item_ticker = str(item.get("ticker") or item.get("ticker_symbol") or "").upper()
            if item_ticker != ticker.upper():
                continue

            cik_value = item.get("cik_str") or item.get("cik")
            if cik_value is None:
                raise ValueError(f"SEC ticker entry for {ticker} is missing a CIK")
            return str(cik_value).zfill(10)

        raise ValueError(f"No CIK found for ticker {ticker}")

    def _classify_statement_type(self, concept: str) -> str:
        lowered = concept.lower()
        if "cashflow" in lowered or lowered.startswith("cash"):
            return "cash_flow"
        if "revenue" in lowered or "income" in lowered or "expense" in lowered or "earnings" in lowered:
            return "income_statement"
        return "balance_sheet"
