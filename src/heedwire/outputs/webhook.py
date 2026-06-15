"""Generic webhook output. Builds a payload for the configured chat platform.

Slack/Discord/Teams accept different JSON shapes, so pick `format`:
  slack          -> {"text": ...}                 (Slack incoming webhook)
  discord        -> {"content": ...}               (Discord webhook)
  teams_workflow -> Adaptive Card in a Workflows   (Power Automate "Workflows"
                    message envelope                 webhook — the supported
                                                     Teams path; see note below)
  teams          -> MessageCard                    (legacy O365 connector shape;
                                                     also accepted by Workflows)
  text           -> {"text": ...}                  (generic)

Teams note: Microsoft retired Office 365 Connectors (the classic "Incoming
Webhook") in Teams in 2026. The replacement is a Power Automate **Workflows**
webhook ("Post to a channel when a webhook request is received"), which yields a
URL Heedwire POSTs to. `teams_workflow` sends the Adaptive Card payload that
trigger expects; `teams` sends the legacy MessageCard, which Workflows still
accept. Prefer `teams_workflow` for new setups.

The webhook URL always comes from an env var (never the config file).
"""
from __future__ import annotations

import os

from ..http import session
from ..models import Finding, Item, Severity
from .base import Output

MAX_ITEMS = 30


def _sev_tag(it: Item) -> str:
    """`[HIGH] ` / `[HIGH est.] ` — the 'est.' flags a heuristic guess, not the
    source's own rating. Empty when severity is unknown."""
    if it.severity is Severity.UNKNOWN:
        return ""
    return f"[{it.severity.value.upper()}{' est.' if it.severity_estimated else ''}] "


def _lines(findings: list[Finding]) -> list[str]:
    out = []
    for f in findings[:MAX_ITEMS]:
        it = f.item
        kev = " [KEV]" if it.known_exploited else ""
        cves = ", ".join(it.cve_ids[:3])
        out.append(f"• {_sev_tag(it)}{it.title}{kev} ({cves or it.source}) — {it.url}")
    return out


def _adaptive_card(findings: list[Finding]) -> dict:
    """Build an Adaptive Card body summarizing the findings (links, KEV tag)."""
    header = f"Heedwire: {len(findings)} new finding(s)"
    body: list[dict] = [
        {"type": "TextBlock", "size": "Large", "weight": "Bolder",
         "text": header, "wrap": True},
    ]
    for f in findings[:MAX_ITEMS]:
        it = f.item
        tag = "🔴 KEV · " if it.known_exploited else ""
        meta = ", ".join(it.cve_ids[:3]) or it.source
        body.append({"type": "TextBlock", "wrap": True,
                     "text": f"{tag}{_sev_tag(it)}[{it.title}]({it.url}) — {meta}"})
    if len(findings) > MAX_ITEMS:
        body.append({"type": "TextBlock", "isSubtle": True, "wrap": True,
                     "text": f"…and {len(findings) - MAX_ITEMS} more"})
    return {"$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "type": "AdaptiveCard", "version": "1.4", "body": body}


def _build_payload(fmt: str, findings: list[Finding]) -> dict:
    header = f"Heedwire: {len(findings)} new finding(s)"
    body = "\n".join(_lines(findings))
    text = f"*{header}*\n{body}"
    if fmt == "discord":
        return {"content": text[:1900]}
    if fmt == "teams_workflow":
        # The Workflows trigger expects an Adaptive Card wrapped as a message
        # attachment with this contentType.
        return {"type": "message", "attachments": [
            {"contentType": "application/vnd.microsoft.card.adaptive",
             "contentUrl": None, "content": _adaptive_card(findings)}]}
    if fmt == "teams":
        return {"@type": "MessageCard", "@context": "http://schema.org/extensions",
                "summary": header, "title": header, "text": body.replace("\n", "  \n")}
    return {"text": text}  # slack / text


class WebhookOutput(Output):
    id = "webhook"

    def send(self, findings: list[Finding]) -> None:
        if not findings:
            return
        url = os.environ.get(self.options.get("url_env", "HEEDWIRE_WEBHOOK_URL"))
        if not url:
            raise RuntimeError("webhook output enabled but URL env is not set")
        payload = _build_payload(self.options.get("format", "slack"), findings)
        resp = session().post(url, json=payload, timeout=20)
        resp.raise_for_status()
