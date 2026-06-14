"""Matching: does an Item match the resolved watchlist, and pass the gates.

Structured fields (vendor/product, packages, cve) match EXACTLY. Aliases are the
only fuzzy path and honor a per-entry safety level so generic words (e.g.
"Windows", "Access") don't flood the news/Reddit side.
"""
from __future__ import annotations

import re

from .config import Gates
from .models import Finding, Item, Severity
from .taxonomy import ResolvedWatch


def _structured_match(rw: ResolvedWatch, item: Item) -> str | None:
    for v in item.vendors:
        for p in item.products:
            if f"{v}/{p}" in rw.vendor_products:
                return f"{v}/{p}"
        if v in rw.vendors:
            return v
    hit = set(item.packages) & rw.packages
    if hit:
        return sorted(hit)[0]
    return None


def _alias_match(rw: ResolvedWatch, item: Item) -> str | None:
    text = item.searchable_text()
    for kw, safety in rw.aliases:
        if safety == "exact":
            if re.search(rf"\b{re.escape(kw)}\b", text):
                return kw
        elif safety == "phrase":
            if kw in text:
                return kw
        elif safety == "cooccur":
            if re.search(rf"\b{re.escape(kw)}\b", text) and item.has_security_term():
                return kw
    return None


def passes_gates(gates: Gates, item: Item) -> bool:
    if gates.only_known_exploited and not item.known_exploited:
        return False
    if not item.known_exploited:  # KEV bypasses the floors: active exploitation wins
        if Severity.rank(item.severity) < Severity.rank(gates.min_severity):
            return False
        if gates.epss_min is not None and (item.epss is None or item.epss < gates.epss_min):
            return False
    return True


def evaluate(rw: ResolvedWatch, gates: Gates, item: Item) -> Finding | None:
    hit = _structured_match(rw, item)
    rule = "structured"
    if not hit:
        hit = _alias_match(rw, item)
        rule = "alias"
    if hit and passes_gates(gates, item):
        return Finding(item=item, matched_rule=rule, matched_on=hit)
    return None
