from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

import pytest


def _load_ingest_script_module():
    root = Path(__file__).resolve().parents[3]
    module_path = root / "scripts" / "ingest_sec_data.py"
    spec = importlib.util.spec_from_file_location("ingest_sec_data", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load ingest_sec_data.py module")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_resolve_tickers_from_env_uses_sec_tickers_and_deduplicates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    script_module = _load_ingest_script_module()
    monkeypatch.setenv("SEC_TICKERS", "aapl, msft, aapl, goog")
    monkeypatch.setenv("SEC_TICKER", "tsla")

    tickers = script_module.resolve_tickers_from_env()

    assert tickers == ["AAPL", "MSFT", "GOOG"]


def test_resolve_tickers_from_env_falls_back_to_sec_ticker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    script_module = _load_ingest_script_module()
    monkeypatch.delenv("SEC_TICKERS", raising=False)
    monkeypatch.setenv("SEC_TICKER", "nvda")

    tickers = script_module.resolve_tickers_from_env()

    assert tickers == ["NVDA"]


def test_resolve_legacy_cik_overrides_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    script_module = _load_ingest_script_module()
    monkeypatch.setenv("SEC_LEGACY_CIK_OVERRIDES", "xom:34088|0000034088;cvx:0000093410")

    overrides = script_module.resolve_legacy_cik_overrides_from_env()

    assert overrides == {
        "XOM": ["0000034088"],
        "CVX": ["0000093410"],
    }


def test_main_reports_inserted_counts_per_ticker(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    script_module = _load_ingest_script_module()
    monkeypatch.setenv("SEC_TICKERS", "aapl,msft")
    monkeypatch.setenv("DATABASE_URL", "postgresql://example")
    monkeypatch.setenv("SEC_LEGACY_CIK_OVERRIDES", "XOM:0000034088")

    captured_client_kwargs: dict[str, Any] = {}

    class FakeClient:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            captured_client_kwargs.update(kwargs)

    class FakeRepository:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

    class FakeUseCase:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def execute_many(self, tickers: list[str]) -> dict[str, int]:
            assert tickers == ["AAPL", "MSFT"]
            return {"AAPL": 2, "MSFT": 1}

    monkeypatch.setattr(script_module, "SecEdgarClient", FakeClient)
    monkeypatch.setattr(script_module, "PostgresSecStatementRepository", FakeRepository)
    monkeypatch.setattr(script_module, "IngestSecFinancialStatementsUseCase", FakeUseCase)

    script_module.main()
    output = capsys.readouterr().out

    assert captured_client_kwargs["legacy_cik_overrides"] == {"XOM": ["0000034088"]}

    assert "Persisted 2 SEC financial statement rows for AAPL into PostgreSQL" in output
    assert "Persisted 1 SEC financial statement rows for MSFT into PostgreSQL" in output
    assert "Total persisted rows across 2 ticker(s): 3" in output
