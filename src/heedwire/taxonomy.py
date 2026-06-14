"""Taxonomy: a curated data file of vendors/products/categories that users pick
from, resolved into concrete matchers BEFORE the matching layer runs.

This is what lets users select "Fortinet" or a category instead of writing
brittle keyword rules. One picked product fans out to the keys each source type
needs: structured CPE vendor/product, distro packages, and alias keywords (tagged
with a safety level so generic words don't flood the news/Reddit side).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class Entry:
    id: str
    vendor: str
    category: str
    cpe_vendor: str = ""
    cpe_product: str = ""
    packages: list[str] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)
    alias_safety: str = "phrase"          # exact | phrase | cooccur
    advisory_feed: str = ""


@dataclass
class ResolvedWatch:
    vendor_products: set[str] = field(default_factory=set)   # "vendor/product"
    vendors: set[str] = field(default_factory=set)           # subscribe to whole vendor
    packages: set[str] = field(default_factory=set)
    aliases: list[tuple[str, str]] = field(default_factory=list)   # (keyword_lower, safety)
    advisory_feeds: set[str] = field(default_factory=set)


def load_taxonomy(path: str | Path) -> list[Entry]:
    rows = yaml.safe_load(Path(path).read_text()) or []
    out: list[Entry] = []
    for r in rows:
        cpe = r.get("cpe", {}) or {}
        out.append(Entry(
            id=r["id"], vendor=r.get("vendor", ""), category=r.get("category", ""),
            cpe_vendor=(cpe.get("vendor", "") or "").lower(),
            cpe_product=(cpe.get("product", "") or "").lower(),
            packages=[p.lower() for p in r.get("packages", [])],
            aliases=r.get("aliases", []),
            alias_safety=r.get("alias_safety", "phrase"),
            advisory_feed=r.get("advisory_feed", ""),
        ))
    return out


def resolve(watch, entries: list[Entry]) -> ResolvedWatch:
    """Expand a user's picks (categories/vendors/products/custom) into matchers."""
    cats = {c.lower() for c in watch.categories}
    pick_vendors = set(watch.vendors)          # already lowercased in config
    pick_products = set(watch.products)

    rw = ResolvedWatch()

    def add_entry(e: Entry) -> None:
        if e.cpe_product:
            rw.vendor_products.add(f"{e.cpe_vendor}/{e.cpe_product}")
        rw.packages.update(e.packages)
        for a in e.aliases:
            rw.aliases.append((a.lower(), e.alias_safety))
        if e.advisory_feed:
            rw.advisory_feeds.add(e.advisory_feed)

    for e in entries:
        if (e.category.lower() in cats or e.vendor.lower() in pick_vendors
                or e.id.lower() in pick_products):
            add_entry(e)
        if e.vendor.lower() in pick_vendors:
            rw.vendors.add(e.cpe_vendor or e.vendor.lower())

    for c in watch.custom:                     # ad-hoc, never blocked on the taxonomy
        cpe = c.get("cpe", {}) or {}
        if cpe.get("product"):
            rw.vendor_products.add(f"{cpe.get('vendor','').lower()}/{cpe['product'].lower()}")
        if cpe.get("vendor") and not cpe.get("product"):
            rw.vendors.add(cpe["vendor"].lower())
        rw.packages.update(p.lower() for p in c.get("packages", []))
        for a in c.get("aliases", []):
            rw.aliases.append((a.lower(), c.get("alias_safety", "phrase")))
    return rw
