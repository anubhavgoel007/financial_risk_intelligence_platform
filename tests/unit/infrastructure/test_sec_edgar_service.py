from __future__ import annotations

from typing import Any

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
            raise RuntimeError("bad response")

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
