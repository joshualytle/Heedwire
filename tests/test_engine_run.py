"""Engine integration: one offline run end-to-end (ingest -> store -> resolve ->
match -> gate -> dedup), then a second run proving dedup.

Fully offline: the source is a local fixture feed and the watch picks a taxonomy
entry with no advisory_feed (vmware.esxi), so the engine never reaches out to a
live PSIRT URL. No webhook env is needed — with no outputs configured the deliver
phase is a no-op, but the run still marks findings notified (the dedup boundary).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from heedwire.config import Config, Gates, Watch
from heedwire.engine import run_once
from heedwire.models import Severity

FEED = str(Path(__file__).parent / "fixtures" / "engine_feed.xml")
TAXONOMY = str(Path(__file__).parents[1] / "data" / "taxonomy.yaml")


@pytest.fixture
def cfg(tmp_path, monkeypatch):
    monkeypatch.delenv("HEEDWIRE_HEARTBEAT_URL", raising=False)
    return Config(
        store_path=str(tmp_path / "engine.db"),
        sources={"rss:test": {"type": "rss", "url": FEED}},
        outputs={},                                   # deliver phase no-ops, dedup still runs
        watch=Watch(products=["vmware.esxi"]),        # no advisory_feed -> stays offline
        gates=Gates(min_severity=Severity.HIGH),
        taxonomy_path=TAXONOMY,
        lookback_hours=24 * 36500,                    # include the fixture's fixed dates
    )


def test_run_once_filters_and_gates(cfg):
    r = run_once(cfg, deliver=True)
    assert r.errors == []
    assert r.fetched == 2 and r.new_items == 2        # both items ingested + stored
    # Only the ESXi item matches the alias AND clears the high gate (parsed High);
    # the unrelated item is stored but never becomes a finding.
    assert len(r.findings) == 1
    f = r.findings[0]
    assert "ESXi" in f.item.title
    assert f.matched_rule == "alias" and f.item.severity is Severity.HIGH


def test_second_run_dedups(cfg):
    run_once(cfg, deliver=True)
    r2 = run_once(cfg, deliver=True)
    assert r2.findings == []                          # already notified -> nothing re-delivered
    assert r2.new_items == 0
