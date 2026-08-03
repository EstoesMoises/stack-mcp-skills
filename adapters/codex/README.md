# Codex adapter

## Install the skills

For a repository, copy each complete, self-contained skill directory into `.agents/skills/<skill-name>/`. For your user scope, copy it into `~/.agents/skills/<skill-name>/`. Preserve each directory’s `SKILL.md`, `evals/`, and referenced local resources; do not copy only the markdown file or flatten the folders. Select any of the nine directories listed in the [common adapter guide](../README.md).

Codex can select a skill automatically when the request matches its description. To invoke one explicitly, type `$skill-name` or use `/skills` to select it.

## Connect Stack Internal MCP

Your Stack Internal administrator must enable the MCP server, and you must have tenant access before connecting. Replace `[slug]` with your customer-specific tenant slug; it is not a shared catalog value.

```bash
codex mcp add stack-internal --url https://[slug].stackenterprise.co/mcp
```

The add command may register the server without opening the browser. Complete OAuth with an authorized tenant account by logging in:

```bash
codex mcp login stack-internal
```

The browser opens when you invoke this explicit login action. Return to Codex after authorization. Unauthenticated use may report that authentication is required; it is not promised to open a browser. Codex detects skill changes automatically; if discovery appears stale, restart Codex and try again. A failed authorization, unavailable endpoint, or missing permission is an MCP access failure, not evidence that Stack Internal was searched.

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
