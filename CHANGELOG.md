# Changelog

All notable changes to Heedwire are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Every user-facing change must update the `[Unreleased]` section in the same PR.

## [Unreleased]

### Added
- Advisory severity parsing: RSS/PSIRT items now carry the **vendor-stated**
  severity when the feed publishes one — an explicit `Severity:`, Cisco's
  `Security Impact Rating`, or a CVSS base score mapped to its qualitative band
  (`heedwire.severity.parse_severity`). This is read, never invented; items whose
  feed states nothing stay `unknown`. Fixes advisory feeds being silently dropped
  by the `min_severity` gate (e.g. high/critical PSIRT advisories now deliver
  under the shipped `min_severity: high`).
- Heuristic severity estimate: when a feed states no severity, Heedwire infers a
  **non-authoritative** band from the advisory's vulnerability-class wording
  (`heedwire.severity.estimate_severity`) so a likely-serious advisory isn't
  silently dropped. It is deterministic (no model), flagged `est.` in webhook
  output and exposed as `severity_estimated` on the API, and never presented as
  the vendor's own rating.
- `.env.example` template for the secrets Heedwire reads from the environment
  (`HEEDWIRE_WEBHOOK_URL`, optional `HEEDWIRE_HEARTBEAT_URL`). Copy it to `.env`
  and fill in; `docker compose` loads it automatically. Keeps secret
  provisioning out of `config.yaml` and the image for self-hosters.
- Initial project scaffolding, repository documentation, and engineering ruleset.
- Starter vendor PSIRT advisory RSS feeds wired into the taxonomy for Fortinet,
  Cisco, and Palo Alto; selecting those vendors (or the Firewalls category)
  auto-adds their advisory feed as an `rss` source.
- Teams delivery via Power Automate **Workflows** (`format: teams_workflow`):
  posts an Adaptive Card to the Workflows webhook that replaces the retired
  Office 365 connector. The legacy `teams` MessageCard format is retained.
- Deployment and taxonomy guides (`docs/deployment.md`, `docs/taxonomy.md`)
  covering the outbound network allowlist, the heartbeat, Teams setup,
  persistence, and alias-safety levels; heartbeat documented in the example config.

### Changed
- README now states the shipped v1 scope honestly (CISA KEV + advisory RSS →
  webhook + local API) with a clear roadmap, instead of implying news/Reddit/AI
  summaries already work.
- RSS source now fetches through the shared HTTP session (explicit timeout +
  retry/backoff) instead of feedparser's un-timed fetch.

### Fixed
- Docker build failed because `.dockerignore`'s `*.md` excluded `README.md`,
  which the Dockerfile copies (pip needs it — `pyproject.toml` sets
  `readme = "README.md"`). Re-include it with `!README.md`.
- CI `gitleaks` job failed: gitleaks-action v2 requires a `GITHUB_TOKEN` to scan
  pull requests. Pass the token and check out full history so it can diff the
  PR range.
- KEV source now strips stray whitespace from the free-text `vendorProject` and
  `product` fields (present in the live CISA catalog), so exact structured
  matching is not silently defeated.
- RSS source parsed feed timestamps as local time, shifting `published` times
  (and the window filter) on non-UTC hosts; they are now correctly read as UTC.

### Security
- Bumped the SHA-pinned CI actions to their current Node.js 24 releases so the
  pipeline keeps working past GitHub's June 16 2026 removal of the Node 20 runner:
  `actions/checkout` v6.0.3, `actions/setup-python` v6.2.0, and
  `gitleaks/gitleaks-action` v3.0.0. Still pinned to commit SHAs, not tags.

<!--
Group entries under: Added / Changed / Deprecated / Removed / Fixed / Security.
On release: move [Unreleased] into a new "## [x.y.z] - YYYY-MM-DD" section.
-->
