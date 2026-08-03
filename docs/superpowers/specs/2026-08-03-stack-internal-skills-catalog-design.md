# Stack Internal MCP Skills Catalog Design

## Summary

Build a public, Git-based catalog of portable agent skills that teach AI agents when and how to use the Stack Overflow Internal MCP server. The catalog will make Stack Internal an automatic, conditional source of company knowledge rather than a tool users must invoke manually.

Every published skill will conform to the open [Agent Skills specification](https://agentskills.io/specification): a self-contained directory with a required `SKILL.md` and optional local resources loaded through progressive disclosure. The first release targets MCP-capable coding agents broadly, with adapters for Codex, Claude Code, Cursor, and GitHub Copilot. It will not include a hosted marketplace, package installer, or code generator. Customers will browse the repository, choose skills or a recommended bundle, and follow the adapter for their agent.

## Goals

- Ground debugging and technical work in trusted company knowledge when the task has a high-signal internal context.
- Teach agents an efficient Stack Internal search strategy, including full-content retrieval and bounded query broadening.
- Turn resolved work into concise, useful, non-generic Q&A without publishing on a user's behalf unexpectedly.
- Provide broader knowledge workflows for onboarding, SME discovery, incident capture, knowledge gaps, stale content, and unanswered questions.
- Keep skill behavior consistent across supported agents while allowing more skills and adapters to be added later.
- Make installation and expected behavior understandable without requiring a build system.
- Validate every skill against the Agent Skills format and use progressive disclosure to control context cost.

## Non-goals for v1

- A hosted marketplace or web application.
- An automated installer or generated agent packs.
- A replacement for the Stack Internal MCP server or its OAuth setup.
- Unattended content creation, editing, or voting.
- Agent-specific forks of the canonical workflows.
- Usage analytics or administration of customer Stack Internal instances.

## Design decisions

The approved decisions are:

- Distribution: a Git repository catalog.
- Audience: multiple MCP-capable agents, not a Codex-only plugin.
- Structure: self-contained Agent Skills folders with thin agent adapters.
- Search policy: automatic only for high-signal internal triggers.
- Write policy: every write requires approval of the exact action and content.
- Scope: three core skills plus an extended workflow set.

## Repository architecture

```text
stack-mcp-skills/
├── README.md
├── CONTRIBUTING.md
├── catalog/
│   └── skills.json
├── skills/
│   ├── core/
│   │   ├── efficient-search/
│   │   │   ├── SKILL.md
│   │   │   ├── references/       # Optional, loaded on demand
│   │   │   └── evals/
│   │   ├── company-debugging/
│   │   │   ├── SKILL.md
│   │   │   ├── references/       # Optional, loaded on demand
│   │   │   └── evals/
│   │   └── capture-quality-qa/
│   │       ├── SKILL.md
│   │       ├── references/       # Optional, loaded on demand
│   │       ├── scripts/          # Optional deterministic helpers
│   │       ├── assets/           # Optional output templates
│   │       └── evals/
│   └── extended/
│       ├── onboarding/
│       ├── find-sme/
│       ├── incident-to-knowledge/
│       ├── fill-knowledge-gap/
│       ├── review-stale-content/
│       └── triage-unanswered/
├── adapters/
│   ├── codex/
│   ├── claude-code/
│   ├── cursor/
│   └── github-copilot/
├── standards/
│   ├── catalog-schema.json
│   └── policy-contract.md
├── scripts/
│   └── validate_catalog.py
└── tests/
    └── contract/
```

Each extended skill directory follows the same self-contained shape: a required `SKILL.md`, an `evals/` directory, and only the optional `references/`, `scripts/`, or `assets/` directories that the workflow genuinely needs. Optional directories must not be created empty.

### Component boundaries

`skills/` contains agent-neutral, specification-compliant behavior. Each folder is independently installable and declares its triggers, tool dependencies, workflow, output, safety gates, failures, and examples.

`references/` within a skill holds focused technical material that is not needed on every activation, such as the relevant MCP tool details, search examples, error interpretation, or longer formatting guidance. The `SKILL.md` must say exactly when to load each reference. File references are relative to the skill root and remain one level deep; reference files do not point agents through further chains.

`scripts/` within a skill is reserved for deterministic logic an agent would otherwise recreate repeatedly, such as validating a structured Q&A draft. A script is not required merely because the skill calls MCP tools. Any bundled script must be non-interactive, self-contained or explicit about dependencies, support concise `--help`, return meaningful exit codes, emit structured results to stdout and diagnostics to stderr, handle retries safely, and use safe defaults. Stateful or destructive helpers also require a dry-run path. Skill-local scripts are added only when evaluation traces demonstrate that they improve reliability.

`assets/` within a skill holds static templates or schemas, such as an adaptable Q&A or incident template. Short, always-needed output shapes stay inline in `SKILL.md`; larger or conditional templates move to assets.

`evals/` within each skill contains realistic prompts, expected outcomes, trigger cases, and optional fixtures. Keeping evals beside the skill makes its quality evidence portable and reviewable.

`standards/` is maintainer-facing governance, not a runtime dependency. It defines catalog fields and invariants that must remain consistent across skills: conditional search, full-content retrieval, duplicate detection, existing-tag validation, source attribution, and write confirmation. Because the Agent Skills format has no portable dependency mechanism, every skill includes its own concise safety-critical instructions. Contract tests guard those deliberately repeated invariants against drift.

`adapters/` explains how to connect and install the canonical behavior in a particular agent. Adapters may translate file placement or native instruction syntax, but may not change triggers, safety rules, or workflow semantics.

`catalog/skills.json` is the browseable machine-readable index. It enables filtering and leaves a path to a future hosted marketplace without making that marketplace part of v1.

`scripts/` and `tests/` at the repository root validate the catalog and cross-skill policy contract. They do not become part of an installed skill and do not call a customer's live Stack Internal instance.

## Canonical skill contract

Every `SKILL.md` contains YAML frontmatter followed by Markdown instructions. It follows the Agent Skills field constraints:

- `name` is required, matches the parent directory, is 1-64 characters, and uses lowercase letters, numbers, and single hyphens only.
- `description` is required, is no more than 1024 characters, and states both what the skill does and when to use it. It emphasizes user intent and includes high-signal trigger language without becoming so broad that routine work activates the skill.
- `license` identifies the repository license or bundled license file.
- `compatibility` is included only when useful and states the requirement for a connected Stack Internal MCP server and network access.
- `metadata` contains only string key-value pairs. Project-specific keys are namespaced as `stack-internal-tier`, `stack-internal-version`, `stack-internal-write-actions`, and `stack-internal-adapters`.
- `allowed-tools` is not used in v1 because the field is experimental and MCP tool identifiers can vary across clients. Required MCP capabilities remain explicit in the body and catalog.

The human-readable contract includes:

- Purpose and user intent.
- Automatic triggers and explicit invocation examples.
- Required MCP tools and whether the workflow can propose writes.
- Preconditions and safety-critical policies.
- Step-by-step workflow with bounded decision points.
- Expected response and draft formats.
- Confirmation and sensitive-data rules.
- Failure and fallback behavior.
- Positive, negative, and edge-case scenarios.
- Explicit instructions describing when to load each optional local resource.

The main `SKILL.md` stays below both 500 lines and the recommended 5,000-token budget. It contains the procedure, fragile safety gates, and non-obvious gotchas needed on every activation. Detailed or conditional information moves into focused local resources so agents load it only when necessary.

The catalog entry repeats only discovery metadata: identifier, name, version, tier, summary, path, tags, required tools, write capability, supported adapters, and adapter compatibility status. The identifier equals the specification-compliant skill `name`; the `SKILL.md` remains the source of truth for behavior.

For v1, `tier` is `core` or `extended`; adapter compatibility is `supported`, `experimental`, or `unsupported`; and write actions are an explicit list drawn from `draft_question`, `create_question`, `create_QA`, `create_article`, `submit_user_answer`, `update_question`, `update_answer`, and `vote`. Required tool names must exist in the catalog schema's documented MCP tool enumeration.

## Shared behavior model

1. Inspect the user's request and available code context.
2. Decide whether a high-signal internal trigger is present.
3. If no trigger is present, continue without Stack Internal.
4. If a trigger is present, search Stack Internal with a focused query.
5. Retrieve the full question or article for promising results.
6. Decide whether the retrieved content is relevant and sufficient.
7. Apply or summarize relevant content and identify the source title and ID.
8. Clearly separate Stack Internal evidence from the agent's own inference.
9. If no relevant content exists, report the gap rather than implying that company guidance exists.
10. If knowledge should be created or updated, prepare a draft and request approval.
11. Perform a write only after approval of the exact content and action.

### High-signal triggers

Automatic search is appropriate when a task depends on likely company-specific knowledge, including:

- Internal standards, policies, conventions, or architectural decisions.
- Debugging unfamiliar company code, services, infrastructure, or recurring errors.
- TODOs, ambiguous behavior, or undocumented implementation choices.
- Security, privacy, compliance, authentication, or regulated workflows.
- Company onboarding, local development, deployment, or operational processes.
- Requests to identify an internal expert or prior incident.
- Requests to document, update, or curate company knowledge.

Routine language questions, generic algorithms, isolated formatting changes, and tasks with no plausible internal dependency must not trigger a search automatically.

## Core skills

### Efficient search

Purpose: find the smallest sufficient set of relevant Stack Internal sources with minimal tool calls and no unsupported synthesis.

Workflow:

1. Extract distinctive error text, component names, internal terms, and likely tags.
2. Start with a concise, focused query rather than copying the entire user prompt.
3. Inspect titles, tags, IDs, and snippets from `search`.
4. Fetch promising items with `get_question` or `get_article` before using them as evidence.
5. If results are weak, broaden the query by removing incidental details or trying a close synonym. A lookup uses at most three search calls: the focused query and up to two broadened queries, unless the user explicitly asks to keep searching.
6. Stop when relevant evidence is found or the bounded sequence is exhausted.
7. Cite source titles and IDs and label any inference not established by those sources.

### Company-grounded debugging

Purpose: diagnose technical problems using company knowledge before falling back to generic patterns.

Workflow:

1. Capture symptoms, exact errors, environment, recent changes, component names, and attempted fixes.
2. Use efficient search for the error and affected component.
3. Retrieve full relevant Q&A or articles.
4. Compare internal guidance with the observed code and runtime evidence.
5. Identify whether the proposed fix is established company practice, a partial match, or a new hypothesis.
6. Continue normal debugging when internal evidence is insufficient, while preserving that distinction in the response.
7. After validation, offer the capture-quality-Q&A workflow when the result is reusable.

### Capture quality Q&A

Purpose: turn a resolved problem into durable, useful knowledge without copying conversation noise or producing generic AI prose.

Workflow:

1. Extract the actual problem, relevant environment, minimal reproduction, root cause, resolution, validation, and prevention guidance.
2. Search Stack Internal for duplicates or an existing answer that should be updated.
3. Remove greetings, narration, speculation, repeated context, secrets, personal data, and unsupported claims.
4. Write a searchable question title and a self-contained body.
5. Write a direct answer that explains why the fix works and how it was verified.
6. Call `get_existing_tags` and select only valid tags when the intended write requires them.
7. Show the complete draft, target action, and tags to the user.
8. Publish or update only after exact-draft approval.

The default Q&A structure is: problem, context, reproduction or symptoms, root cause, resolution, validation, and prevention. Sections without useful information may be omitted rather than padded.

## Extended skills

- **Onboarding:** assemble a sourced, role- or task-specific learning path from existing internal content.
- **Find SME:** search for the topic, resolve an existing tag ID with `get_existing_tags`, then use `recommend_SME`.
- **Incident to knowledge:** search for related incidents and draft a record containing impact, timeline, root cause, resolution, validation, and follow-up actions.
- **Fill knowledge gap:** activate only after bounded search finds no relevant content; draft a focused question for review.
- **Review stale content:** compare existing content with current code or practices, identify evidence of divergence, and propose an update.
- **Triage unanswered:** use `get_questions_to_answer`, gather related internal evidence, and draft an answer for review.

Extended skills use the same search and capture semantics as the core skills. They may recommend another installed skill when the client supports composition, but they must remain independently usable because the Agent Skills specification does not define portable inter-skill dependencies. Each extended skill therefore carries the concise, safety-critical subset it needs; contract tests ensure those rules do not drift.

## Write safety

All content creation, answers, edits, and votes are writes. Every write follows this sequence:

1. Search for duplicate or related content.
2. Retrieve valid tags when required.
3. Show the exact content, target, tags, and intended tool action.
4. Receive explicit user approval.
5. Execute the approved action without modifying the approved payload. Server-added provenance or system metadata does not invalidate the approval.
6. Report the result, including the created or updated content ID when available.

Approval does not transfer to a changed draft or a different action. Any material change requires approval again. Downvotes and upvotes both require confirmation. Skills must never embed credentials, secrets, tokens, personal data, or unnecessary customer information in a proposed write.

## Failure handling

- **MCP unavailable or unconfigured:** state that Stack Internal could not be accessed and ask whether to continue using general knowledge.
- **Authentication or permission failure:** report the access problem and do not attempt to bypass it.
- **No useful results:** complete bounded query broadening, report the gap, and offer the fill-knowledge-gap workflow.
- **Truncated result:** retrieve the full content; if retrieval fails, label the evidence incomplete.
- **Conflicting internal guidance:** show the conflict and source IDs. Use relevance, accepted status, support, and recency when available to explain which source appears stronger, but do not silently merge contradictions.
- **Missing required tool:** identify the unavailable workflow step and do not substitute an unintended action.
- **Write failure:** preserve the approved draft, report that nothing was confirmed as published, and allow an explicit retry after the underlying issue is addressed.

At no point may a skill claim that Stack Internal was searched successfully when the corresponding MCP calls failed.

## Agent adapters

Each adapter documents:

- Stack Internal MCP connection prerequisites.
- Supported personal and project installation scopes.
- Whether the client natively supports Agent Skills folders.
- Native skill locations and copy/setup steps for compatible clients.
- A clearly labeled instruction-file fallback for clients without native Agent Skills support.
- A smoke-test prompt and observable expected behavior.
- Known limitations and compatibility status.

The initial adapters are Codex, Claude Code, Cursor, and GitHub Copilot. Native Agent Skills installation is preferred where the client supports it; the repository does not claim native support without confirming the client's current documentation. Adapter behavior is considered compatible only when its smoke tests and behavior evals pass. Agent-specific convenience features may be documented, but an adapter cannot weaken the canonical skill's safety policy.

## Verification strategy

### Catalog validation

- Every skill passes `skills-ref validate <skill-directory>`.
- Every catalog entry has a unique identifier and points to an existing skill.
- Tiers, compatibility values, and tool names come from defined enumerations.
- Each entry declares write capability and supported adapters.
- The catalog and skill metadata agree.
- Every `name` matches its directory and every `description` satisfies the Agent Skills length and content requirements.

### Contract validation

- Every skill contains all required contract sections.
- Every referenced local resource exists, uses a skill-root-relative path, and is one reference hop from `SKILL.md`.
- No installed skill depends on a repository-level runtime file or another skill.
- Every write-capable skill includes exact-draft approval.
- Every content-creation workflow includes duplicate detection and valid-tag retrieval where required.
- Safety-critical policy invariants agree across all relevant skills.
- Every script is non-interactive, documents usage, separates structured output from diagnostics, and has safe retry behavior.

### Behavior scenarios

Each skill contains `evals/evals.json` with realistic prompts, expected outcomes, and optional input fixtures. Initial skill development starts with two or three output-quality cases, including an edge case, and compares runs with the skill against runs without it or against the previous skill version. Each case is expanded with specific, observable assertions after inspecting the first outputs.

Each skill also contains `evals/trigger-evals.json` with realistic positive cases and near-miss negative cases. Core skills target at least eight should-trigger and eight should-not-trigger queries; extended skills start with at least four of each and expand when false positives or missed activations appear. Trigger queries vary phrasing, explicitness, context, detail, and common typos. Adapter evaluation runs each query multiple times because model activation is nondeterministic and records the observed trigger rate.

Behavior fixtures define the user request, simulated MCP responses, expected tool sequence, forbidden actions, and response characteristics. Static tests validate fixture structure and skill coverage; adapter smoke tests use selected fixtures as a manual compatibility checklist. The initial suite covers:

- An internal-policy question triggers search.
- A generic question does not trigger search.
- A promising result triggers full-content retrieval.
- Weak search results cause bounded broadening rather than repeated unbounded calls.
- Debugging distinguishes internal guidance from a new hypothesis.
- No results produce a knowledge-gap offer but no automatic write.
- Duplicate content prevents creation of a new Q&A.
- Every write pauses for exact-draft approval.
- A changed draft invalidates prior approval.
- MCP, authentication, and permission failures are reported honestly.
- Sensitive content is removed from proposed Q&A.
- Equivalent scenarios preserve behavior across all supported adapters.

## Contribution model

New skills enter the extended tier by default. A skill belongs in the core tier only when it is a broadly required foundation used by multiple workflows. Contributions must follow the Agent Skills specification and canonical contract, remain self-contained, add catalog metadata, declare tool and write requirements, provide evals, and update relevant adapters.

Reviewers reject skills that duplicate existing workflows, silently broaden automatic triggers, weaken write confirmation, depend on an undocumented MCP tool, create empty optional directories, or add scripts and references without a concrete progressive-disclosure need.

## Acceptance criteria

The v1 catalog is complete when:

- All three core and six extended skills satisfy the contract.
- Every skill passes the `skills-ref` reference validator.
- Catalog and contract validation pass.
- Every skill includes its initial output and trigger eval sets, and the initial behavior suite passes for the canonical skills.
- Codex, Claude Code, Cursor, and GitHub Copilot adapters document installation and pass their smoke-test checklist.
- A new customer can connect the Stack Internal MCP server, select an adapter, install the core bundle, and observe high-signal conditional search without repeatedly asking the agent to use Stack Internal.
- No tested write occurs without approval of the exact content and action.

## Future evolution

After the v1 workflows and metadata stabilize, the catalog can support generated agent packs, an installer, organization-specific bundles, compatibility automation, and a hosted marketplace UI. Those features should consume the canonical skill contract and catalog rather than introduce a second source of truth.

## References

- [Stack Internal MCP Server Quickstart Guide](https://support.stackenterprise.co/support/solutions/articles/22000294548-mcp-server-quickstart-guide)
- [Stack Internal MCP Server Agent Instructions](https://support.stackenterprise.co/support/solutions/articles/22000295101-mcp-server-agent-instructions)
- [Stack Internal MCP Server Use Cases](https://support.stackenterprise.co/support/solutions/articles/22000295102)
- [Agent Skills Overview](https://agentskills.io/home)
- [Agent Skills Specification](https://agentskills.io/specification)
- [Best Practices for Skill Creators](https://agentskills.io/skill-creation/best-practices)
- [Using Scripts in Skills](https://agentskills.io/skill-creation/using-scripts)
- [Evaluating Skill Output Quality](https://agentskills.io/skill-creation/evaluating-skills)
- [Optimizing Skill Descriptions](https://agentskills.io/skill-creation/optimizing-descriptions)
