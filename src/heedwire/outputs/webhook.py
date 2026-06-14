"""Generic webhook output. Builds a payload for the configured chat platform.

Slack/Discord/Teams accept different JSON shapes, so pick `format`:
  slack   -> {"text": ...}        (Slack incoming webhook)
  discord -> {"content": ...}     (Discord webhook)
  teams   -> MessageCard          (Teams incoming webhook)
  text    -> {"text": ...}        (generic)
URL comes from an env var (never the config file).
"""
from __future__ import annotations

import os

from ..http import session
from ..models import Finding
from .base import Output


def _lines(findings: list[Finding]) -> list[str]:
    out = []
    for f in findings[:30]:
        it = f.item
        kev = " [KEV]" if it.known_exploited else ""
        cves = ", ".join(it.cve_ids[:3])
        out.append(f"• {it.title}{kev} ({cves or it.source}) — {it.url}")
    return out


class WebhookOutput(Output):
    id = "webhook"

    def send(self, findings: list[Finding]) -> None:
        if not findings:
            return
        url = os.environ.get(self.options.get("url_env", "HEEDWIRE_WEBHOOK_URL"))
        if not url:
            raise RuntimeError("webhook output enabled but URL env is not set")
        fmt = self.options.get("format", "slack")
        header = f"Heedwire: {len(findings)} new finding(s)"
        body = "\n".join(_lines(findings))
        text = f"*{header}*\n{body}"
        if fmt == "discord":
            payload = {"content": text[:1900]}
        elif fmt == "teams":
            payload = {"@type": "MessageCard", "@context": "http://schema.org/extensions",
                       "summary": header, "title": header, "text": body.replace("\n", "  \n")}
        else:  # slack / text
            payload = {"text": text}
        resp = session().post(url, json=payload, timeout=20)
        resp.raise_for_status()
