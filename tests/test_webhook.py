"""Webhook output tests: payload shapes per format, env-only URL, dedup-empty.

No network — the shared session is replaced with a capturing fake.
"""
from __future__ import annotations

import pytest

from heedwire.models import Finding, Item, Severity
from heedwire.outputs import webhook as wh
from heedwire.outputs.webhook import WebhookOutput


class _Resp:
    def raise_for_status(self) -> None:
        pass


class _Session:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def post(self, url, json=None, timeout=None):
        self.calls.append({"url": url, "json": json, "timeout": timeout})
        return _Resp()


@pytest.fixture
def fake_session(monkeypatch):
    s = _Session()
    monkeypatch.setattr(wh, "session", lambda: s)
    return s


def _findings(n=2):
    out = []
    for i in range(n):
        it = Item(source="kev", uid=f"CVE-{i}", title=f"Thing {i} Vulnerability",
                  url=f"https://nvd.nist.gov/vuln/detail/CVE-{i}",
                  severity=Severity.CRITICAL, cve_ids=[f"CVE-{i}"],
                  known_exploited=(i == 0))
        out.append(Finding(item=it, matched_rule="structured", matched_on="kev"))
    return out


def test_url_from_env_and_payload_sent(monkeypatch, fake_session):
    monkeypatch.setenv("HEEDWIRE_WEBHOOK_URL", "https://example/hook")
    WebhookOutput(format="slack").send(_findings())
    assert len(fake_session.calls) == 1
    assert fake_session.calls[0]["url"] == "https://example/hook"
    assert "text" in fake_session.calls[0]["json"]


def test_missing_env_raises(monkeypatch, fake_session):
    monkeypatch.delenv("HEEDWIRE_WEBHOOK_URL", raising=False)
    with pytest.raises(RuntimeError, match="URL env is not set"):
        WebhookOutput(format="slack").send(_findings())


def test_empty_findings_no_post(monkeypatch, fake_session):
    monkeypatch.setenv("HEEDWIRE_WEBHOOK_URL", "https://example/hook")
    WebhookOutput(format="slack").send([])
    assert fake_session.calls == []


def test_custom_url_env(monkeypatch, fake_session):
    monkeypatch.setenv("MY_HOOK", "https://example/custom")
    WebhookOutput(format="slack", url_env="MY_HOOK").send(_findings())
    assert fake_session.calls[0]["url"] == "https://example/custom"


def test_teams_workflow_adaptive_card(monkeypatch, fake_session):
    monkeypatch.setenv("HEEDWIRE_WEBHOOK_URL", "https://example/hook")
    WebhookOutput(format="teams_workflow").send(_findings())
    payload = fake_session.calls[0]["json"]
    assert payload["type"] == "message"
    att = payload["attachments"][0]
    assert att["contentType"] == "application/vnd.microsoft.card.adaptive"
    card = att["content"]
    assert card["type"] == "AdaptiveCard"
    assert card["body"][0]["text"] == "Heedwire: 2 new finding(s)"
    # KEV finding is tagged; finding links are present
    blocks = "\n".join(b["text"] for b in card["body"])
    assert "🔴 KEV" in blocks
    assert "https://nvd.nist.gov/vuln/detail/CVE-0" in blocks


def test_teams_workflow_caps_and_overflow(monkeypatch, fake_session):
    monkeypatch.setenv("HEEDWIRE_WEBHOOK_URL", "https://example/hook")
    WebhookOutput(format="teams_workflow").send(_findings(35))
    card = fake_session.calls[0]["json"]["attachments"][0]["content"]
    # header + 30 findings + 1 overflow note
    assert len(card["body"]) == 1 + 30 + 1
    assert "…and 5 more" in card["body"][-1]["text"]


def test_discord_and_teams_legacy_formats(monkeypatch, fake_session):
    monkeypatch.setenv("HEEDWIRE_WEBHOOK_URL", "https://example/hook")
    WebhookOutput(format="discord").send(_findings())
    assert "content" in fake_session.calls[0]["json"]
    WebhookOutput(format="teams").send(_findings())
    assert fake_session.calls[1]["json"]["@type"] == "MessageCard"
