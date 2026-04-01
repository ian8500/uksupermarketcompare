import io
from urllib.error import HTTPError

import pytest

from app.services.providers.live_sources import LiveSourceError, TescoLiveSourceConfig, TescoThirdPartyApiSource
from app.services.providers.retailers import TescoProvider


class _FakeResponse:
    def __init__(self, payload: bytes):
        self._payload = payload

    def read(self) -> bytes:
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def _http_error(code: int, retry_after: str | None = None) -> HTTPError:
    headers = {"Retry-After": retry_after} if retry_after else None
    return HTTPError(url="https://example.test", code=code, msg="error", hdrs=headers, fp=io.BytesIO(b""))


def test_malformed_payload_root_raises(monkeypatch):
    config = TescoLiveSourceConfig(
        mode="thirdparty",
        official_base_url="",
        official_api_key=None,
        official_partner_id=None,
        third_party_base_url="https://example.test/products",
        third_party_api_key="key",
        query_terms=["milk"],
        timeout_seconds=5,
        max_retries=0,
    )
    source = TescoThirdPartyApiSource(config)

    monkeypatch.setattr(
        "app.services.providers.live_sources.urlopen",
        lambda req, timeout: _FakeResponse(b'["not-an-object-root"]'),
    )

    with pytest.raises(LiveSourceError, match="All Tesco upstream queries failed"):
        source.fetch_products()


def test_rate_limit_retries_then_succeeds(monkeypatch):
    config = TescoLiveSourceConfig(
        mode="thirdparty",
        official_base_url="",
        official_api_key=None,
        official_partner_id=None,
        third_party_base_url="https://example.test/products",
        third_party_api_key="key",
        query_terms=["milk"],
        timeout_seconds=5,
        max_retries=1,
    )
    source = TescoThirdPartyApiSource(config)

    calls = {"count": 0}

    def _fake_urlopen(req, timeout):
        calls["count"] += 1
        if calls["count"] == 1:
            raise _http_error(429, retry_after="0")
        return _FakeResponse(
            b'{"products": [{"id": "p1", "name": "Milk", "price": "1.50", "size": "1L", "brand": "Tesco"}]}'
        )

    monkeypatch.setattr("app.services.providers.live_sources.time.sleep", lambda seconds: None)
    monkeypatch.setattr("app.services.providers.live_sources.urlopen", _fake_urlopen)

    rows = source.fetch_products()

    assert len(rows) == 1
    assert calls["count"] == 2
    assert source.last_fetch_report["fetched"] == 1
    assert source.last_fetch_report["mapped"] == 1


def test_tesco_provider_falls_back_to_seed_when_live_fails(monkeypatch):
    monkeypatch.setenv("TESCO_SOURCE_MODE", "thirdparty")
    monkeypatch.setenv("TESCO_THIRD_PARTY_BASE_URL", "https://example.test/products")
    monkeypatch.setenv("TESCO_THIRD_PARTY_API_KEY", "key")

    provider = TescoProvider()
    monkeypatch.setattr(
        provider._third_party,
        "fetch_products",
        lambda: (_ for _ in ()).throw(LiveSourceError("rate limited")),
    )

    rows = provider.load_products()

    assert rows
    assert provider.active_source == "seed"
    assert provider.last_import_report["source"] == "seed"
    assert provider.last_import_report["mapped"] == len(rows)
