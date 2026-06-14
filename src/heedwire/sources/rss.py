"""Generic RSS/Atom adapter (vendor PSIRT feeds, advisory feeds, news).

Configure one per feed; matching against RSS items is alias-based via the
taxonomy. Set `_id` so matched items show which feed fired.
"""
from __future__ import annotations

from datetime import datetime, timezone
from time import mktime

import feedparser

from ..models import Item, make_uid
from .base import Source


class RssSource(Source):
    id = "rss"

    def fetch(self, since: datetime) -> list[Item]:
        url = self.options.get("url")
        if not url:
            raise ValueError(f"rss source {self.options.get('_id','')} missing 'url'")
        feed = feedparser.parse(url)
        if getattr(feed, "bozo", 0) and not feed.entries:
            raise ValueError(f"failed to parse feed {url}: {getattr(feed,'bozo_exception','')}")
        inst = self.options.get("_id", self.id)
        items: list[Item] = []
        for e in feed.entries:
            tm = e.get("published_parsed") or e.get("updated_parsed")
            published = datetime.fromtimestamp(mktime(tm), tz=timezone.utc) if tm else None
            if published and published < since:
                continue
            link = e.get("link", "")
            items.append(Item(
                source=inst,
                uid=e.get("id") or e.get("guid") or make_uid(inst, link, e.get("title", "")),
                title=e.get("title", "(untitled)"), url=link,
                published=published, summary=e.get("summary", ""),
            ))
        return items
