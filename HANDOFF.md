# Heedwire — Handoff & Build Plan

For the Claude Code session building Heedwire. This is *what* to build; `CLAUDE.md`
is *how* (read it first). Heedwire is a free, self-hostable security **signal**
monitor: watch advisory feeds, security news, and Reddit/forum chatter; filter to
the user's stack via a curated taxonomy; optionally summarize; push what matters.

---

## 0. Prime directive — ship a focused v1

Value comes from **finishing** a small, dependable, honest tool. Build the v1 in
§5 and stop; everything else is a documented fast-follow. Resist scope creep —
surface it to the human instead of building it.

**OUT of scope for v1** (design the seams, don't build the feature yet): the
news source, the Reddit source, AI summaries, a web UI/PWA, multi-user/auth, a
separate companion app. v1 proves the spine works end to end.

---

## 1. What it is / positioning

Structured CVE monitors (OpenCVE et al.) already cover advisory databases well.
Heedwire is complementary and deliberately small:
- **Chatter signal** nobody else surfaces: news + Reddit for "is this patch safe /
  Patch Tuesday is breaking things," which never appears in a CVE database.
- **Pick, don't write rules**: a curated taxonomy of categories/vendors/products.
- **One container, no DB to stand up**: alerting in minutes.
- **Responsible AI summaries**: grounded, source-linked, security-aware.

Honesty is a feature — this audience punishes overclaiming.

---

## 2. Architecture (concern split, single deployment)

```
        ┌────────────────────────── one Docker container ──────────────────────────┐
        │  FEEDER (ingest)            RESOLVE+FILTER            ENRICH      DELIVER   │
PUBLIC  │  sources → normalize →   ── taxonomy.resolve() →  ── summarize → notify ──►│─► webhook
FEEDS ─►│  STORE (SQLite, volume)     match(watchlist)         (optional)            │   (Teams/Slack)
        │       │                     + severity/KEV gates                            │
        │       └──── read-only local API (/healthz /findings /sources) ─────────────┼─► (future UI/companion)
        │  scheduler (loop) · heartbeat (dead-man's-switch)                           │
        └─────────────────────────────────────────────────────────────────────────────┘
```

- **Feeder** pulls each source's broad/recent feed (no per-watchlist upstream
  queries), normalizes to one `Item`, stores in SQLite on a mounted volume.
- **Taxonomy resolve** turns the user's picks into structured matchers + alias
  keyword sets *before* matching (the matching layer stays generic).
- **Filter** matches stored items against the resolved watchlist + severity/KEV
  gates; dedupes by stable uid.
- **Enrich** (optional, off by default) adds a grounded summary.
- **Deliver** posts new findings to a webhook.
- **Local API** is the seam (alert rules live server-side; a future PWA/companion
  is a read/browse consumer). One process, one container for v1.

Decided earlier and not to be re-litigated: alert rules are **server-side** (they
drive scheduled pushes when no browser is open); view filtering is client-side UX;
auth is for **exposure/multi-user**, not privacy (single-tenant self-host = the
operator is the user). Localhost bind by default.

---

## 3. Sources & realistic data (no search scraping)

| Source | v1? | How |
|---|---|---|
| `kev` (CISA KEV) | **yes** | full public JSON, filter local |
| `psirt`/`rss` (vendor PSIRT + advisory RSS) | **yes** | per-feed RSS via feedparser |
| `usn` (Ubuntu) | fast-follow | notices API, date-windowed |
| `nvd` | fast-follow | NVD 2.0 date-window; CVSS V40→V31→V30→V2; KEV bypasses floor |
| `news` | fast-follow | security-news RSS + **Google Alerts exported as RSS**; optional GDELT / Brave Search API free tiers. **The Bing Search API was retired (Aug 2025); Google has no free general search API — do not scrape.** |
| `reddit` | fast-follow | official Reddit API (OAuth, rate-limited); watch chosen subs (r/sysadmin, r/msp, etc.) for taxonomy aliases |

All sources implement one `Source` contract; matching is uniform downstream.

---

## 4. The taxonomy (the filtering layer)

Ships as `data/taxonomy.yaml`. Each entry carries the keys each source type needs,
because sources speak different languages:

```yaml
- id: fortinet.fortios
  vendor: Fortinet
  category: Network Security / Firewalls
  cpe: { vendor: fortinet, product: fortios }   # KEV/NVD structured match
  packages: []                                   # distro package names (USN)
  aliases: ["FortiOS", "FortiGate"]              # news/Reddit keyword match
  alias_safety: phrase                           # exact | phrase | cooccur
  advisory_feed: https://.../fortinet-psirt.rss  # optional vendor PSIRT
```

User-facing config selects at three levels; the engine unions them:

```yaml
watch:
  categories: ["Network Security / Firewalls", "Remote Access / VPN"]
  vendors: [Microsoft, Fortinet, Ivanti]
  products: [fortinet.fortios, microsoft.windows_server]
  custom: []          # ad-hoc entries so users are never blocked on the taxonomy
```

