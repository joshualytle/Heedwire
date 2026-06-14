# Taxonomy

The taxonomy is how you tell Heedwire what to watch **without writing keyword
rules**. It ships as a curated data file, `data/taxonomy.yaml`, and you select
from it in `config.yaml` under `watch:`.

## How selection works

You pick at three levels; Heedwire unions them:

```yaml
watch:
  categories: ["Network Security / Firewalls", "Remote Access / VPN"]
  vendors: [Microsoft, Fortinet, Ivanti]      # whole vendor
  products: [fortinet.fortios, vmware.esxi]   # a specific taxonomy entry id
  custom: []                                  # your own ad-hoc entries
```

Before matching runs, `taxonomy.resolve()` expands your picks into concrete
matchers:

- **Structured matchers** — CPE vendor/product and distro package names; matched
  **exactly** against the structured fields a source provides (KEV, NVD, USN).
- **Alias keywords** — product names matched against item title/summary (news,
  Reddit, advisory titles), each tagged with a safety level (below).
- **Advisory feeds** — if a selected entry defines an `advisory_feed`, that PSIRT
  RSS feed is added as a source automatically. (The starter taxonomy ships feeds
  for Fortinet, Cisco, and Palo Alto.)

Inspect exactly what your config resolves to:

```bash
heedwire resolve -c config.yaml
```

## A taxonomy entry

```yaml
- id: fortinet.fortios
  vendor: Fortinet
  category: Network Security / Firewalls
  cpe: { vendor: fortinet, product: fortios }   # structured (KEV/NVD) match
  packages: []                                   # distro package names (USN)
  aliases: ["FortiOS", "FortiGate"]              # keyword (news/Reddit) match
  alias_safety: exact                            # exact | phrase | cooccur
  advisory_feed: https://www.fortiguard.com/rss/ir.xml   # optional vendor PSIRT
```

## Alias safety levels

Aliases are the only fuzzy match, so each carries a safety level to keep generic
words from flooding the news/Reddit side:

- **`exact`** — whole-word match (`ESXi` matches "VMware ESXi", not "esximore").
  Use for distinctive product names.
- **`phrase`** — substring/phrase match. Use for multi-word names
  (`Windows Server`).
- **`cooccur`** — whole-word match **only when** a security term (vulnerability,
  exploit, CVE, patch, …) is also present. Use for generic words that would
  otherwise over-match (`Windows`, `Access`).

Structured (CPE/package) matching is always exact and unaffected by these.

## Custom entries (never blocked on the taxonomy)

You don't need a taxonomy PR to watch something. Add it under `watch.custom`:

```yaml
watch:
  custom:
    - cpe: { vendor: acme, product: widget }
      aliases: ["AcmeWidget"]
      alias_safety: phrase
      # advisory_feed: https://acme.example/psirt.rss
```

Contributions to the shared taxonomy are welcome too — see
[`CONTRIBUTING.md`](../CONTRIBUTING.md).
</content>
