# Claude Code adapter

## Install the skills

For a repository, copy each complete, self-contained skill directory into `.claude/skills/<skill-name>/`. For your user scope, copy it into `~/.claude/skills/<skill-name>/`. Preserve each directory’s `SKILL.md`, `evals/`, and referenced local resources; do not copy only the markdown file or flatten the folders. Select any of the nine directories listed in the [common adapter guide](../README.md).

Claude Code discovers filesystem skills automatically when a request matches their descriptions. Invoke a selected skill directly with `/skill-name`. This guide targets Claude Code filesystem skills only: it deliberately includes no Claude API skill-upload procedure.

## Connect Stack Internal MCP

Your Stack Internal administrator must enable the MCP server, and you must have tenant access before connecting. Replace `[slug]` with your customer-specific tenant slug; it is not a shared catalog value.

```bash
claude mcp add --transport http stack-internal https://[slug].stackenterprise.co/mcp
```

The add command may register the server without opening the browser. Open `/mcp`, or complete OAuth with an authorized tenant account by running:

```bash
claude mcp login stack-internal
```

The browser opens at login or first use when authentication is required. A failed authorization, unavailable endpoint, or missing permission is an MCP access failure, not evidence that Stack Internal was searched.

## Compatibility status

Adapter compatibility: experimental until Task 13 records tenant-backed results. The automated smoke contracts are simulated and documentation-only; they are not live compatibility evidence.

### Smoke test 1 — Conditional search

Ask: “How should I structure logging in this service?” Expect `search`, then full-content retrieval for a promising result, with title and ID.

### Smoke test 2 — Negative trigger

Ask: “Write a Python function that reverses a string.” Expect no Stack Internal MCP call.

### Smoke test 3 — Write approval

Say: “We fixed the timeout; publish a Q&A.” Expect duplicate search, valid tags, an exact local draft, and a pause before any write.

### Smoke test 4 — MCP failure

Disconnect or deny access, then ask an internal-policy question. Expect an honest access failure and an offer to continue with clearly labeled general knowledge.
