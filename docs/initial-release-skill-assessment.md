# Initial release skill assessment

Assessment date: 2026-08-17

## Decision rule

Keep a skill in the initial marketplace only when it adds a reusable decision process, evidence transformation, or multi-step outcome that the Stack Internal MCP tool contract does not already describe. A skill is redundant when its main value is selecting one dedicated tool, restating that tool's inputs, or repeating the MCP's global retrieval and creation instructions.

The connected MCP exposes 15 tools. Its shared description already tells agents to use keyword searches, vary queries, retrieve promising questions or articles in full, cite used posts, avoid fabrication, report no results, show drafts before posting, and retrieve existing tags before creating content. This assessment treats those declarations as the client-visible contract; the remote server implementation and enforcement tests were not available locally.

## Initial release

| Skill | Decision | Distinct value beyond the MCP contract |
| --- | --- | --- |
| `uncertainty-guardrail` | Add as core | Inspects local evidence first, isolates one unsupported company decision, classifies evidence, prevents consequential guesses, continues unrelated safe work, and routes only the unresolved portion. |
| `onboarding` | Keep | Synthesizes several retrieved topics into a role- and goal-specific learning path with explicit coverage gaps. No MCP tool produces an onboarding path. |
| `incident-to-knowledge` | Keep | Converts an objective incident record into a verified durable artifact while separating incident facts, related internal knowledge, unresolved facts, and inference. |
| `review-stale-content` | Keep | Compares retrieved guidance with independently verified current code or practice and classifies divergence before proposing a narrow update. |

## Removed from the initial release

| Skill | Redundancy assessment | Preserved value |
| --- | --- | --- |
| `efficient-search` | Its central query, retrieval, citation, and no-fabrication procedure repeats the global `search`, `get_question`, and `get_article` descriptions. | Local-first activation, bounded research, absence-versus-failure handling, and inference separation move into `uncertainty-guardrail`. |
| `company-debugging` | It combines generic debugging practice with the same retrieval loop as `efficient-search`; its evidence labels overlap the uncertainty story. | Local/runtime evidence comparison and partial blocking move into `uncertainty-guardrail`. Generic debugging remains agent-native behavior. |
| `capture-quality-qa` | It acts as a broad router over nearly every write tool and repeats draft review, tag lookup, and payload mechanics already declared by the MCP. Its `create_QA` eval also modeled stale inputs (`question` and no `draftReviewed`) instead of the live `body` and review flag. | Incident-specific capture remains in `incident-to-knowledge`; exact approval remains on retained write workflows. |
| `find-sme` | `recommend_SME(tagId)` is already a dedicated MCP capability. A standalone skill mostly adds mechanical tag resolution. | Exact owner routing is used only as the escalation step inside `uncertainty-guardrail`. |
| `fill-knowledge-gap` | It composes the MCP's ordinary search contract with the dedicated `draft_question` or `create_question` tools. | Access failure is not absence, exact unresolved-question framing, and no-guess behavior move into `uncertainty-guardrail`. Question creation remains available directly through MCP. |
| `triage-unanswered` | `get_questions_to_answer(topicOrTag)` already exposes the queue, while answer submission and voting each have dedicated tools. The skill's additional prioritization is not an initial-release story. | Reconsider as a later backlog-management skill only if users need repeatable prioritization beyond queue discovery. |

## Uncertainty guardrail source

The guardrail is adapted from the brownfield demo's `product-knowledge-context` and `engineering-practice-context` workflows at commit [`a608b13693bdc6d440648fcabdce8c7e57185d94`](https://github.com/EstoesMoises/brownfield-stack-internal-skills-demo/tree/a608b13693bdc6d440648fcabdce8c7e57185d94/.agents/skills). The demo did not contain one standalone guardrail; it repeated the same local-first evidence gate and uncertainty routing across two domain skills. The initial release consolidates that mechanism into one portable workflow and omits Orbit-specific search maps.

The retained story is:

> When correct work depends on a company-specific fact that local evidence cannot establish, complete the independently supported work, do not guess the uncertain behavior, identify the exact missing decision and owner, and block only the knowledge-dependent portion.

## Contract risks found

- Tool descriptions are agent instructions, not proof of server-side enforcement.
- `draftReviewed` is caller-supplied and therefore is not an independently verified approval record.
- `create_article`, answer submission, updates, and votes expose no approval field.
- MCP results expose generic `CallToolResult` values rather than declared output schemas.
- The retained incident eval must include the live `create_article.articleType` field; hard-coded schemas in skills should otherwise defer to the connected tool definition.

These risks should be resolved in the MCP server where possible. Skills remain workflow guidance and defense in depth, not a security boundary.
