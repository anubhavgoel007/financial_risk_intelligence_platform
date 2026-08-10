from __future__ import annotations

import time
from typing import Any

import httpx

from risk_platform.domain.entities.sec_financial_statement import SecFinancialStatement


class SecEdgarClient:
    """Fetches and normalizes SEC EDGAR company facts for a ticker."""

    def __init__(
        self,
        user_agent: str | None = None,
        *,
        request_delay_seconds: float = 0.35,
        max_retries: int = 3,
        retry_backoff_seconds: float = 0.5,
        retry_backoff_multiplier: float = 2.0,
        timeout_seconds: float = 20.0,
        legacy_cik_overrides: dict[str, list[str]] | None = None,
    ) -> None:
        self._user_agent = user_agent or "risk-platform/0.1"
        self._request_delay_seconds = max(request_delay_seconds, 0.0)
        self._max_retries = max(max_retries, 0)
        self._retry_backoff_seconds = max(retry_backoff_seconds, 0.0)
        self._retry_backoff_multiplier = max(retry_backoff_multiplier, 1.0)
        self._timeout_seconds = max(timeout_seconds, 1.0)
        self._headers = {
            "User-Agent": self._user_agent,
            "Accept-Encoding": "gzip, deflate",
            "Accept": "application/json",
        }
        self._last_request_monotonic: float | None = None
        self._ticker_to_cik_cache: dict[str, str] = {}
        self._legacy_cik_overrides = self._normalize_legacy_cik_overrides(legacy_cik_overrides)

    def fetch_company_facts(self, ticker: str) -> list[SecFinancialStatement]:
        if not ticker:
            raise ValueError("ticker is required")

        normalized_ticker = ticker.strip().upper()
        statements: list[SecFinancialStatement] = []
        for cik in self._resolve_ciks_for_ticker(normalized_ticker):
            payload = self._request_json_with_retry(
                f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json",
                not_found_message=(
                    f"No SEC company facts found for ticker {normalized_ticker} and CIK {cik}"
                ),
            )
            statements.extend(self.normalize_company_facts(payload, ticker=normalized_ticker))

        return self._deduplicate_statements(statements)

    def _resolve_ciks_for_ticker(self, ticker: str) -> list[str]:
        primary_cik = self._resolve_cik(ticker)
        ciks = [primary_cik]
        for legacy_cik in self._legacy_cik_overrides.get(ticker, []):
            if legacy_cik not in ciks:
                ciks.append(legacy_cik)
        return ciks

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
        normalized_ticker = ticker.strip().upper()
        cached = self._ticker_to_cik_cache.get(normalized_ticker)
        if cached is not None:
            return cached

        payload = self._request_json_with_retry("https://www.sec.gov/files/company_tickers.json")
        if not isinstance(payload, dict):
            raise ValueError("SEC ticker feed did not return a JSON object")

        for item in payload.values():
            if not isinstance(item, dict):
                continue

            item_ticker = str(item.get("ticker") or item.get("ticker_symbol") or "").upper()
            if item_ticker != normalized_ticker:
                continue

            cik_value = item.get("cik_str") or item.get("cik")
            if cik_value is None:
                raise ValueError(f"SEC ticker entry for {normalized_ticker} is missing a CIK")
            resolved = str(cik_value).zfill(10)
            self._ticker_to_cik_cache[normalized_ticker] = resolved
            return resolved

        raise ValueError(f"No CIK found for ticker {normalized_ticker}")

    @staticmethod
    def _normalize_legacy_cik_overrides(
        overrides: dict[str, list[str]] | None,
    ) -> dict[str, list[str]]:
        if not overrides:
            return {}

        normalized: dict[str, list[str]] = {}
        for raw_ticker, raw_ciks in overrides.items():
            ticker = raw_ticker.strip().upper()
            if not ticker:
                continue
            ciks: list[str] = []
            seen: set[str] = set()
            for raw_cik in raw_ciks:
                cik = str(raw_cik).strip()
                if not cik:
                    continue
                normalized_cik = cik.zfill(10)
                if normalized_cik in seen:
                    continue
                seen.add(normalized_cik)
                ciks.append(normalized_cik)
            if ciks:
                normalized[ticker] = ciks
        return normalized

    @staticmethod
    def _deduplicate_statements(
        statements: list[SecFinancialStatement],
    ) -> list[SecFinancialStatement]:
        deduped: list[SecFinancialStatement] = []
        seen: set[tuple[object, ...]] = set()
        for statement in statements:
            dedup_key = (
                statement.ticker.upper(),
                statement.concept,
                statement.value,
                statement.unit,
                statement.fiscal_year,
                statement.fiscal_period,
                statement.filed_on,
                statement.statement_type,
                statement.source,
            )
            if dedup_key in seen:
                continue
            seen.add(dedup_key)
            deduped.append(statement)
        return deduped

    def _request_json_with_retry(
        self,
        url: str,
        *,
        not_found_message: str | None = None,
    ) -> dict[str, Any]:
        backoff_seconds = self._retry_backoff_seconds
        attempts = 0
        while True:
            self._apply_request_delay()
            try:
                response = httpx.get(
                    url,
                    headers=self._headers,
                    timeout=self._timeout_seconds,
                )
                if response.status_code == 404 and not_found_message:
                    raise ValueError(not_found_message)
                response.raise_for_status()
                payload = response.json()
                if not isinstance(payload, dict):
                    raise ValueError("SEC API did not return a JSON object")
                return payload
            except ValueError:
                raise
            except (httpx.TimeoutException, httpx.TransportError):
                if attempts >= self._max_retries:
                    raise
            except httpx.HTTPStatusError as exc:
                status_code = exc.response.status_code if exc.response is not None else None
                retryable = status_code == 429 or (status_code is not None and 500 <= status_code < 600)
                if status_code == 404 and not_found_message:
                    raise ValueError(not_found_message) from exc
                if not retryable or attempts >= self._max_retries:
                    raise

            attempts += 1
            if backoff_seconds > 0:
                time.sleep(backoff_seconds)
            backoff_seconds *= self._retry_backoff_multiplier

    def _apply_request_delay(self) -> None:
        if self._request_delay_seconds <= 0:
            return

        now = time.monotonic()
        if self._last_request_monotonic is not None:
            elapsed = now - self._last_request_monotonic
            remaining = self._request_delay_seconds - elapsed
            if remaining > 0:
                time.sleep(remaining)
                now = time.monotonic()
        self._last_request_monotonic = now

    def _classify_statement_type(self, concept: str) -> str:
        lowered = concept.lower()
        if "cashflow" in lowered or lowered.startswith("cash"):
            return "cash_flow"
        if "revenue" in lowered or "income" in lowered or "expense" in lowered or "earnings" in lowered:
            return "income_statement"
        return "balance_sheet"
