# Stack Internal MCP Skills Marketplace

Install focused Agent Skills that turn Stack Internal MCP tools into reusable company-knowledge workflows. The initial release deliberately excludes skills whose primary behavior is already described by a dedicated MCP tool.

The catalog ships one foundational core skill and three opt-in extended workflows. Each skill is self-contained, validated against the [Agent Skills specification](https://agentskills.io/specification), and packaged for the documented experimental adapters. Adapter compatibility remains experimental until tenant-backed evidence exists for the exact client and skill versions.

## Catalog

| Tier | Skill | Outcome |
| --- | --- | --- |
| Core | [Uncertainty Guardrail](skills/core/uncertainty-guardrail/) | Prevent unsupported company-specific assumptions from becoming code or operational decisions while unrelated safe work continues. |
| Extended | [Stack Internal Onboarding Paths](skills/extended/onboarding/) | Build role- and goal-specific onboarding paths from bounded, fully retrieved company knowledge. |
| Extended | [Incident to Stack Internal Knowledge](skills/extended/incident-to-knowledge/) | Turn verified internal incidents into sourced, approval-gated articles or Q&A with objective incident records. |
| Extended | [Review Stale Stack Internal Content](skills/extended/review-stale-content/) | Compare existing company guidance with current verified evidence and propose only approval-gated, targeted updates. |

The [initial release assessment](docs/initial-release-skill-assessment.md) records why six earlier skills were merged, removed, or deferred after comparison with the live MCP tool definitions.

## Prerequisites

- The Stack Internal MCP server is enabled for your tenant.
- You are authenticated with an account authorized for that tenant.
- You use one of the clients documented in the [adapter guides](adapters/README.md): Codex, Claude Code, Cursor, or GitHub Copilot.

Adapter compatibility is experimental until the tenant-backed release gate passes for the exact client and skill versions. See the [release checklist](docs/release-checklist.md) for the distinction between automated validation and live compatibility evidence.

Auditable compatibility records use the versioned [evidence schema](standards/adapter-evidence-schema.json), [smoke-artifact schema](standards/smoke-evidence-schema.json), and [evidence registry](compatibility/evidence.json). The empty registry with a null release candidate is the valid pre-gate state. Promotion requires a real ancestor release-candidate commit plus exact committed, redacted artifacts for all four numbered smokes; dangling or mismatched references fail closed. Records never contain tenant identifiers or raw content.

## Install from the public marketplace

Browse the [Stack Internal Skills catalog](https://estoesmoises.github.io/stack-mcp-skills/) to choose a skill and see its client-specific installation guidance. The native marketplace is the primary installation path for Codex, Claude Code, and GitHub Copilot CLI; it keeps each installed plugin independently updatable, disableable, and removable.

For Codex, add the marketplace and install the core guardrail:

```bash
codex plugin marketplace add EstoesMoises/stack-mcp-skills
codex plugin add uncertainty-guardrail@stack-internal
```

For Claude Code, add the marketplace and install the plugin explicitly at project scope, then reload plugin discovery:

```bash
claude plugin marketplace add EstoesMoises/stack-mcp-skills --scope project
```

```bash
claude plugin install uncertainty-guardrail@stack-internal --scope project
```

```text
/reload-plugins
```

For GitHub Copilot CLI, add the marketplace and install an individual plugin:

```bash
copilot plugin marketplace add EstoesMoises/stack-mcp-skills
copilot plugin install uncertainty-guardrail@stack-internal
```

The catalog's core action installs `uncertainty-guardrail` as one independently manageable plugin. Copilot cloud, code review, and IDE surfaces can use the filesystem fallback documented in the Copilot adapter guide.

## Filesystem fallback

1. Ask your Stack Internal administrator to enable MCP, then connect your client to `https://[slug].stackenterprise.co/mcp` and complete OAuth with your authorized tenant account. Use your customer-specific slug.
2. Choose the appropriate [adapter guide](adapters/README.md) and its project or user installation scope.
3. Copy the complete `skills/core/uncertainty-guardrail/` directory into that adapter's skills location. Preserve `SKILL.md` and `evals/`.
4. Restart the client only if its adapter guide says discovery is stale.
5. Run the positive smoke prompt: “The repository does not establish whether Guests may export project data. Implement the supported permissions without guessing.” The agent should inspect local evidence, research only the unresolved decision, and leave only knowledge-dependent work unchanged if evidence remains inadequate.
6. Run the negative smoke prompt: “Fix the null dereference demonstrated by this complete failing unit test.” It should make no Stack Internal MCP call.
7. Test a write-capable plugin separately with a verified non-sensitive incident or stale-content scenario. The agent must display the exact action and payload and stop for approval before any write.

Install an extended skill the same way: copy its entire directory without flattening it.

## Why skills when the MCP already defines tools?

The MCP contract owns tool purposes, parameters, authentication, permissions, and baseline retrieval or creation instructions. Skills belong here only when they add a distinct workflow: deciding when local evidence is insufficient, synthesizing several sources into an onboarding path, converting objective incident evidence into durable knowledge, or proving that existing guidance diverges from current practice.

Skills are behavioral guidance and defense in depth, not a security boundary. Authorization and critical write protections must be enforced by the MCP server.

## Safety model

- The uncertainty guardrail inspects local evidence first and blocks only work dependent on an unresolved company decision.
- Access failure is an unknown state, not proof that guidance is absent.
- Retained write workflows require verified source material, a complete displayed payload, and explicit approval before the MCP call.
- Proposed content excludes secrets, credentials, tokens, personal data, and unnecessary customer data.
- MCP, authentication, permission, retrieval, and write failures are reported honestly.

The complete cross-skill rules live in the [policy contract](standards/policy-contract.md). Contributors should also read [CONTRIBUTING.md](CONTRIBUTING.md).

## Official documentation

- [Stack Internal MCP Server Quickstart Guide](https://support.stackenterprise.co/support/solutions/articles/22000294548-mcp-server-quickstart-guide)
- [Stack Internal MCP Server Agent Instructions](https://support.stackenterprise.co/support/solutions/articles/22000295101-mcp-server-agent-instructions)
- [Stack Internal MCP Server Use Cases](https://support.stackenterprise.co/support/solutions/articles/22000295102)
- [Agent Skills specification](https://agentskills.io/specification)

## Beyond the initial release

Deferred workflows should return only when user evidence shows they add repeatable judgment beyond a dedicated MCP tool. `catalog/skills.json` and each retained `SKILL.md` remain the sources of truth.
