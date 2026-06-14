---
name: end-of-session
description: Produce an end-of-session handoff — what was done, what's planned next, blockers, and a copy-pasteable note for the next session — and audit that every unresolved item became a tracked todo. Use when wrapping up a work session (especially before the sandbox/session is recreated).
---

# end-of-session

Heedwire sessions run in ephemeral sandboxes; anything not committed or written
down is lost when the session ends. This skill captures the state so the next
session starts cold but informed. Everything here is public-repo safe: reference
only Heedwire, and never write a secret (webhook/heartbeat URL, token, `.env`,
real `config.yaml`, or the watchlist) into the summary, a file, or a commit.

1. **Gather facts, don't guess.** Establish ground truth before summarizing:
   - `git log --oneline <base>..HEAD` for this session's commits, and `git status`.
   - The open PR(s) for the branch and their state (CI, review) via the GitHub
     tools.
   - Re-read the conversation for every item raised: decisions, fixes, deferrals,
     blockers, and anything the maintainer asked for.

2. **Summarize what was done.** Group logically (not commit-by-commit). For each
   item note *how it was verified* (test/live/localhost/build) and any honesty
   caveat (e.g. "verified against a mirror because egress blocked the canonical
   host"). Keep it skimmable.

3. **List what's planned next**, split and labeled:
   - **Agent todos**, each tagged with its state: *unblocked* / *blocked: egress* /
     *blocked: secret* / *later*. Name the exact blocker.
   - **Maintainer todos** — anything only the human can do (recreate the session,
     provide a test webhook secret, app registrations, review/merge, decisions).
   - **Open decisions** still pending (e.g. `HANDOFF.md` §9).

4. **Audit — nothing silently dropped.** Cross-check the conversation: every item
   raised this session must appear under *Done* or under a *todo*. State the audit
   result explicitly ("all N items accounted for: X done, Y carried forward").
   If something was deferred, say why. Do not mark anything done that wasn't
   verified.

5. **Produce a copy-pasteable handoff block** for the next session as a single
   fenced code block the maintainer can paste as the opening prompt. Include:
   branch name, PR number/URL, one-line current state, the **first actions** the
   next session should take (in order), and **what's needed from the maintainer**
   to unblock. No secrets — refer to env var *names* only.

6. **Output to chat by default.** Offer to also save the handoff to a tracked file
   (e.g. `docs/handoffs/YYYY-MM-DD.md`) if the maintainer wants a durable log;
   only do so on request. Never commit secrets.
</content>
