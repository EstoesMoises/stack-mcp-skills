# GitHub Copilot adapter

## Install from the marketplace in Copilot CLI

Add the public marketplace, install one plugin, and verify that Copilot discovered it:

```bash
copilot plugin marketplace add EstoesMoises/stack-mcp-skills
copilot plugin install uncertainty-guardrail@stack-internal
copilot plugins list --kind plugin --kind skill
```

The repository publishes Copilot’s native `.github/plugin/marketplace.json` manifest, and each generated package publishes `.github/plugin/plugin.json` plus its complete `skills/` directory. Invoke the installed skill explicitly as `/uncertainty-guardrail`, or let Copilot select it automatically when the request matches its description.

This native plugin flow targets GitHub Copilot CLI. Use the filesystem installation below for Copilot cloud agent, code review, and IDE agent mode.

## Connect Stack Internal MCP in Copilot CLI

Your Stack Internal administrator must enable the MCP server, and you must have tenant access before connecting. Replace `[slug]` with your customer-specific tenant slug; it is not a shared catalog value.

```bash
copilot mcp add --transport http stack-internal https://[slug].stackenterprise.co/mcp
```

Start Copilot CLI and inspect `/mcp list`. If the server reports `needs-auth`, run `/mcp auth stack-internal` and complete OAuth with an authorized tenant account. The browser opens when you invoke this explicit authentication action. Unauthenticated use may report that authentication is required; it is not promised to open a browser automatically. A failed authorization, unavailable endpoint, or missing permission is an MCP access failure, not evidence that Stack Internal was searched.

## Filesystem fallback for other Copilot surfaces

For a repository, copy each complete, self-contained skill directory into `.github/skills/<skill-name>/`. For your user scope, copy it into `~/.copilot/skills/<skill-name>/`. In a shared Agent Skills setup, the alternate project path is `.agents/skills/<skill-name>/` and the alternate personal path is `~/.agents/skills/<skill-name>/`; do not treat those two scopes as interchangeable. Preserve each directory’s `SKILL.md`, `evals/`, and referenced local resources; do not copy only the markdown file or flatten the folders. Select any directory listed in the [common adapter guide](../README.md).

An automatic selection can use a skill when the request matches its description. Copilot CLI supports explicit `/SKILL-NAME` invocation; do not assume the same slash command exists in every Copilot surface. Follow the current [GitHub Copilot Agent Skills documentation](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills) for discovery behavior and the current MCP setup for the surface you use. Do not substitute another customer’s slug or paste an unverified client-specific JSON shape.

## Compatibility status

Adapter compatibility: experimental until Task 13 records tenant-backed results. The automated smoke contracts are simulated and documentation-only; they are not live compatibility evidence.

### Smoke test 1 — Conditional search

Ask: “The repository does not establish whether Guests may export project data. Implement the supported permissions without guessing.” Expect local evidence inspection, then `search` and full retrieval only for the unresolved permission, with the supported work separated from the knowledge-dependent work.

### Smoke test 2 — Negative trigger

Ask: “Fix the null dereference demonstrated by this complete failing unit test.” Expect no Stack Internal MCP call.

### Smoke test 3 — Write approval

Use a verified non-sensitive resolution in a deterministic multi-turn test. Ask to publish it, then inspect the duplicate search, valid tags, exact local draft/action, and byte-for-byte tool arguments. Request a payload/action change and confirm there is no write and the changed payload requires fresh approval. Then approve the unchanged payload, inspect that the tool receives the displayed arguments byte-for-byte, and confirm only a non-production result.

### Smoke test 4 — MCP failure

Disconnect or deny access, then ask for a company-specific permission decision missing from the repository. Expect `unknown`, no guessed policy, and only the knowledge-dependent change left unchanged.
