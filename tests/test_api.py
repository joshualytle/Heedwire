"""Read-only API tests: /healthz, /findings (since/limit), /sources.

Uses FastAPI's TestClient against a temp store seeded directly — no network,
no scheduler. Covers the v1 read-only API surface (the feeder/consumer seam).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from heedwire.api import create_app
from heedwire.config import Config
from heedwire.models import Item, Severity
from heedwire.store import Store


def _item(uid: str, **kw) -> Item:
    base = dict(source="kev", uid=uid, title=f"{uid} Vulnerability",
                url=f"https://nvd.nist.gov/vuln/detail/{uid}")
    base.update(kw)
    return Item(**base)


@pytest.fixture
def cfg(tmp_path):
    return Config(store_path=str(tmp_path / "api.db"),
                  sources={"kev": {"type": "kev"}, "rss:psirt-0": {"type": "rss"}})


@pytest.fixture
def client(cfg):
    return TestClient(create_app(cfg))


def _seed(cfg: Config, *items: Item) -> None:
    store = Store(cfg.store_path)
    try:
        for it in items:
            store.upsert(it)
    finally:
        store.close()


def test_healthz_fresh_store(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"ok": True, "last_run": None}


def test_healthz_reports_last_run(cfg, client):
    store = Store(cfg.store_path)
    store.set_meta("last_run", "2026-06-14T00:00:00+00:00")
    store.close()
    assert client.get("/healthz").json()["last_run"] == "2026-06-14T00:00:00+00:00"


def test_sources_lists_configured_keys(client):
    body = client.get("/sources").json()
    assert body == {"sources": ["kev", "rss:psirt-0"]}


def test_findings_returns_stored_items(cfg, client):
    _seed(cfg, _item("CVE-2026-1", severity=Severity.CRITICAL, known_exploited=True),
          _item("CVE-2026-2"))
    items = client.get("/findings").json()["items"]
    assert {i["uid"] for i in items} == {"CVE-2026-1", "CVE-2026-2"}
    # serialized via to_wire(): severity is a plain string, raw is dropped
    kev = next(i for i in items if i["uid"] == "CVE-2026-1")
    assert kev["severity"] == "critical" and kev["known_exploited"] is True
    assert "raw" not in kev


def test_findings_since_filters_on_first_seen(cfg, client):
    _seed(cfg, _item("CVE-2026-3"))
    future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    assert client.get("/findings", params={"since": future}).json()["items"] == []
    assert len(client.get("/findings", params={"since": past}).json()["items"]) == 1


def test_findings_respects_limit(cfg, client):
    _seed(cfg, _item("CVE-2026-4"), _item("CVE-2026-5"), _item("CVE-2026-6"))
    assert len(client.get("/findings", params={"limit": 2}).json()["items"]) == 2
