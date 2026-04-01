from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.services.diagnostics import _classify_retailer_freshness


def test_freshness_classification_healthy_with_recent_success() -> None:
    now = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    success_at = (now - timedelta(hours=4)).isoformat()

    age_hours, status = _classify_retailer_freshness(now=now, last_success_at=success_at, last_status="success")

    assert age_hours == 4
    assert status == "healthy"


def test_freshness_classification_stale_when_older_than_24h() -> None:
    now = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    success_at = (now - timedelta(hours=30)).isoformat()

    age_hours, status = _classify_retailer_freshness(now=now, last_success_at=success_at, last_status="success")

    assert age_hours == 30
    assert status == "stale"


def test_freshness_classification_critical_when_older_than_72h() -> None:
    now = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    success_at = (now - timedelta(hours=80)).isoformat()

    age_hours, status = _classify_retailer_freshness(now=now, last_success_at=success_at, last_status="success")

    assert age_hours == 80
    assert status == "critical"


def test_freshness_classification_failed_when_latest_failed_and_no_recent_success() -> None:
    now = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    success_at = (now - timedelta(hours=36)).isoformat()

    age_hours, status = _classify_retailer_freshness(now=now, last_success_at=success_at, last_status="failed")

    assert age_hours == 36
    assert status == "failed"


def test_freshness_classification_failed_when_latest_failed_and_no_success_exists() -> None:
    now = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)

    age_hours, status = _classify_retailer_freshness(now=now, last_success_at=None, last_status="failed")

    assert age_hours is None
    assert status == "failed"

