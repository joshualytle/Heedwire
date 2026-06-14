"""Generic RSS/Atom adapter (vendor PSIRT feeds, advisory feeds, news).

Configure one per feed; matching against RSS items is alias-based via the
taxonomy. Set `_id` so matched items show which feed fired.
"""
from __future__ import annotations

import calendar
from datetime import datetime, timezone

import feedparser

from ..http import DEFAULT_TIMEOUT, session
from ..models import Item, make_uid
from ..severity import parse_severity
from .base import Source


class RssSource(Source):
    id = "rss"

    def fetch(self, since: datetime) -> list[Item]:
        url = self.options.get("url")
        if not url:
            raise ValueError(f"rss source {self.options.get('_id','')} missing 'url'")
        # Network goes through the shared session (explicit timeout + retry/backoff);
        # feedparser.parse does its own un-timed fetch, so we fetch the bytes first.
        # A local path/string (used by tests) is handed to feedparser directly.
        if url.startswith(("http://", "https://")):
            resp = session().get(url, timeout=DEFAULT_TIMEOUT)
            resp.raise_for_status()
            feed = feedparser.parse(resp.content)
        else:
            feed = feedparser.parse(url)
        if getattr(feed, "bozo", 0) and not feed.entries:
            raise ValueError(f"failed to parse feed {url}: {getattr(feed,'bozo_exception','')}")
        inst = self.options.get("_id", self.id)
        items: list[Item] = []
        for e in feed.entries:
            tm = e.get("published_parsed") or e.get("updated_parsed")
            # feedparser returns *_parsed as a UTC struct_time; use timegm (UTC),
            # not time.mktime (which assumes local time and shifts non-UTC hosts).
            published = datetime.fromtimestamp(calendar.timegm(tm), tz=timezone.utc) if tm else None
            if published and published < since:
                continue
            link = e.get("link", "")
            title = e.get("title", "(untitled)")
            summary = e.get("summary", "")
            items.append(Item(
                source=inst,
                uid=e.get("id") or e.get("guid") or make_uid(inst, link, title),
                title=title, url=link,
                published=published, summary=summary,
                # Read the vendor-stated severity (Severity:/SIR/CVSS) when present
                # so PSIRT advisories gate correctly; UNKNOWN when the feed says nothing.
                severity=parse_severity(f"{title} {summary}"),
            ))
        return items
