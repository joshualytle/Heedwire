# Contributing to Heedwire

Thanks for helping. Heedwire aims to be a small, honest, dependable tool — please
keep contributions in that spirit: focused, well-tested, and clear about limits.

## Dev setup

```bash
pip install -e ".[dev]"
pre-commit install        # installs gitleaks + hygiene hooks
pytest                    # tests must pass
ruff check . && ruff format --check .
```

Tests use **recorded fixtures** for source parsers — never hit live APIs in tests.

## Branching & PRs (GitHub Flow)

- `main` is always releasable and protected. Work on short-lived branches:
  `feat/news-source`, `fix/dedup-window`, `docs/taxonomy`.
- Open a PR describing **what changed and why**; link the issue. PRs are
  **squash-merged** so `main` is one clean commit per change.

## Commits — Conventional Commits

`type(scope): summary` (imperative, lowercase). Types: `feat`, `fix`, `docs`,
`refactor`, `test`, `chore`, `build`, `ci`, `perf`. Breaking: `feat(api)!:` + a
`BREAKING CHANGE:` footer. Example: `feat(taxonomy): add RMM/PSA category`.

## PR checklist

- [ ] CI green (ruff, pytest, docker build, gitleaks)
- [ ] `CHANGELOG.md` `[Unreleased]` updated for any user-facing change
- [ ] Docstrings/README/`docs/` updated; ADR added if the decision was significant
- [ ] No secrets; no new copyleft deps; deps pinned; actions SHA-pinned
- [ ] Claims stay honest — no "catches everything"

## Adding a source adapter

Implement the `Source` contract in `src/heedwire/sources/<name>.py`:
- Fetch the **broad/recent** feed and normalize to the `Item` model. **Never**
  query upstream by the user's watchlist terms (privacy boundary).
- Explicit `timeout` on every request; go through the shared HTTP helper with
  retry/backoff. Validate response shape; raise a clear error on surprises.
- Add a fixture-based test. Register the adapter in `sources/__init__.py`.

## Adding a taxonomy entry (the easy, high-value contribution)

Taxonomy lives in `data/taxonomy.yaml`. Each entry maps one product to the keys
each source type needs, because sources speak different languages:

```yaml
- id: fortinet.fortios
  vendor: Fortinet
  category: Network Security / Firewalls
  cpe: { vendor: fortinet, product: fortios }   # structured advisory match (KEV/NVD)
  packages: []                                   # distro package names (USN etc.)
  aliases: ["FortiOS", "FortiGate"]              # news/Reddit keyword match
  alias_safety: phrase                           # exact | phrase | cooccur (see below)
  advisory_feed: https://.../fortinet-psirt.rss  # optional vendor PSIRT feed
```

**Alias discipline matters** — this is where false positives live. Set
`alias_safety`:
- `exact` — distinctive token, safe to match as a word (e.g. `FortiOS`).
- `phrase` — match the multi-word phrase only.
- `cooccur` — generic word (e.g. `Windows`, `Access`); only match when it
  co-occurs with security terms (vulnerability/patch/CVE/exploit).

Seed structured keys from the **NVD CPE dictionary**; prioritize vendors/products
that appear in **CISA KEV**. When in doubt, prefer fewer, higher-precision aliases.

## Documentation & honesty

Docstrings on public functions (include any privacy/security note). Record
significant decisions as ADRs in `docs/adr/`. This audience trusts precise over
promotional — state limits plainly.
