# Changelog

All notable changes to Heedwire are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Every user-facing change must update the `[Unreleased]` section in the same PR.

## [Unreleased]

### Added
- Initial project scaffolding, repository documentation, and engineering ruleset.

### Fixed
- KEV source now strips stray whitespace from the free-text `vendorProject` and
  `product` fields (present in the live CISA catalog), so exact structured
  matching is not silently defeated.

<!--
Group entries under: Added / Changed / Deprecated / Removed / Fixed / Security.
On release: move [Unreleased] into a new "## [x.y.z] - YYYY-MM-DD" section.
-->
