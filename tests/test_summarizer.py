"""Summarizer seam: OFF by default, never fabricates, runs without any model.

Guards the v1 promise that the whole tool runs without a model: disabled returns
a safe placeholder, and the enabled fallback only ever echoes (truncated) source
text — it never invents content. No model client is imported here.
"""
from __future__ import annotations

from heedwire.models import Finding, Item
from heedwire.summarizer import Summarizer


def _finding(summary: str) -> Finding:
    it = Item(source="rss:psirt-0", uid="u", title="t", url="x", summary=summary)
    return Finding(item=it, matched_rule="alias", matched_on="x")


def test_disabled_by_default_returns_placeholder():
    assert Summarizer().summarize(_finding("anything")) is None
    assert Summarizer(enabled=False).summarize(_finding("anything")) is None


def test_enabled_fallback_is_grounded_and_truncated():
    s = Summarizer(enabled=True)
    # echoes the source text verbatim when short (grounded — nothing invented)
    assert s.summarize(_finding("A short advisory note.")) == "A short advisory note."
    # truncates long source text rather than republishing it whole
    out = s.summarize(_finding("x" * 400))
    assert out.endswith("...") and len(out) == 283
    # nothing to summarize -> placeholder, never a fabricated sentence
    assert s.summarize(_finding("   ")) is None
