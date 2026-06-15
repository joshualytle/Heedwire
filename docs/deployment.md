# Deployment

Heedwire runs as one container. `docker compose up -d` with a `config.yaml` and
the right environment variables is the whole story. This doc covers the
operational details: outbound network, secrets, the heartbeat, Teams setup, and
data persistence.

## Secrets (environment only)

Heedwire never reads secrets from `config.yaml`. They come from the environment:

| Env var | Purpose |
|---|---|
| `HEEDWIRE_WEBHOOK_URL` | Incoming-webhook URL for your chat platform (Slack/Teams/Discord). |
| `HEEDWIRE_HEARTBEAT_URL` | Optional dead-man's-switch ping URL (see below). |

Copy the shipped template and fill in your values:

```bash
cp .env.example .env   # then edit .env
```

`docker compose` loads `.env` from the project directory automatically. `.env` is
gitignored — keep your real secrets there or in your secret store, never in the
image or `config.yaml`. An unset webhook URL doesn't crash the run: ingest and
matching still happen, but the delivery step errors (isolated per-output) and
nothing is posted.

## Outbound network (egress allowlist)

Heedwire **pulls broad public feeds and filters locally** — your watchlist is
never sent upstream. If your host or platform restricts outbound traffic, allow
the hosts for the sources and output you actually use:

```
# CISA KEV (canonical)
www.cisa.gov

# Vendor PSIRT advisory feeds (only those whose vendors/categories you watch)
www.fortiguard.com
sec.cloudapps.cisco.com
security.paloaltonetworks.com

# Output webhook host — pick the one you use
hooks.slack.com                 # Slack
discord.com                     # Discord
*.logic.azure.com               # Teams (Power Automate Workflows; the host
*.webhook.office.com            #   varies — use the one in YOUR generated URL)
*.azure-apim.net
```

Notes:
- Some vendor advisory feeds sit behind a CDN/WAF that may block automated
  clients from certain networks (e.g. datacenter IP ranges). A failing feed is
  isolated per-source — the run continues and the error is reported.
- CISA also publishes the KEV catalog at the official GitHub mirror
  `raw.githubusercontent.com/cisagov/kev-data`, which is a useful fallback if
  `www.cisa.gov` is hard to reach from your network. Point the `kev` source's
  `url` at it in `config.yaml` if needed.

## Heartbeat (dead-man's-switch)

A scheduled tool that dies quietly looks identical to "a quiet week." To catch
that, set `HEEDWIRE_HEARTBEAT_URL` to a push-monitor URL (e.g. healthchecks.io,
Uptime Kuma). After each completed run Heedwire pings it; if any source errored,
it pings `<url>/fail`. Configure your monitor to alert if it stops hearing the
ping. The env var name can be changed via `heartbeat_env` in `config.yaml`.

## Microsoft Teams

Office 365 Connectors (the classic Teams "Incoming Webhook") were retired in
2026. Use a **Power Automate Workflows** webhook instead:

1. In the target Teams channel: **⋯ → Workflows → "Post to a channel when a
   webhook request is received."**
2. Copy the generated URL into `HEEDWIRE_WEBHOOK_URL`.
3. Set the output `format: teams_workflow` in `config.yaml` (posts an Adaptive
   Card). The legacy `format: teams` MessageCard is still accepted by Workflows
   but `teams_workflow` is preferred.

## Data persistence

The SQLite store (`store_path`, default `data/heedwire.db`) holds seen items, the
"notified" marker (dedup), and `last_run`. Mount it on a volume (the compose file
mounts `./data`) so dedup and the window survive restarts. It contains only broad
public items and a timestamp — never your watchlist.

## Local API

The read-only API (`heedwire serve`) binds `127.0.0.1` by default. It has no auth
— that's intentional for single-tenant self-hosting. If you expose it beyond
localhost or share it, put authentication in front of it (e.g. a reverse proxy).
</content>
