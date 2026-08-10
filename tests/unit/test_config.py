from __future__ import annotations

from risk_platform.core.config import Settings


def test_settings_reads_all_sec_settings(monkeypatch) -> None:
    monkeypatch.setenv(
        "SEC_TICKERS",
        "AAPL,MSFT,GOOGL,AMZN,META,NVDA,TSLA,JPM,BAC,WFC,UNH,JNJ,XOM,CVX,PG,KO,PEP,HD,DIS,V",
    )
    monkeypatch.setenv("SEC_USER_AGENT", "Test Agent test@example.com")
    monkeypatch.setenv("SEC_REQUEST_DELAY_SECONDS", "0.35")
    monkeypatch.setenv("SEC_MAX_RETRIES", "3")
    monkeypatch.setenv("SEC_RETRY_BACKOFF_SECONDS", "0.5")
    monkeypatch.setenv("SEC_RETRY_BACKOFF_MULTIPLIER", "2.0")

    settings = Settings()

    assert settings.sec_user_agent == "Test Agent test@example.com"
    assert settings.sec_request_delay_seconds == 0.35
    assert settings.sec_max_retries == 3
    assert settings.sec_retry_backoff_seconds == 0.5
    assert settings.sec_retry_backoff_multiplier == 2.0
    assert len(settings.sec_tickers) == 20
    assert len(set(settings.sec_tickers)) == 20


def test_settings_deduplicates_tickers_and_falls_back(monkeypatch) -> None:
    monkeypatch.setenv("SEC_TICKERS", "aapl, msft, aapl")
    settings = Settings()
    assert settings.sec_tickers == ["AAPL", "MSFT"]

    monkeypatch.delenv("SEC_TICKERS", raising=False)
    monkeypatch.setenv("SEC_TICKER", "nvda")
    settings_fallback = Settings()
    assert settings_fallback.sec_tickers == ["NVDA"]


def test_settings_parses_legacy_cik_overrides(monkeypatch) -> None:
    monkeypatch.setenv(
        "SEC_LEGACY_CIK_OVERRIDES",
        "xom:34088|0000034088; badsegment ; cvx:0000093410",
    )

    settings = Settings()

    assert settings.sec_legacy_cik_overrides == {
        "XOM": ["0000034088"],
        "CVX": ["0000093410"],
    }
