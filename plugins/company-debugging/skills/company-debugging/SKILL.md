---
name: company-debugging
description: Debug company code, services, infrastructure, deployments, and recurring errors by grounding diagnosis in Stack Internal before generic knowledge. Use for unfamiliar internal components, exact error messages, TODOs, ambiguous behavior, security-sensitive flows, or fixes that may depend on company conventions. Do not use for isolated generic programming questions.
license: Apache-2.0
compatibility: Requires a connected Stack Internal MCP server and network access.
metadata:
  stack-internal-tier: core
  stack-internal-version: "0.1.0"
  stack-internal-write-actions: "none"
  stack-internal-adapters: "codex,claude-code,cursor,github-copilot"
---

# Company-Grounded Debugging

Ground diagnosis in retrieved Stack Internal evidence, then investigate the actual failure systematically. Require `search`, `get_question`, `get_article`, and `get_comments`. This workflow is read-only: do not draft, create, update, answer, or vote.

## Workflow

1. Use Stack Internal only for high-signal company debugging: an internal service, deployment, CI failure, unfamiliar module, ambiguous implementation note, authentication or logging policy, or recurring operational error. For an isolated generic problem, debug without an automatic search.
2. Capture the symptom, exact error, environment, component, recent changes, reproduction, runtime evidence, and attempted fixes. Read the error and stack trace; reproduce it when possible before proposing a fix.
3. Search once with the exact error and affected component. Treat titles, tags, snippets, and scores as discovery only. Rank promising results by direct relevance, then retrieve the strongest question with `get_question` or article with `get_article`. For a relevant Q&A source, retrieve its comments with `get_comments`; use them as attributed context, not as a replacement for the full source. Reassess sufficiency from the full content and comments.
4. Broaden only when the strongest retrieved evidence is insufficient. Make at most two broader searches by removing incidental details or using a close component synonym. After each search, rank candidates, retrieve the strongest full source and relevant comments, then reassess. Stop as soon as sufficient evidence is retrieved or the three-search limit is exhausted.
5. Compare retrieved guidance against the code and runtime evidence. Continue root-cause investigation: trace data flow, inspect recent changes and configuration, compare a working path, form one testable hypothesis, and test it minimally. Stack Internal evidence informs this investigation; it never substitutes for it.
6. Label the diagnosis exactly once:
   - `established-company-practice`: directly relevant full content establishes the fix, and code or runtime evidence matches its conditions.
   - `partial-internal-match`: usable internal material is similar, incomplete, materially mismatched, or conflicting. State the gap or conflict.
   - `new-hypothesis`: no usable internal evidence exists, including when Stack Internal is unavailable or the bounded search has no relevant result. State the hypothesis as unverified and continue systematic debugging.
7. Verify the fix with the smallest relevant reproduction, test, deployment check, or runtime observation. Report what passed and what remains unverified.
8. Only after verification, offer to capture reusable learning as a Q&A. Do not create or draft content in this workflow.

Load [the evidence playbook](references/evidence-playbook.md) only when multiple internal sources conflict or source strength is unclear.

## Response shape

```markdown
Diagnosis: <established-company-practice | partial-internal-match | new-hypothesis>

Company evidence
- <title> (ID: <id>): <what its retrieved full content establishes>
- Comments on <title> (ID: <id>): <relevant attributed context, if any>

Code and runtime evidence: <observed facts>
Gap or conflict: <mismatch, conflict, or "None.">
Hypothesis and next check: <one testable statement and check>
Verification: <passed evidence or what remains unverified>
```

Do not call an inference, a search snippet, or a failed MCP request company guidance.

## Failure handling

- If Stack Internal, authentication, permission, or a required tool is unavailable, disclose the failed step. Continue only with `new-hypothesis` reasoning if appropriate; do not convert a failed MCP request into a claim about company practice.
- If full retrieval or comment retrieval fails, mark that evidence incomplete and do not use a snippet or partial result to establish a practice. Use `partial-internal-match` when relevant incomplete material remains; use `new-hypothesis` only when no usable internal evidence remains.
- If searches produce no relevant result after the bounded sequence, report the knowledge gap and continue systematic debugging as `new-hypothesis`.
- If internal sources conflict, label the diagnosis `partial-internal-match`, name the conflict and source IDs, and use the evidence playbook to explain source strength. Do not merge contradictory guidance.
- If verification fails, keep the diagnosis provisional, return to the observed evidence, and test a new single hypothesis rather than stacking fixes.
