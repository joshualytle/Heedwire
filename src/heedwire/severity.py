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


# --- Heuristic estimate (NON-AUTHORITATIVE) ---------------------------------
# When a feed states no severity, we *guess* one from vulnerability-class clues
# in the text so a likely-serious advisory isn't silently dropped by the gate.
# This is an explicit guess, labelled as estimated wherever it surfaces — never
# presented as the vendor's rating. Substring phrases are matched on tag-stripped
# lowercased text; short acronyms use word boundaries to avoid false hits
# ("rce" vs "force", "dos" vs "dose").
_CRIT_PHRASES = ("authentication bypass", "auth bypass", "actively exploited",
                 "exploited in the wild", "in the wild", "wormable",
                 "missing authentication")
_HIGH_PHRASES = ("remote code execution", "arbitrary code", "privilege escalation",
                 "command injection", "sql injection", "insecure deserialization",
                 "deserialization of untrusted", "path traversal", "directory traversal",
                 "use after free", "buffer overflow", "heap overflow", "stack overflow")
_MED_PHRASES = ("cross-site scripting", "cross-site request forgery", "request forgery",
                "information disclosure", "sensitive information", "denial of service",
                "improper access control", "access control", "open redirect")
_HIGH_ACRONYMS = re.compile(r"\b(rce)\b", re.I)
_MED_ACRONYMS = re.compile(r"\b(xss|csrf|ssrf|dos)\b", re.I)
# Generic markers that this is a vulnerability advisory at all (so we don't guess
# a severity for unrelated news/chatter).
_VULN_CONTEXT = ("vulnerab", "exploit", "cve-", "advisor", "security update", "patch")


def estimate_severity(text: str) -> Severity:
    """Heuristic, non-authoritative severity guess from vuln-class clues.

    CRITICAL/HIGH/MEDIUM by the worst signal present; a conservative MEDIUM when
    it's clearly an advisory but no class stands out; UNKNOWN when there's no
    vulnerability context to guess from. Deterministic — never calls a model.
    """
    if not text:
        return Severity.UNKNOWN
    clean = _TAGS.sub(" ", text).lower()
    if any(p in clean for p in _CRIT_PHRASES):
        return Severity.CRITICAL
    if any(p in clean for p in _HIGH_PHRASES) or _HIGH_ACRONYMS.search(clean):
        return Severity.HIGH
    if any(p in clean for p in _MED_PHRASES) or _MED_ACRONYMS.search(clean):
        return Severity.MEDIUM
    if any(c in clean for c in _VULN_CONTEXT):
        return Severity.MEDIUM
    return Severity.UNKNOWN


def classify(text: str) -> tuple[Severity, bool]:
    """Resolve a severity for free text. Returns (severity, estimated).

    Prefer the vendor-stated severity (estimated=False). Only when none is stated
    do we fall back to the heuristic guess (estimated=True), so callers can label
    it honestly. A bare UNKNOWN is never marked estimated.
    """
    stated = parse_severity(text)
    if stated is not Severity.UNKNOWN:
        return stated, False
    guess = estimate_severity(text)
    return guess, guess is not Severity.UNKNOWN