`taxonomy.resolve(watch)` → a `ResolvedWatch` of: structured matchers (cpe vendor/
product, package names), and alias keyword sets tagged by `alias_safety`. The
existing `matching` layer consumes that — **exact** for structured fields,
and for aliases: `exact` (word), `phrase` (multi-word), or `cooccur` (generic word
only when near security terms like vulnerability/patch/CVE/exploit). This keeps the
news/Reddit side from flooding on words like "Windows" or "Access".

**Seeding & maintenance:** derive structured keys from the **NVD CPE dictionary**;
prioritize vendors/products in **CISA KEV**; ship a curated core covering the
MSP-critical categories (Firewalls, VPN/Remote Access, Hypervisors, RMM/PSA, Email
Security, OS); accept community PRs; users add `custom` entries locally.

---

## 5. v1 Definition of Done (the finish line)

`docker compose up` with a config yields a service that, on a schedule:
1. Pulls **CISA KEV** + **N configured advisory/PSIRT RSS feeds**.
2. Normalizes to `Item`, stores in SQLite (volume).
3. Resolves the user's taxonomy picks and **filters** (structured + alias) with
   severity/KEV gating.
4. Posts **new** (deduped) findings to **one webhook** (Teams/Slack-compatible).
5. Exposes read-only `GET /healthz`, `/findings?since=`, `/sources`.
6. Pings a heartbeat on each successful run; survives a dead source.

Plus: README, `config.example.yaml`, a starter `data/taxonomy.yaml`, `LICENSE`
(Apache-2.0), `NOTICE`, `DISCLAIMER.md`, `SECURITY.md`, `CHANGELOG.md` `0.1.0`
entry, CI green (ruff/pytest/docker build/gitleaks), Dockerfile + compose. Target:
a couple of focused weekends.

---

## 6. Module layout

```
heedwire/
├── README.md · LICENSE · NOTICE · DISCLAIMER.md · SECURITY.md · CHANGELOG.md
├── CLAUDE.md · CONTRIBUTING.md · HANDOFF.md
├── Dockerfile · docker-compose.yml · .dockerignore
├── .gitignore · .pre-commit-config.yaml · .gitleaks.toml · pyproject.toml
├── config.example.yaml
├── data/taxonomy.yaml
├── .github/workflows/ci.yml
├── docs/ taxonomy.md · deployment.md · adr/0001-*.md
├── src/heedwire/
│   ├── __init__.py · cli.py            # run | serve | once
│   ├── config.py · models.py · store.py · http.py
│   ├── taxonomy.py                     # load + resolve(picks) -> ResolvedWatch
│   ├── matching.py · state.py · scheduler.py · heartbeat.py
│   ├── summarizer.py                   # gated, off by default, placeholder when off
│   ├── api.py                          # FastAPI read-only local API
│   ├── sources/  base.py · kev.py · rss.py   (+ usn/nvd/news/reddit = fast-follow)
│   └── outputs/  base.py · webhook.py · stdout.py
└── tests/  test_taxonomy.py · test_matching.py · test_store.py · test_kev.py · test_rss.py
```

---

## 7. Work outline (phased, each shippable)

1. **Skeleton + hygiene** — repo, `pyproject.toml`, Apache LICENSE/NOTICE,
   DISCLAIMER/SECURITY/CHANGELOG, `.gitignore`, pre-commit (gitleaks), CI, ADR-0001.
2. **Ingest core** — `models.Item`, `store` (SQLite upsert by uid + window query),
   `sources/base`, `sources/kev`, `sources/rss`. Fixture tests.
3. **Taxonomy + filter** — `data/taxonomy.yaml` starter, `taxonomy.resolve()`,
   `matching` (structured exact + alias by safety + severity/KEV gate), `state`.
4. **Deliver + service** — `outputs/webhook` (+ `stdout`), `scheduler`,
   `heartbeat`, `api`, `cli`. Wire: ingest → store → resolve → match → notify.
5. **Containerize + document** — Dockerfile (non-root, multi-stage), compose,
   `config.example.yaml`, README quickstart, `docs/`. Cut `0.1.0`.
6. **Fast-follows (separate issues):** `summarizer` (grounded, BYO model), then
   `news`, `reddit`, `usn`, `nvd` sources, then a localhost web UI/PWA over the API.

---

## 8. Behavioral requirements (carry-over, must hold)

- Pull broad, filter local; no upstream queries by watchlist term; no search
  scraping.
- Per-source isolation + retries/backoff + timeouts; surface parse failures.
- Stable dedup by `Item.uid`; ~25h overlap window; heartbeat for silent-skip.
- Secrets from env only; never log matched products.
- AI summaries (when added): grounded, source-linked, non-authoritative, no
  republishing; off by default.

---

## 9. Open decisions for the human

1. Confirm repo name **Heedwire** + personal account, fill the README clone URL.
2. v1 webhook: generic (covers Teams + Slack + Discord) — confirm, or Teams-first
   card formatting.
3. Starter advisory/PSIRT RSS feed list to ship in `config.example.yaml`.
4. Starter taxonomy coverage: confirm the MSP categories to seed first (Firewalls,
   VPN/Remote Access, Hypervisors, RMM/PSA, Email Security, OS).
