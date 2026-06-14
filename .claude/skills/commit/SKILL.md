---
name: commit
description: Stage one logical change, write a Conventional Commit, and update the CHANGELOG in the same step. Use whenever committing work in this repo.
---

# commit

1. Review staged/unstaged changes; ensure the change is **one logical unit**
   (split if not).
2. Write a Conventional Commit: `type(scope): summary` (imperative, lowercase,
   <=72 chars). Types: feat|fix|docs|refactor|test|chore|build|ci|perf.
   Breaking: `type(scope)!:` + a `BREAKING CHANGE:` footer. Body explains *why*.
3. If the change is user-facing, add a line to `CHANGELOG.md` under
   `## [Unreleased]` in the right group (Added/Changed/Fixed/Security) **in the
   same commit**.
4. Never commit secrets or files matching `.gitignore`. Confirm gitleaks passes.
5. Work on a `claude/<type>-<slug>` branch; never commit to `main`.
