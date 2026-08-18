---
name: uncertainty-guardrail
description: Resolve company-specific uncertainty without guessing when a coding or operational task depends on a product rule, engineering practice, policy, ownership boundary, or supported workflow that local code, tests, issue text, documentation, and history do not establish. Inspect local evidence first, isolate the exact unresolved decision, continue unrelated safe work, and route missing or conflicting evidence to an appropriate owner. Do not use for direct Stack Internal searches, generic questions, or behavior already specified locally.
license: Apache-2.0
compatibility: Requires a connected Stack Internal MCP server and network access.
metadata:
  stack-internal-tier: core
  stack-internal-version: "0.1.0"
  stack-internal-write-actions: "none"
  stack-internal-adapters: "codex,claude-code,cursor,github-copilot"
---

# Uncertainty Guardrail

Prevent unsupported company-specific assumptions from becoming code or operational decisions. Keep local evidence primary, use Stack Internal only for the unresolved decision, and block only work whose correctness depends on that decision.

## Workflow

1. Inspect the task, implementation, tests, local documentation, relevant configuration, and history. State one exact company-specific decision that remains unresolved. If local evidence establishes it, proceed from that evidence and do not call Stack Internal.
2. Separate work that is already supported from work that depends on the unresolved decision. Continue the supported, safe portion when it can be changed and verified independently.
3. Search Stack Internal for the unresolved decision under the connected MCP's retrieval contract. Reformulate only when a materially different query could resolve the uncertainty, with at most three searches unless the user asks for broader research.
4. Evaluate retained full sources for direct applicability, effective date, version, environment, owner, exceptions, and supersession. Retrieve comments when they could change scope or freshness. Keep source-backed conclusions separate from inference.
5. Classify the decision exactly once:
   - `supported`: current, directly applicable full evidence establishes the decision without a material conflict.
   - `conflicting`: applicable full sources disagree, or current local evidence contradicts the internal guidance.
   - `unknown`: no adequate full source was found, the required scope or freshness is missing, or MCP access or retrieval failed.
6. For `supported`, implement only the behavior the evidence establishes and record the source title and content ID in the work notes. Never infer authorization, entitlement, policy, compatibility, or approval from UI visibility, existing usage, popularity, or legacy code alone.
7. For `conflicting` or `unknown`, state the exact clarification needed and the affected work. When an exact ownership tag can be resolved from existing tags, use it to request an SME recommendation; do not guess a tag ID or an owner. This workflow performs no Stack Internal writes.
8. Report the supported work completed, the knowledge-dependent work left unchanged, the evidence and conflict or gap, the recommended owner when available, and the next decision needed. Do not describe the whole task as blocked when only one portion is uncertain.

## Response shape

```markdown
Uncertainty decision
- Question: <one exact company-specific decision>
- Status: <supported | conflicting | unknown>
- Supported work: <completed or independently safe work>
- Knowledge-dependent work: <work completed from evidence or left unchanged>
- Evidence: <source title and content ID, or None>
- Gap or conflict: <missing scope, freshness issue, conflicting claims, access failure, or None>
- Owner route: <recommended SME and resolved tag, or Not resolved>
- Clarification needed: <one answerable question, or None>
- Inference: <reasoning beyond the evidence, or None>
```

## Failure handling

- Treat an MCP, authentication, permission, search, or retrieval failure as `unknown`, never as proof that guidance does not exist.
- Treat a search summary, title, tag, score, model memory, or undated example as discovery rather than support for the decision.
- If full sources conflict or their scope cannot be reconciled, classify `conflicting`; do not silently choose the convenient answer.
- If no exact ownership tag is available or several tags are equally plausible, report that routing is unresolved instead of selecting the closest-looking tag.
- If the uncertain portion cannot be isolated safely, stop before the consequential change and explain the smallest decision required to continue.
