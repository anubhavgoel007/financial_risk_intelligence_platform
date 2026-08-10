from __future__ import annotations

from typing import Any

import httpx
import pytest

from risk_platform.application.use_cases.sec_ingest_use_case import IngestSecFinancialStatementsUseCase
from risk_platform.domain.entities.sec_financial_statement import SecFinancialStatement
from risk_platform.infrastructure.external.sec.edgar_service import SecEdgarClient


class FakeRepository:
    def __init__(self) -> None:
        self.items: list[SecFinancialStatement] = []

    def save_many(self, statements: list[SecFinancialStatement]) -> None:
        self.items.extend(statements)


class DummyResponse:
    def __init__(self, payload: dict[str, Any], *, status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            request = httpx.Request("GET", "https://data.sec.gov")
            response = httpx.Response(self.status_code, request=request, json=self._payload)
            raise httpx.HTTPStatusError("bad response", request=request, response=response)

    def json(self) -> dict[str, Any]:
        return self._payload


def test_sec_edgar_client_normalizes_company_facts() -> None:
    payload = {
        "cik": 320193,
        "entityName": "Apple Inc.",
        "facts": {
            "us-gaap": {
                "Assets": {
                    "units": {"USD": [{"val": 100000, "fy": 2024, "fp": "FY", "filed": "2025-02-01"}]}
                },
                "RevenueFromContractWithCustomer": {
                    "units": {"USD": [{"val": 200000, "fy": 2024, "fp": "FY", "filed": "2025-02-01"}]}
                },
            }
        },
    }

    client = SecEdgarClient(user_agent="test-agent")
    statements = client.normalize_company_facts(payload, ticker="AAPL")

    assert len(statements) == 2
    assert statements[0].ticker == "AAPL"
    assert statements[0].concept == "Assets"
    assert statements[0].value == 100000
    assert statements[0].statement_type == "balance_sheet"


def test_resolve_cik_uses_cik_str_field(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(url: str, *args: Any, **kwargs: Any) -> DummyResponse:
        if "company_tickers" in url:
            return DummyResponse({"0": {"ticker": "AAPL", "cik_str": "320193"}})
        raise AssertionError(f"unexpected url: {url}")

    monkeypatch.setattr("risk_platform.infrastructure.external.sec.edgar_service.httpx.get", fake_get)

    client = SecEdgarClient(user_agent="test-agent")
    assert client._resolve_cik("AAPL") == "0000320193"


def test_resolve_cik_returns_current_xom_cik(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(url: str, *args: Any, **kwargs: Any) -> DummyResponse:
        if "company_tickers" in url:
            return DummyResponse({"0": {"ticker": "XOM", "cik_str": "2115436"}})
        raise AssertionError(f"unexpected url: {url}")

    monkeypatch.setattr("risk_platform.infrastructure.external.sec.edgar_service.httpx.get", fake_get)

    client = SecEdgarClient(user_agent="test-agent")
    assert client._resolve_cik("XOM") == "0002115436"


def test_fetch_company_facts_xom_uses_current_and_legacy_ciks_and_deduplicates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    current_payload = {
        "cik": "0002115436",
        "entityName": "Exxon Mobil Corporation",
        "facts": {
            "us-gaap": {
                "Assets": {
                    "units": {
                        "USD": [
                            {"val": 1000, "fy": 2026, "fp": "FY", "filed": "2026-02-01"},
                            {"val": 900, "fy": 2024, "fp": "FY", "filed": "2025-02-01"},
                        ]
                    }
                }
            }
        },
    }
    legacy_payload = {
        "cik": "0000034088",
        "entityName": "Exxon Mobil Corporation",
        "facts": {
            "us-gaap": {
                "Assets": {
                    "units": {
                        "USD": [
                            # Overlap with current payload: should be deduplicated by content.
                            {"val": 900, "fy": 2024, "fp": "FY", "filed": "2025-02-01"},
                            {"val": 800, "fy": 2023, "fp": "FY", "filed": "2024-02-01"},
                        ]
                    }
                }
            }
        },
    }

    def fake_get(url: str, *args: Any, **kwargs: Any) -> DummyResponse:
        calls.append(url)
        if "company_tickers" in url:
            return DummyResponse({"0": {"ticker": "XOM", "cik_str": "2115436"}})
        if "CIK0002115436" in url:
            return DummyResponse(current_payload)
        if "CIK0000034088" in url:
            return DummyResponse(legacy_payload)
        raise AssertionError(f"unexpected url: {url}")

    monkeypatch.setattr("risk_platform.infrastructure.external.sec.edgar_service.httpx.get", fake_get)

    client = SecEdgarClient(
        user_agent="test-agent",
        request_delay_seconds=0.0,
        legacy_cik_overrides={"XOM": ["0000034088"]},
    )

    statements = client.fetch_company_facts("XOM")

    assert any("company_tickers" in call for call in calls)
    assert any("CIK0002115436" in call for call in calls)
    assert any("CIK0000034088" in call for call in calls)
    # 2026 + deduplicated 2024 + 2023
    assert len(statements) == 3
    assert sorted({statement.fiscal_year for statement in statements if statement.fiscal_year is not None}) == [
        2023,
        2024,
        2026,
    ]


def test_fetch_company_facts_non_xom_keeps_single_cik_behavior(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"companyfacts": 0}

    def fake_get(url: str, *args: Any, **kwargs: Any) -> DummyResponse:
        if "company_tickers" in url:
            return DummyResponse({"0": {"ticker": "AAPL", "cik_str": "320193"}})
        if "companyfacts" in url:
            calls["companyfacts"] += 1
            return DummyResponse(
                {
                    "cik": "0000320193",
                    "entityName": "Apple Inc.",
                    "facts": {
                        "us-gaap": {
                            "Assets": {
                                "units": {
                                    "USD": [
                                        {
                                            "val": 100000,
                                            "fy": 2024,
                                            "fp": "FY",
                                            "filed": "2025-02-01",
                                        }
                                    ]
                                }
                            }
                        }
                    },
                }
            )
        raise AssertionError(f"unexpected url: {url}")

    monkeypatch.setattr("risk_platform.infrastructure.external.sec.edgar_service.httpx.get", fake_get)

    client = SecEdgarClient(
        user_agent="test-agent",
        request_delay_seconds=0.0,
        legacy_cik_overrides={"XOM": ["0000034088"]},
    )
    statements = client.fetch_company_facts("AAPL")

    assert len(statements) == 1
    assert calls["companyfacts"] == 1


def test_ingest_use_case_persists_normalized_statements(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {
        "cik": 320193,
        "entityName": "Apple Inc.",
        "facts": {
            "us-gaap": {
                "Assets": {
                    "units": {"USD": [{"val": 100000, "fy": 2024, "fp": "FY", "filed": "2025-02-01"}]}
                }
            }
        },
    }

    class FakeClient:
        def __init__(self) -> None:
            self.calls: list[str] = []

        def fetch_company_facts(self, ticker: str) -> list[SecFinancialStatement]:
            self.calls.append(ticker)
            return [
                SecFinancialStatement(
                    ticker=ticker,
                    cik="320193",
                    company_name="Apple Inc.",
                    concept="Assets",
                    value=100000,
                    unit="USD",
                    fiscal_year=2024,
                    fiscal_period="FY",
                    filed_on="2025-02-01",
                    statement_type="balance_sheet",
                )
            ]

    repository = FakeRepository()
    use_case = IngestSecFinancialStatementsUseCase(client=FakeClient(), repository=repository)

    result = use_case.execute("AAPL")

    assert result == 1
    assert len(repository.items) == 1
    assert repository.items[0].ticker == "AAPL"


def test_ingest_use_case_execute_many_is_sequential() -> None:
    class FakeClient:
        def __init__(self) -> None:
            self.calls: list[str] = []

        def fetch_company_facts(self, ticker: str) -> list[SecFinancialStatement]:
            self.calls.append(ticker)
            return [
                SecFinancialStatement(
                    ticker=ticker,
                    cik="320193",
                    company_name="Example Co",
                    concept="Assets",
                    value=100000.0,
                    unit="USD",
                    fiscal_year=2024,
                    fiscal_period="FY",
                    filed_on="2025-02-01",
                    statement_type="balance_sheet",
                )
            ]

    class CountingRepository:
        def save_many(self, statements: list[SecFinancialStatement]) -> int:
            return len(statements)

    client = FakeClient()
    use_case = IngestSecFinancialStatementsUseCase(client=client, repository=CountingRepository())

    counts = use_case.execute_many([" aapl ", "", "msft"])

    assert client.calls == ["AAPL", "MSFT"]
    assert counts == {"AAPL": 1, "MSFT": 1}


def test_fetch_company_facts_retries_429_with_backoff(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"company_tickers": 0, "companyfacts": 0}
    sleep_calls: list[float] = []

    def fake_sleep(seconds: float) -> None:
        sleep_calls.append(seconds)

    def fake_get(url: str, *args: Any, **kwargs: Any) -> DummyResponse:
        if "company_tickers" in url:
            calls["company_tickers"] += 1
            return DummyResponse({"0": {"ticker": "AAPL", "cik_str": "320193"}}, status_code=200)
        if "companyfacts" in url:
            calls["companyfacts"] += 1
            if calls["companyfacts"] == 1:
                return DummyResponse({}, status_code=429)
            return DummyResponse(
                {
                    "cik": 320193,
                    "entityName": "Apple Inc.",
                    "facts": {
                        "us-gaap": {
                            "Assets": {
                                "units": {
                                    "USD": [
                                        {
                                            "val": 100000,
                                            "fy": 2024,
                                            "fp": "FY",
                                            "filed": "2025-02-01",
                                        }
                                    ]
                                }
                            }
                        }
                    },
                },
                status_code=200,
            )
        raise AssertionError(f"unexpected url: {url}")

    monkeypatch.setattr("risk_platform.infrastructure.external.sec.edgar_service.httpx.get", fake_get)
    monkeypatch.setattr("risk_platform.infrastructure.external.sec.edgar_service.time.sleep", fake_sleep)

    client = SecEdgarClient(
        user_agent="test-agent",
        request_delay_seconds=0.0,
        max_retries=2,
        retry_backoff_seconds=0.1,
        retry_backoff_multiplier=2.0,
    )

    statements = client.fetch_company_facts("AAPL")

    assert len(statements) == 1
    assert calls["company_tickers"] == 1
    assert calls["companyfacts"] == 2
    assert sleep_calls == [0.1]
