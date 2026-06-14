"""Configuration loading. Secrets come from env, never the file."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .models import Severity


@dataclass
class Watch:
    categories: list[str] = field(default_factory=list)
    vendors: list[str] = field(default_factory=list)
    products: list[str] = field(default_factory=list)
    custom: list[dict] = field(default_factory=list)


@dataclass
class Gates:
    min_severity: Severity = Severity.UNKNOWN
    only_known_exploited: bool = False
    epss_min: float | None = None


@dataclass
class Config:
    sources: dict[str, dict[str, Any]] = field(default_factory=dict)
    outputs: dict[str, dict[str, Any]] = field(default_factory=dict)
    watch: Watch = field(default_factory=Watch)
    gates: Gates = field(default_factory=Gates)
    lookback_hours: int = 25
    interval_minutes: int = 1440
    store_path: str = "data/heedwire.db"
    taxonomy_path: str = "data/taxonomy.yaml"
    heartbeat_env: str = "HEEDWIRE_HEARTBEAT_URL"
    summarizer: dict[str, Any] = field(default_factory=lambda: {"enabled": False})
    api_host: str = "127.0.0.1"
    api_port: int = 8787


def load_config(path: str | Path) -> Config:
    raw = yaml.safe_load(Path(path).read_text()) or {}
    w = raw.get("watch", {}) or {}
    g = raw.get("gates", {}) or {}
    return Config(
        sources=raw.get("sources", {}) or {},
        outputs=raw.get("outputs", {}) or {},
        watch=Watch(
            categories=w.get("categories", []), vendors=[v.lower() for v in w.get("vendors", [])],
            products=[p.lower() for p in w.get("products", [])], custom=w.get("custom", []),
        ),
        gates=Gates(
            min_severity=Severity(g.get("min_severity", "unknown")),
            only_known_exploited=bool(g.get("only_known_exploited", False)),
            epss_min=g.get("epss_min"),
        ),
        lookback_hours=int(raw.get("lookback_hours", 25)),
        interval_minutes=int(raw.get("interval_minutes", 1440)),
        store_path=raw.get("store_path", "data/heedwire.db"),
        taxonomy_path=raw.get("taxonomy_path", "data/taxonomy.yaml"),
        heartbeat_env=raw.get("heartbeat_env", "HEEDWIRE_HEARTBEAT_URL"),
        summarizer=raw.get("summarizer", {"enabled": False}) or {"enabled": False},
        api_host=raw.get("api_host", "127.0.0.1"),
        api_port=int(raw.get("api_port", 8787)),
    )
