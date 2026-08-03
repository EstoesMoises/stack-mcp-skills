# Stack Internal MCP Skills Catalog Design

## Summary

Build a public, Git-based catalog of portable agent skills that teach AI agents when and how to use the Stack Overflow Internal MCP server. The catalog will make Stack Internal an automatic, conditional source of company knowledge rather than a tool users must invoke manually.

The first release targets MCP-capable coding agents broadly, with adapters for Codex, Claude Code, Cursor, and GitHub Copilot. It will not include a hosted marketplace, package installer, or code generator. Customers will browse the repository, choose skills or a recommended bundle, and follow the adapter for their agent.

## Goals

- Ground debugging and technical work in trusted company knowledge when the task has a high-signal internal context.
- Teach agents an efficient Stack Internal search strategy, including full-content retrieval and bounded query broadening.
- Turn resolved work into concise, useful, non-generic Q&A without publishing on a user's behalf unexpectedly.
- Provide broader knowledge workflows for onboarding, SME discovery, incident capture, knowledge gaps, stale content, and unanswered questions.
- Keep skill behavior consistent across supported agents while allowing more skills and adapters to be added later.
- Make installation and expected behavior understandable without requiring a build system.

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
- Structure: one portable canonical skill with thin agent adapters.
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
│   │   │   └── SKILL.md
│   │   ├── company-debugging/
│   │   │   └── SKILL.md
│   │   └── capture-quality-qa/
│   │       └── SKILL.md
│   └── extended/
│       ├── onboarding/
│       ├── find-sme/
│       ├── incident-to-knowledge/
│       ├── fill-knowledge-gap/
│       ├── review-stale-content/
│       └── triage-unanswered/
├── shared/
│   ├── search-policy.md
│   ├── write-safety.md
│   └── mcp-tool-reference.md
├── adapters/
│   ├── codex/
│   ├── claude-code/
│   ├── cursor/
│   └── github-copilot/
└── tests/
    ├── contract/
    └── scenarios/
```

Each extended skill directory also contains a `SKILL.md`. A skill may add focused examples or references beneath its own directory, but shared policies must not be copied into individual skills.

### Component boundaries

`skills/` contains agent-neutral behavior. Each skill must be independently understandable and declare its triggers, tool dependencies, workflow, output, safety gates, failures, and examples.

`shared/` contains rules that must be identical across skills: conditional search, full-content retrieval, duplicate detection, existing-tag validation, source attribution, and write confirmation. Skills reference these policies instead of redefining them.

`adapters/` explains how to connect and install the canonical behavior in a particular agent. Adapters may translate file placement or native instruction syntax, but may not change triggers, safety rules, or workflow semantics.

`catalog/skills.json` is the browseable machine-readable index. It enables filtering and leaves a path to a future hosted marketplace without making that marketplace part of v1.

`tests/` holds static contract checks and behavior scenarios. It does not call a customer's live Stack Internal instance.

## Canonical skill contract

Every `SKILL.md` contains machine-readable metadata and human-readable instructions. Its contract includes:

- Stable identifier, name, version, tier, summary, and purpose.
- Supported adapters and compatibility status.
- Automatic triggers and explicit invocation examples.
- Required MCP tools and whether the workflow can propose writes.
- Preconditions and related shared policies.
- Step-by-step workflow with bounded decision points.
- Expected response and draft formats.
- Confirmation and sensitive-data rules.
- Failure and fallback behavior.
- Positive, negative, and edge-case scenarios.

The catalog entry repeats only discovery metadata: identifier, name, version, tier, summary, path, tags, required tools, write capability, supported adapters, and compatibility status. The `SKILL.md` remains the source of truth for behavior.

For v1, `tier` is `core` or `extended`; adapter compatibility is `supported`, `experimental`, or `unsupported`; and write actions are an explicit list drawn from `create_question`, `create_QA`, `create_article`, `submit_user_answer`, `update_question`, `update_answer`, and `vote`. Required tool names must exist in `shared/mcp-tool-reference.md`, which reflects the documented MCP tool surface.

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

Extended skills compose the core search and capture behaviors instead of implementing alternative versions of them.

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
- Native instruction locations and copy/setup steps.
- How the canonical skill and shared policies are referenced.
- A smoke-test prompt and observable expected behavior.
- Known limitations and compatibility status.

The initial supported adapters are Codex, Claude Code, Cursor, and GitHub Copilot. Adapter behavior is considered compatible only when its smoke tests and shared behavior scenarios pass. Agent-specific convenience features may be documented, but the adapter cannot weaken the shared safety policy.

## Verification strategy

### Catalog validation

- Every catalog entry has a unique identifier and points to an existing skill.
- Tiers, compatibility values, and tool names come from defined enumerations.
- Each entry declares write capability and supported adapters.
- The catalog and skill metadata agree.

### Contract validation

- Every skill contains all required contract sections.
- Every referenced shared policy and local resource exists.
- Every write-capable skill includes exact-draft approval.
- Every content-creation workflow includes duplicate detection and valid-tag retrieval where required.
- Extended skills depend on the canonical core behavior rather than duplicating it.

### Behavior scenarios

Each scenario is a deterministic fixture defining the user request, simulated MCP responses, expected tool sequence, forbidden actions, and response characteristics. Static tests validate fixture structure and skill coverage; adapter smoke tests use selected fixtures as a manual compatibility checklist. The initial suite covers:

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

New skills enter the extended tier by default. A skill belongs in the core tier only when it is a broadly required foundation used by multiple workflows. Contributions must follow the canonical contract, reference shared policies, add catalog metadata, declare tool and write requirements, provide scenarios, and update relevant adapters.

Reviewers reject skills that duplicate existing workflows, silently broaden automatic triggers, weaken write confirmation, or depend on an undocumented MCP tool.

## Acceptance criteria

The v1 catalog is complete when:

- All three core and six extended skills satisfy the contract.
- Catalog and contract validation pass.
- The initial behavior scenario suite passes for the canonical skills.
- Codex, Claude Code, Cursor, and GitHub Copilot adapters document installation and pass their smoke-test checklist.
- A new customer can connect the Stack Internal MCP server, select an adapter, install the core bundle, and observe high-signal conditional search without repeatedly asking the agent to use Stack Internal.
- No tested write occurs without approval of the exact content and action.

## Future evolution

After the v1 workflows and metadata stabilize, the catalog can support generated agent packs, an installer, organization-specific bundles, compatibility automation, and a hosted marketplace UI. Those features should consume the canonical skill contract and catalog rather than introduce a second source of truth.

## References

- [Stack Internal MCP Server Quickstart Guide](https://support.stackenterprise.co/support/solutions/articles/22000294548-mcp-server-quickstart-guide)
- [Stack Internal MCP Server Agent Instructions](https://support.stackenterprise.co/support/solutions/articles/22000295101-mcp-server-agent-instructions)
- [Stack Internal MCP Server Use Cases](https://support.stackenterprise.co/support/solutions/articles/22000295102)
