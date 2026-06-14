# Changelog

All notable changes to Heedwire are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Every user-facing change must update the `[Unreleased]` section in the same PR.

## [Unreleased]

### Added
- Initial project scaffolding, repository documentation, and engineering ruleset.
- Starter vendor PSIRT advisory RSS feeds wired into the taxonomy for Fortinet,
  Cisco, and Palo Alto; selecting those vendors (or the Firewalls category)
  auto-adds their advisory feed as an `rss` source.
- Teams delivery via Power Automate **Workflows** (`format: teams_workflow`):
  posts an Adaptive Card to the Workflows webhook that replaces the retired
  Office 365 connector. The legacy `teams` MessageCard format is retained.

### Changed
- RSS source now fetches through the shared HTTP session (explicit timeout +
  retry/backoff) instead of feedparser's un-timed fetch.

### Fixed
- KEV source now strips stray whitespace from the free-text `vendorProject` and
  `product` fields (present in the live CISA catalog), so exact structured
  matching is not silently defeated.
- RSS source parsed feed timestamps as local time, shifting `published` times
  (and the window filter) on non-UTC hosts; they are now correctly read as UTC.

<!--
Group entries under: Added / Changed / Deprecated / Removed / Fixed / Security.
On release: move [Unreleased] into a new "## [x.y.z] - YYYY-MM-DD" section.
-->
