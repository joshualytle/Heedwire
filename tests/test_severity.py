"""parse_severity: read a vendor-stated severity from advisory text only."""
from __future__ import annotations

import pytest

from heedwire.models import Severity
from heedwire.severity import classify, cvss_to_severity, estimate_severity, parse_severity


@pytest.mark.parametrize("score,expected", [
    (10.0, Severity.CRITICAL), (9.0, Severity.CRITICAL),
    (8.9, Severity.HIGH), (7.0, Severity.HIGH),
    (6.9, Severity.MEDIUM), (4.0, Severity.MEDIUM),
    (3.9, Severity.LOW), (0.1, Severity.LOW),
    (0.0, Severity.UNKNOWN),
])
def test_cvss_bands(score, expected):
    assert cvss_to_severity(score) is expected


def test_explicit_severity_word():            # Palo Alto style
    assert parse_severity("PAN-OS: ... (Severity: MEDIUM)") is Severity.MEDIUM


def test_cisco_security_impact_rating():      # Cisco SIR
    assert parse_severity("...Security Impact Rating: Critical...") is Severity.CRITICAL


def test_cvss_score_across_html_tags():       # Fortinet style
    assert parse_severity("<strong>CVSSv3 Score: </strong> 6.2") is Severity.MEDIUM
    assert parse_severity("CVSS v4.0 Base Score 9.1") is Severity.CRITICAL


def test_label_anchored_no_false_positive_on_prose():
    # "allow"/"below" contain "low" but must not be read as LOW severity.
    assert parse_severity("This could allow access to data below the threshold") is Severity.UNKNOWN


def test_empty_and_unstated():
    assert parse_severity("") is Severity.UNKNOWN
    assert parse_severity("A vulnerability was patched.") is Severity.UNKNOWN


# --- heuristic estimate (non-authoritative) ---

def test_estimate_by_vuln_class():
    assert estimate_severity("Authentication bypass in the admin portal") is Severity.CRITICAL
    assert estimate_severity("Remote code execution via crafted request") is Severity.HIGH
    assert estimate_severity("An RCE was found") is Severity.HIGH
    assert estimate_severity("Reflected cross-site scripting (XSS)") is Severity.MEDIUM
    assert estimate_severity("Open redirect on the login page") is Severity.MEDIUM


def test_estimate_acronyms_word_boundary():
    # "force"/"across"/"dose" must not trip the rce/xss/dos acronym matchers.
    assert estimate_severity("This will force a reload across the dose schedule") is Severity.UNKNOWN


def test_estimate_conservative_default_and_no_context():
    # Clearly an advisory but no class signal -> conservative MEDIUM guess.
    assert estimate_severity("Security advisory: a vulnerability was addressed") is Severity.MEDIUM
    # No vulnerability context at all -> no guess.
    assert estimate_severity("Quarterly product newsletter") is Severity.UNKNOWN


def test_classify_prefers_stated_over_guess():
    sev, est = classify("PAN-OS RCE issue (Severity: MEDIUM)")
    assert sev is Severity.MEDIUM and est is False        # stated wins, not guessed HIGH
    sev, est = classify("Remote code execution, no rating given")
    assert sev is Severity.HIGH and est is True           # guessed -> flagged estimated
    sev, est = classify("Quarterly product newsletter")
    assert sev is Severity.UNKNOWN and est is False       # bare unknown isn't 'estimated'
