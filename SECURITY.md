# Security Policy

Heedwire is a security tool, so we hold its own security to a high bar. Thank you
for helping keep it and its users safe.

## Reporting a vulnerability

**Please do not open a public issue for security vulnerabilities.**

Report privately via GitHub's **"Report a vulnerability"** (Security tab → Report
a vulnerability) so we can triage and fix before disclosure. If that is
unavailable, contact the maintainer through the address listed on the GitHub
profile.

Please include: affected version/commit, a description, reproduction steps, and
impact. A proof of concept helps but is not required.

## What we care about most

- Secret/credential exposure (webhook URLs, API keys, tokens).
- Injection via untrusted feed/news/Reddit content reaching code, the store, the
  web UI, or a downstream notifier.
- The local API or web UI being reachable beyond its intended bind.
- Supply-chain issues in dependencies or the container image.

## Response

We aim to acknowledge reports within a few days and to fix confirmed issues
promptly, crediting reporters who wish to be named. There is no paid bounty.

## Scope notes

Heedwire processes untrusted external content by design. Findings that require an
already-compromised host, or that depend on a user deliberately exposing the
service without auth, will be assessed case by case.
