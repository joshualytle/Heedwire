---
name: add-source
description: Scaffold a new Heedwire source adapter following the Source contract and the pull-broad-filter-local rule, with a fixture-based test. Use when adding a feed/source.
---

# add-source

1. Create `src/heedwire/sources/<name>.py` with a class implementing `Source`:
   `fetch(self, since: datetime) -> list[Item]`.
2. **Pull the broad/recent feed and normalize to `Item`. Never query upstream by
   the user's watchlist.** Fill the structured fields the matcher uses
   (`vendors`, `products`, `packages`, `cve_ids`) where the source provides them;
   otherwise rely on `title`/`summary` for alias matching.
3. Every request: explicit `timeout`, via `http.session()` (retry/backoff).
   Validate response shape; raise a clear error on surprises (don't silently drop).
4. Give each item a **stable `uid`** (native id, else `make_uid(...)`).
5. Register the class in `sources/__init__.py` `REGISTRY`.
6. Add a **fixture-based test** in `tests/` (save a sample response under
   `tests/fixtures/`; never hit the live API in tests).
7. Document any privacy caveat in the module docstring.
