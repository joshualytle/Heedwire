"""Advisory-RSS end-to-end matching against a saved real PSIRT feed (no network).

`tests/fixtures/paloalto_psirt_rss.xml` is a real Palo Alto Networks PSIRT feed
(trimmed to 3 entries, recorded from the shipped `advisory_feed`). It exercises
the full advisory path: rss parse -> taxonomy resolve -> alias match. PSIRT items
carry no parsed severity (UNKNOWN), so they match via the alias path only; we use
permissive `Gates()` here to isolate matching from the severity gate (the shipped
config's `min_severity: high` would otherwise gate UNKNOWN advisory items out).
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from heedwire.config import Gates, Watch
from heedwire.matching import evaluate
from heedwire.sources.rss import RssSource
from heedwire.taxonomy import load_taxonomy, resolve

FIXTURES = Path(__file__).parent / "fixtures"
TAXONOMY = Path(__file__).parents[1] / "data" / "taxonomy.yaml"
LONG_AGO = datetime(2000, 1, 1, tzinfo=timezone.utc)


def _resolved_panos():
    return resolve(Watch(products=["paloalto.panos"]), load_taxonomy(TAXONOMY))


def test_resolve_adds_real_advisory_feed():
    """Picking the product pulls in its real shipped PSIRT feed URL."""
    rw = _resolved_panos()
    assert "https://security.paloaltonetworks.com/rss.xml" in rw.advisory_feeds


def test_advisory_item_matches_via_alias():
    rw = _resolved_panos()
    items = RssSource(url=str(FIXTURES / "paloalto_psirt_rss.xml"),
                      _id="rss:psirt-0").fetch(LONG_AGO)
    assert len(items) == 3

    findings = [f for it in items if (f := evaluate(rw, Gates(), it))]
    # Only the "PAN-OS" advisory fires the alias; the GlobalProtect-only entries
    # do not (alias_safety: phrase, and "Palo Alto"/"PAN-OS" aren't in their text).
    assert len(findings) == 1
    f = findings[0]
    assert f.matched_rule == "alias"
    assert f.matched_on == "pan-os"
    assert "PAN-OS" in f.item.title
    assert f.item.source == "rss:psirt-0"      # _id tags which feed fired
