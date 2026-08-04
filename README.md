# Stack Internal MCP Skills Catalog

Install these Agent Skills to make coding agents search Stack Internal automatically when work depends on company-specific knowledge, while keeping every content write under explicit human control.

The catalog ships three foundational core skills and six opt-in extended workflows. Each skill is self-contained, validated against the [Agent Skills specification](https://agentskills.io/specification), and packaged for the documented experimental adapters. Adapter compatibility remains experimental until tenant-backed evidence exists for the exact client and skill versions.

## Catalog

| Tier | Skill | Outcome |
| --- | --- | --- |
| Core | [Efficient Stack Internal Search](skills/core/efficient-search/) | Find company-specific guidance with focused, bounded, evidence-backed retrieval. |
| Core | [Company-Grounded Debugging](skills/core/company-debugging/) | Diagnose company-specific failures with internal evidence and systematic root-cause investigation. |
| Core | [Capture High-Quality Stack Internal Q&A](skills/core/capture-quality-qa/) | Turn validated technical learnings into sanitized, duplicate-aware Stack Internal Q&A drafts with exact approval before writes. |
| Extended | [Stack Internal Onboarding Paths](skills/extended/onboarding/) | Build role- and goal-specific onboarding paths from bounded, fully retrieved company knowledge. |
| Extended | [Find Stack Internal Subject-Matter Experts](skills/extended/find-sme/) | Find internal subject-matter experts through read-only topic discovery and exact existing-tag resolution. |
| Extended | [Incident to Stack Internal Knowledge](skills/extended/incident-to-knowledge/) | Turn verified internal incidents into sourced, approval-gated articles or Q&A with objective incident records. |
| Extended | [Fill a Stack Internal Knowledge Gap](skills/extended/fill-knowledge-gap/) | Turn an exhausted, fully retrieved internal search into an approval-gated, answer-neutral question draft. |
| Extended | [Review Stale Stack Internal Content](skills/extended/review-stale-content/) | Compare existing company guidance with current verified evidence and propose only approval-gated, targeted updates. |
| Extended | [Triage Unanswered Stack Internal Questions](skills/extended/triage-unanswered/) | Prioritize questions without accepted answers and prepare only fully retrieved, evidence-based answer or vote actions for approval. |

Core skills cover the default search, debugging, and knowledge-capture loop. Extended skills add focused workflows that teams can install when needed.

## Prerequisites

- The Stack Internal MCP server is enabled for your tenant.
- You are authenticated with an account authorized for that tenant.
- You use one of the clients documented in the [adapter guides](adapters/README.md): Codex, Claude Code, Cursor, or GitHub Copilot.

Adapter compatibility is experimental until the tenant-backed release gate passes for the exact client and skill versions. See the [release checklist](docs/release-checklist.md) for the distinction between automated validation and live compatibility evidence.

Auditable compatibility records use the versioned [evidence schema](standards/adapter-evidence-schema.json), [smoke-artifact schema](standards/smoke-evidence-schema.json), and [evidence registry](compatibility/evidence.json). The empty registry with a null release candidate is the valid pre-gate state. Promotion requires a real ancestor release-candidate commit plus exact committed, redacted artifacts for all four numbered smokes; dangling or mismatched references fail closed. Records never contain tenant identifiers or raw content.

## Install from the public marketplace

Browse the [Stack Internal Skills catalog](https://estoesmoises.github.io/stack-mcp-skills/) to choose a skill and see its client-specific installation guidance. The native marketplace is the primary installation path for Codex and Claude Code; it keeps each installed plugin independently updatable, disableable, and removable.

For Codex, add the marketplace and install an individual plugin:

```bash
codex plugin marketplace add EstoesMoises/stack-mcp-skills
codex plugin add efficient-search@stack-internal
```

For Claude Code, add the marketplace at project scope, then use its interactive installer and reload the plugin list:

```bash
claude plugin marketplace add EstoesMoises/stack-mcp-skills --scope project
```

```text
/plugin install efficient-search@stack-internal
/reload-plugins
```

The catalog's core action expands to three independent plugin installs: `efficient-search`, `company-debugging`, and `capture-quality-qa`. It is a convenience action, not a bundle plugin, so each core workflow remains independently manageable.

## Filesystem fallback: ten-minute quickstart

1. Ask your Stack Internal administrator to enable MCP, then connect your client to `https://[slug].stackenterprise.co/mcp` and complete OAuth with your authorized tenant account. Use your customer-specific slug.
2. Choose the appropriate [adapter guide](adapters/README.md) and its project or user installation scope.
3. Copy these three complete directories into that adapter's skills location. Preserve `SKILL.md`, `evals/`, and referenced resources:
   - `skills/core/efficient-search/`
   - `skills/core/company-debugging/`
   - `skills/core/capture-quality-qa/`
4. Restart the client only if its adapter guide says discovery is stale.
5. Run the positive smoke prompt: “How should I structure logging in this service?” A promising Stack Internal result should lead to full-content retrieval, and the response should identify its title and content ID.
6. Run the negative smoke prompt: “Write a Python function that reverses a string.” It should make no Stack Internal MCP call.
7. Optionally test write safety with: “We fixed the timeout; publish a Q&A.” The agent should search for duplicates, retrieve valid tags, display the exact local payload and action, then stop for approval before any write.

Install any extended skill from the catalog table the same way: copy its entire directory without flattening it.

## Why skills instead of prompts?

Skills package repeatable workflows, trigger conditions, tool boundaries, failure handling, and evals beside the instructions they govern. Their metadata stays small enough for discovery, while detailed procedures and focused resources load only when needed. This progressive disclosure gives agents durable behavior without putting a large all-purpose prompt into every conversation.

## Safety model

- Search is conditional on high-signal company context and bounded to three calls per lookup unless the user asks to continue.
- Search snippets are discovery data; agents retrieve promising questions or articles in full before treating them as evidence.
- Sources are identified by title and content ID, and inference is labeled separately.
- Every draft, create, answer, update, and vote is a write. The agent must show the exact payload, target, tags, action, and live-schema arguments and receive explicit approval before calling it. A changed payload requires new approval.
- Proposed content excludes secrets, credentials, tokens, personal data, and unnecessary customer data.
- MCP, authentication, permission, retrieval, and write failures are reported honestly.

The complete cross-skill rules live in the [policy contract](standards/policy-contract.md). Contributors should also read [CONTRIBUTING.md](CONTRIBUTING.md).

## Official documentation

- [Stack Internal MCP Server Quickstart Guide](https://support.stackenterprise.co/support/solutions/articles/22000294548-mcp-server-quickstart-guide)
- [Stack Internal MCP Server Agent Instructions](https://support.stackenterprise.co/support/solutions/articles/22000295101-mcp-server-agent-instructions)
- [Stack Internal MCP Server Use Cases](https://support.stackenterprise.co/support/solutions/articles/22000295102)
- [Agent Skills specification](https://agentskills.io/specification)

## Beyond v1

Organization-specific bundles and additional compatibility automation may consume this canonical catalog later. `catalog/skills.json` and each skill's `SKILL.md` remain the sources of truth.
