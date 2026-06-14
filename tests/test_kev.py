"""KEV parser tests against a saved real CISA KEV sample (no live API).

The fixture `tests/fixtures/kev_sample.json` is trimmed from the live CISA
catalog and preserves real quirks (e.g. stray whitespace in a product field).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from heedwire.models import Severity
from heedwire.sources import kev as kev_mod
from heedwire.sources.kev import KevSource

FIXTURE = Path(__file__).parent / "fixtures" / "kev_sample.json"


@pytest.fixture
def sample() -> dict:
    return json.loads(FIXTURE.read_text())


def _patch(monkeypatch, payload: dict) -> None:
    monkeypatch.setattr(kev_mod, "get_json", lambda *a, **k: payload)


def test_fetch_normalizes_real_sample(monkeypatch, sample):
    _patch(monkeypatch, sample)
    items = KevSource().fetch(datetime(2000, 1, 1, tzinfo=timezone.utc))

    assert len(items) == 4
    assert all(it.known_exploited for it in items)
    assert all(it.severity is Severity.CRITICAL for it in items)
    assert all(it.source == "kev" for it in items)

    by_cve = {it.uid: it for it in items}
    forti = by_cve["CVE-2019-6693"]
    assert forti.uid == "CVE-2019-6693"          # native CVE id is the stable uid
    assert forti.cve_ids == ["CVE-2019-6693"]
    assert forti.vendors == ["fortinet"] and forti.products == ["fortios"]
    assert forti.url == "https://nvd.nist.gov/vuln/detail/CVE-2019-6693"


def test_fetch_strips_whitespace_in_structured_fields(monkeypatch, sample):
    """The live catalog ships products like ' PeopleSoft...'; normalize them so
    exact structured matching is not silently defeated."""
    _patch(monkeypatch, sample)
    items = KevSource().fetch(datetime(2000, 1, 1, tzinfo=timezone.utc))
    oracle = next(it for it in items if it.uid == "CVE-2026-35273")
    assert oracle.products == ["peoplesoft enterprise peopletools"]   # no leading space
    assert oracle.vendors == ["oracle"]


def test_fetch_applies_window(monkeypatch, sample):
    _patch(monkeypatch, sample)
    # Only the 2026-06-12 entry is newer than this cutoff.
    items = KevSource().fetch(datetime(2026, 6, 1, tzinfo=timezone.utc))
    assert [it.uid for it in items] == ["CVE-2026-35273"]


def test_fetch_raises_on_unexpected_shape(monkeypatch):
    _patch(monkeypatch, {"unexpected": []})
    with pytest.raises(ValueError, match="vulnerabilities"):
        KevSource().fetch(datetime(2000, 1, 1, tzinfo=timezone.utc))
