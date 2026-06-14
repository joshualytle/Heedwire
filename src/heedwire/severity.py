"""Parse a *vendor-stated* severity out of advisory free text.

Grounded, not invented: we only read a severity the source itself published —
an explicit "Severity: High" / Cisco "Security Impact Rating", or a CVSS base
score mapped to the standard qualitative band. When the source states nothing we
return UNKNOWN (the caller decides how to gate that). This deliberately never
guesses a severity from prose; inferring one is a separate, gated concern.
"""
from __future__ import annotations

import re

from .models import Severity

_TAGS = re.compile(r"<[^>]+>")
# Explicit textual rating, anchored to a label so body prose ("allow", "below")
# can't be misread as "low". Covers "Severity: High" and Cisco's "Security
# Impact Rating: Critical".
_WORD = re.compile(
    r"(?:security impact rating|severity)\s*[:\-]?\s*(critical|high|medium|low)", re.I)
# CVSS base score, e.g. "CVSSv3 Score: 6.2" / "CVSS v4.0 Base Score 9.1".
_CVSS = re.compile(r"cvss\s*v?[\d.]*\s*(?:base\s*)?score\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)?)", re.I)

_WORDS = {"critical": Severity.CRITICAL, "high": Severity.HIGH,
          "medium": Severity.MEDIUM, "low": Severity.LOW}


def cvss_to_severity(score: float) -> Severity:
    """Map a CVSS v3/v4 base score to its standard qualitative band."""
    if score >= 9.0:
        return Severity.CRITICAL
    if score >= 7.0:
        return Severity.HIGH
    if score >= 4.0:
        return Severity.MEDIUM
    if score >= 0.1:
        return Severity.LOW
    return Severity.UNKNOWN


def parse_severity(text: str) -> Severity:
    """Best-effort extraction of a vendor-stated severity; UNKNOWN if none found."""
    if not text:
        return Severity.UNKNOWN
    clean = _TAGS.sub(" ", text)
    m = _WORD.search(clean)
    if m:
        return _WORDS[m.group(1).lower()]
    m = _CVSS.search(clean)
    if m:
        return cvss_to_severity(float(m.group(1)))
    return Severity.UNKNOWN
