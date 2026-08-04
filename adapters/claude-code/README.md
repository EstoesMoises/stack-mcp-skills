# Claude Code adapter

## Install from the marketplace

Add the public marketplace at project scope:

```bash
claude plugin marketplace add EstoesMoises/stack-mcp-skills --scope project
```

Install the selected plugin explicitly at project scope, then reload its plugin discovery:

```bash
claude plugin install efficient-search@stack-internal --scope project
/reload-plugins
```

Invoke the installed skill explicitly as `/efficient-search:efficient-search`. Claude Code also discovers installed skills automatically when a request matches their descriptions.

## Connect Stack Internal MCP

Your Stack Internal administrator must enable the MCP server, and you must have tenant access before connecting. Replace `[slug]` with your customer-specific tenant slug; it is not a shared catalog value.

```bash
claude mcp add --transport http stack-internal https://[slug].stackenterprise.co/mcp
```

The add command may register the server without opening the browser. Open `/mcp`, or complete OAuth with an authorized tenant account by running:

```bash
claude mcp login stack-internal
```

The browser opens when you invoke `/mcp` authentication or this explicit login action. Unauthenticated use may report that authentication is required; it is not promised to open a browser. A failed authorization, unavailable endpoint, or missing permission is an MCP access failure, not evidence that Stack Internal was searched.

## Compatibility status

Adapter compatibility: experimental until Task 13 records tenant-backed results. The automated smoke contracts are simulated and documentation-only; they are not live compatibility evidence.

### Smoke test 1 — Conditional search

Ask: “How should I structure logging in this service?” Expect `search`, then full-content retrieval for a promising result, with title and ID.

### Smoke test 2 — Negative trigger

Ask: “Write a Python function that reverses a string.” Expect no Stack Internal MCP call.

### Smoke test 3 — Write approval

Use a verified non-sensitive resolution in a deterministic multi-turn test. Ask to publish it, then inspect the duplicate search, valid tags, exact local draft/action, and byte-for-byte tool arguments. Request a payload/action change and confirm there is no write and the changed payload requires fresh approval. Then approve the unchanged payload, inspect that the tool receives the displayed arguments byte-for-byte, and confirm only a non-production result.

### Smoke test 4 — MCP failure

Disconnect or deny access, then ask an internal-policy question. Expect an honest access failure and an offer to continue with clearly labeled general knowledge.

## Filesystem fallback

For a repository, copy each complete, self-contained skill directory into `.claude/skills/<skill-name>/`. For your user scope, copy it into `~/.claude/skills/<skill-name>/`. Preserve each directory’s `SKILL.md`, `evals/`, and referenced local resources; do not copy only the markdown file or flatten the folders. Select any of the nine directories listed in the [common adapter guide](../README.md).

Claude Code discovers filesystem skills automatically when a request matches their descriptions. Invoke a selected skill directly with `/skill-name`. This guide targets Claude Code filesystem skills only: it deliberately includes no Claude API skill-upload procedure.
