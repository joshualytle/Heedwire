"""On-device / BYO LLM summary seam. OFF by default; returns a safe placeholder
when disabled so the whole tool runs without any model.

Rules when enabled (see CLAUDE.md): grounded (summarize only the linked source),
source-linked, non-authoritative, no republishing of article text. Only this
module imports a model client.
"""
from __future__ import annotations

from .models import Finding


class Summarizer:
    def __init__(self, **options) -> None:
        self.enabled = bool(options.get("enabled", False))
        self.options = options

    def summarize(self, finding: Finding) -> str | None:
        if not self.enabled:
            return None
        # TODO(claude-code): call the configured local/BYO model here, grounded on
        # finding.item.summary + the fetched source. Until then, a non-AI fallback:
        text = finding.item.summary.strip()
        return (text[:280] + "...") if len(text) > 280 else text or None
