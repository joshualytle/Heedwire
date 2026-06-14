"""Core data models. Dependency-light and serialisable."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any

SECURITY_TERMS = (
    "vulnerab", "exploit", "cve-", "patch", "advisor", "0-day", "zero-day",
    "rce", "breach", "compromis", "malware", "ransomware", "hotfix",
)


class Severity(str, Enum):
    UNKNOWN = "unknown"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @classmethod
    def rank(cls, value: "Severity") -> int:
        return [cls.UNKNOWN, cls.LOW, cls.MEDIUM, cls.HIGH, cls.CRITICAL].index(value)


@dataclass
class Item:
    """A normalized advisory / news / forum item from a Source.

    `uid` MUST be stable across runs (CVE id, KEV id, RSS guid) — it is the
    de-duplication key.
    """

    source: str
    uid: str
    title: str
    url: str
    published: datetime | None = None
    severity: Severity = Severity.UNKNOWN
    score: float | None = None
    cve_ids: list[str] = field(default_factory=list)
    vendors: list[str] = field(default_factory=list)   # lowercased, e.g. ["fortinet"]
    products: list[str] = field(default_factory=list)   # lowercased, e.g. ["fortios"]
    packages: list[str] = field(default_factory=list)
    known_exploited: bool = False
    epss: float | None = None
    summary: str = ""
    ai_summary: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    def searchable_text(self) -> str:
        return " ".join(p for p in (self.title, self.summary) if p).lower()

    def has_security_term(self) -> bool:
        t = self.searchable_text()
        return any(term in t for term in SECURITY_TERMS)

    def to_wire(self) -> dict[str, Any]:
        d = asdict(self)
        d.pop("raw", None)
        d["severity"] = self.severity.value
        d["published"] = self.published.isoformat() if self.published else None
        return d


@dataclass
class Finding:
    item: Item
    matched_rule: str
    matched_on: str

    def to_wire(self) -> dict[str, Any]:
        d = self.item.to_wire()
        d["matched_rule"] = self.matched_rule
        d["matched_on"] = self.matched_on
        return d


def make_uid(*parts: str) -> str:
    return hashlib.sha256("\x1f".join(parts).encode()).hexdigest()[:16]
