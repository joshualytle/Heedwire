"""Local SQLite store: dedup, offline cache, and the read source for the API.

Keeps items, a 'notified' timestamp (so we never re-alert), and a meta table
(last_run). Privacy note: stores only the broad public items + a last_run
timestamp; it never needs the watchlist to function.
"""
from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from .models import Item, Severity

_SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
  uid TEXT PRIMARY KEY,
  source TEXT NOT NULL,
  published TEXT,
  first_seen TEXT NOT NULL,
  notified TEXT,
  data TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_items_first_seen ON items(first_seen);
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);
"""


class Store:
    def __init__(self, path: str | Path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(path))
        self.conn.row_factory = sqlite3.Row
        with closing(self.conn.cursor()) as cur:
            cur.executescript(_SCHEMA)
        self.conn.commit()

    def upsert(self, item: Item) -> bool:
        """Insert if new. Returns True if this uid was not seen before."""
        now = datetime.now(timezone.utc).isoformat()
        data = json.dumps(item.to_wire())
        pub = item.published.isoformat() if item.published else None
        with closing(self.conn.cursor()) as cur:
            cur.execute("SELECT 1 FROM items WHERE uid=?", (item.uid,))
            exists = cur.fetchone() is not None
            if exists:
                cur.execute("UPDATE items SET data=?, published=? WHERE uid=?",
                            (data, pub, item.uid))
            else:
                cur.execute(
                    "INSERT INTO items(uid, source, published, first_seen, data) "
                    "VALUES(?,?,?,?,?)", (item.uid, item.source, pub, now, data))
        self.conn.commit()
        return not exists

    def unnotified(self) -> list[Item]:
        with closing(self.conn.cursor()) as cur:
            cur.execute("SELECT data FROM items WHERE notified IS NULL")
            return [_item_from_row(r["data"]) for r in cur.fetchall()]

    def mark_notified(self, uids: list[str]) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with closing(self.conn.cursor()) as cur:
            cur.executemany("UPDATE items SET notified=? WHERE uid=?",
                            [(now, u) for u in uids])
        self.conn.commit()

    def recent(self, since: datetime | None = None, limit: int = 200) -> list[dict]:
        with closing(self.conn.cursor()) as cur:
            if since:
                cur.execute("SELECT data FROM items WHERE first_seen>=? "
                            "ORDER BY first_seen DESC LIMIT ?",
                            (since.isoformat(), limit))
            else:
                cur.execute("SELECT data FROM items ORDER BY first_seen DESC LIMIT ?",
                            (limit,))
            return [json.loads(r["data"]) for r in cur.fetchall()]

    def get_meta(self, key: str) -> str | None:
        with closing(self.conn.cursor()) as cur:
            cur.execute("SELECT value FROM meta WHERE key=?", (key,))
            row = cur.fetchone()
            return row["value"] if row else None

    def set_meta(self, key: str, value: str) -> None:
        with closing(self.conn.cursor()) as cur:
            cur.execute("INSERT INTO meta(key,value) VALUES(?,?) "
                        "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()


def _item_from_row(data: str) -> Item:
    d = json.loads(data)
    pub = d.get("published")
    return Item(
        source=d["source"], uid=d["uid"], title=d["title"], url=d["url"],
        published=datetime.fromisoformat(pub) if pub else None,
        severity=Severity(d.get("severity", "unknown")), score=d.get("score"),
        cve_ids=d.get("cve_ids", []), vendors=d.get("vendors", []),
        products=d.get("products", []), packages=d.get("packages", []),
        known_exploited=d.get("known_exploited", False), epss=d.get("epss"),
        summary=d.get("summary", ""), ai_summary=d.get("ai_summary"),
    )
