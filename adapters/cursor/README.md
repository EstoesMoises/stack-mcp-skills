# Cursor adapter

## Install the skills

For a repository, copy each complete, self-contained skill directory into `.cursor/skills/<skill-name>/`. For your user scope, copy it into `~/.cursor/skills/<skill-name>/`. Preserve each directory’s `SKILL.md`, `evals/`, and referenced local resources; do not copy only the markdown file or flatten the folders. Select any of the nine directories listed in the [common adapter guide](../README.md).

Cursor discovers filesystem skills automatically when a request matches their descriptions. You can also invoke a skill with Cursor’s slash-command flow. Use the current [Cursor Agent Skills documentation](https://cursor.com/docs/skills) when the client presents a different discovery or command surface.

## Connect Stack Internal MCP

Your Stack Internal administrator must enable the MCP server, and you must have tenant access before connecting. Open your customer-specific `https://[slug].stackenterprise.co/mcp` landing page, then follow its current Cursor MCP setup instructions or use Cursor’s current MCP settings. Do not substitute another customer’s slug or paste an unverified settings JSON shape.

Complete the OAuth browser flow when Cursor opens it, using an authorized tenant account. A failed authorization, unavailable endpoint, or missing permission is an MCP access failure, not evidence that Stack Internal was searched.

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
