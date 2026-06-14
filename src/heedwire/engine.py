"""Engine: one run = ingest -> store -> resolve -> match -> summarize -> deliver.

Per-source isolation (one dead feed never aborts a run), dedup via the store,
heartbeat on completion. The resolved watchlist's advisory_feeds are auto-added
as rss sources, so picking a vendor also pulls its PSIRT feed.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from .config import Config
from .http import session
from .matching import evaluate
from .models import Finding
from .outputs import REGISTRY as OUTPUTS
from .sources import REGISTRY as SOURCES
from .store import Store
from .summarizer import Summarizer
from .taxonomy import ResolvedWatch, load_taxonomy, resolve


@dataclass
class RunResult:
    fetched: int = 0
    new_items: int = 0
    findings: list[Finding] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def _window_start(cfg: Config, store: Store) -> datetime:
    now = datetime.now(timezone.utc)
    last = store.get_meta("last_run")
    if last:
        return min(datetime.fromisoformat(last) - timedelta(hours=1), now)
    return now - timedelta(hours=cfg.lookback_hours)


def _source_specs(cfg: Config, rw: ResolvedWatch) -> dict[str, dict]:
    specs = dict(cfg.sources)
    for i, feed in enumerate(sorted(rw.advisory_feeds)):
        specs[f"rss:psirt-{i}"] = {"type": "rss", "url": feed}
    return specs


def run_once(cfg: Config, *, deliver: bool = True) -> RunResult:
    store = Store(cfg.store_path)
    try:
        entries = load_taxonomy(cfg.taxonomy_path)
        rw = resolve(cfg.watch, entries)
        since = _window_start(cfg, store)
        result = RunResult()

        for name, spec in _source_specs(cfg, rw).items():
            if spec.get("enabled", True) is False:
                continue
            try:
                cls = SOURCES[spec.get("type", name.split(":")[0])]
                src = cls(**{k: v for k, v in spec.items() if k != "type"}, _id=name)
                items = src.fetch(since)
                result.fetched += len(items)
                for it in items:
                    if store.upsert(it):
                        result.new_items += 1
            except Exception as exc:  # per-source isolation
                result.errors.append(f"{name}: {type(exc).__name__}: {exc}")

        summarizer = Summarizer(**cfg.summarizer)
        notified: list[str] = []
        for it in store.unnotified():
            finding = evaluate(rw, cfg.gates, it)
            if not finding:
                continue
            finding.item.ai_summary = summarizer.summarize(finding)
            result.findings.append(finding)

        if deliver:
            for oname, ospec in cfg.outputs.items():
                if ospec.get("enabled", True) is False:
                    continue
                try:
                    ocls = OUTPUTS[ospec.get("type", oname)]
                    ocls(**{k: v for k, v in ospec.items() if k != "type"}).send(result.findings)
                except Exception as exc:
                    result.errors.append(f"output {oname}: {type(exc).__name__}: {exc}")
            notified = [f.item.uid for f in result.findings]
            store.mark_notified(notified)
            store.set_meta("last_run", datetime.now(timezone.utc).isoformat())
            _heartbeat(cfg, result)
        return result
    finally:
        store.close()


def _heartbeat(cfg: Config, result: RunResult) -> None:
    url = os.environ.get(cfg.heartbeat_env)
    if not url:
        return
    try:
        session().get(url.rstrip("/") + ("/fail" if result.errors else ""), timeout=10)
    except Exception:
        pass
