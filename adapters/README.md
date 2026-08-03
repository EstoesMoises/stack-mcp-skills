# Native agent adapters

All four clients now support filesystem-based Agent Skills. These thin adapter guides install the same canonical skill directories; they do not translate or relax a skill's workflow or safety rules.

| Client | Project location | User location | Primary documentation |
| --- | --- | --- | --- |
| Codex | `.agents/skills/<skill-name>/` | `~/.agents/skills/<skill-name>/` | [Build skills](https://learn.chatgpt.com/docs/build-skills) |
| Claude Code | `.claude/skills/<skill-name>/` | `~/.claude/skills/<skill-name>/` | [Agent Skills](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview) |
| Cursor | `.cursor/skills/<skill-name>/` | `~/.cursor/skills/<skill-name>/` | [Agent Skills](https://cursor.com/docs/skills) |
| GitHub Copilot | `.github/skills/<skill-name>/` | `~/.copilot/skills/<skill-name>/` | [Adding agent skills](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills) |

Before releasing an adapter version, re-check the primary documentation above. Client paths, preview features, and MCP setup screens can change.

## Common prerequisites

An administrator must enable the Stack Internal MCP server for the tenant, and every person using a guide must be authorized to access it. Replace `[slug]` with the customer-specific tenant slug in `https://[slug].stackenterprise.co/mcp`; never copy a URL from a different tenant. Complete the client’s OAuth browser flow when it opens and use an account with access to the tenant.

Copy each complete, self-contained skill directory, including `SKILL.md`, `evals/`, and every local resource it references. Do not copy only a `SKILL.md`, merge contents into an instruction file, or flatten the directory. The current catalog has these nine source directories:

- `skills/core/efficient-search/`
- `skills/core/company-debugging/`
- `skills/core/capture-quality-qa/`
- `skills/extended/onboarding/`
- `skills/extended/find-sme/`
- `skills/extended/incident-to-knowledge/`
- `skills/extended/fill-knowledge-gap/`
- `skills/extended/review-stale-content/`
- `skills/extended/triage-unanswered/`

## Compatibility status

Adapter compatibility: experimental. It remains experimental until Task 13 records four tenant-backed smoke results for the exact client and skill versions. The automated smoke contracts in this repository are simulated, documentation-only checks; they are not live compatibility evidence.

Choose a client guide: [Codex](codex/README.md), [Claude Code](claude-code/README.md), [Cursor](cursor/README.md), or [GitHub Copilot](github-copilot/README.md).
