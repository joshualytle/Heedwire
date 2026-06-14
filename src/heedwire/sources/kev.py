"""CISA Known Exploited Vulnerabilities. Full public JSON, filtered locally."""
from __future__ import annotations

from datetime import datetime, timezone

from ..http import get_json
from ..models import Item, Severity, make_uid
from .base import Source

KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"


class KevSource(Source):
    id = "kev"

    def fetch(self, since: datetime) -> list[Item]:
        data = get_json(self.options.get("url", KEV_URL))
        if "vulnerabilities" not in data:
            raise ValueError("KEV feed shape unexpected: missing 'vulnerabilities'")
        items: list[Item] = []
        for v in data["vulnerabilities"]:
            added = v.get("dateAdded")
            published = (datetime.fromisoformat(added).replace(tzinfo=timezone.utc)
                         if added else None)
            if published and published < since:
                continue
            cve = v.get("cveID", "").strip()
            # KEV vendorProject/product are free text and occasionally carry stray
            # leading/trailing whitespace in the live catalog; normalize so exact
            # structured matching isn't silently defeated.
            vendor = (v.get("vendorProject") or "").strip().lower()
            product = (v.get("product") or "").strip().lower()
            items.append(Item(
                source=self.id,
                uid=cve or make_uid("kev", v.get("vulnerabilityName", "")),
                title=v.get("vulnerabilityName", cve),
                url=f"https://nvd.nist.gov/vuln/detail/{cve}",
                published=published, severity=Severity.CRITICAL,
                cve_ids=[cve] if cve else [],
                vendors=[vendor] if vendor else [],
                products=[product] if product else [],
                known_exploited=True, summary=v.get("shortDescription", ""), raw=v,
            ))
        return items
