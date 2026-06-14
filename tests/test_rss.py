"""RSS/Atom source tests against a saved real feed sample (no network).

`tests/fixtures/atom_feed.xml` is a real Atom feed (trimmed to 3 entries),
recorded from a public GitHub feed. feedparser reads the local file directly,
so these tests never touch the network.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from heedwire.sources.rss import RssSource

FIXTURE = str(Path(__file__).parent / "fixtures" / "atom_feed.xml")
LONG_AGO = datetime(2000, 1, 1, tzinfo=timezone.utc)


def test_fetch_normalizes_atom_entries():
    items = RssSource(url=FIXTURE, _id="rss:test").fetch(LONG_AGO)
    assert len(items) == 3
    first = items[0]
    assert first.source == "rss:test"                      # _id tags the firing feed
    assert first.uid == "tag:github.com,2008:Grit::Commit/432051d5e341e6cd903d4175ee8e77e5e262b681"
    assert first.url.startswith("https://github.com/cisagov/kev-data/commit/")
    assert first.title == "Add Updated KEV Files for 2026-06-12"


def test_published_is_utc_not_tz_shifted():
    """Regression: feedparser *_parsed is UTC; the parser must not treat it as
    local time. The feed entry is 2026-06-12T18:45:20Z."""
    items = RssSource(url=FIXTURE).fetch(LONG_AGO)
    assert items[0].published == datetime(2026, 6, 12, 18, 45, 20, tzinfo=timezone.utc)


def test_fetch_applies_window():
    # Two entries are 2026-06-11, one is 2026-06-12; cut between them.
    items = RssSource(url=FIXTURE).fetch(datetime(2026, 6, 12, tzinfo=timezone.utc))
    assert [it.published.day for it in items] == [12]


def test_missing_url_raises():
    with pytest.raises(ValueError, match="missing 'url'"):
        RssSource(_id="rss:test").fetch(LONG_AGO)


def test_unparseable_feed_raises(tmp_path):
    bad = tmp_path / "bad.xml"
    bad.write_text("this is not a feed at all <<<>>>")
    with pytest.raises(ValueError, match="failed to parse feed"):
        RssSource(url=str(bad)).fetch(LONG_AGO)
