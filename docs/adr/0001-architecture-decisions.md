# ADR 0001 — Foundational architecture decisions

Status: accepted

## Context
Heedwire is a public, self-hostable security signal monitor. A few decisions shape
everything else and are recorded here so they aren't accidentally reversed.

## Decisions
1. **Pull broad, filter local.** Sources fetch whole/recent public feeds; the
   watchlist is resolved and matched locally. No upstream is ever queried by a
   user's watchlist term. Consequence: providers never learn what a user watches.
2. **Taxonomy resolves before matching.** Users pick categories/vendors/products;
   a resolver expands picks into structured + alias matchers. The matching layer
   stays generic. Consequence: no hand-written keyword rules; alias safety levels
   contain false positives on the news/Reddit side.
3. **Feeder/consumer split, single container.** Ingest+store is logically separate
   from filter+deliver, joined by a read-only local API seam. Shipped as one
   container for v1; a companion app can consume the API later.
4. **Alert rules are server-side; view filtering is client-side; auth is for
   exposure/multi-user, not privacy.** Single-tenant self-host means the operator
   is the user. Local API binds localhost by default.
5. **No search scraping.** Bing's Search API was retired (2025) and Google has no
   free general search API; news discovery uses RSS (incl. Google Alerts as RSS)
   and optional free-tier providers. Reddit via its official API.
6. **AI summaries are grounded, source-linked, non-authoritative, off by default.**
