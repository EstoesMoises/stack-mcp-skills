---
name: fill-knowledge-gap
description: Draft a focused Stack Internal question when a company-specific search has genuinely found no relevant answer. Use after a bounded search for an internal standard, process, service behavior, or unresolved technical gap. Do not activate before searching, for generic public questions, or when an existing question should be updated instead.
license: Apache-2.0
compatibility: Requires a connected Stack Internal MCP server and network access.
metadata:
  stack-internal-tier: extended
  stack-internal-version: "0.1.0"
  stack-internal-write-actions: "draft_question,create_question"
  stack-internal-adapters: "codex,claude-code,cursor,github-copilot"
---

# Fill a Stack Internal Knowledge Gap

Turn a verified absence of company guidance into one narrow, answer-seeking question. Require `search`, `get_question`, `get_article`, and `get_existing_tags`; `draft_question` and `create_question` are writes and are permitted only after exact approval.

## Workflow

1. Confirm this is a company-specific standard, process, service behavior, or unresolved internal technical gap. Do not activate for a generic public question, an unsearched request, or a request that should update an existing question.
2. Form one focused query from the internal system, behavior, and requested standard. Call `search` once. For every possible near match, retrieve its full content before deciding: use `get_question` for a question and `get_article` for an article. A title, tag, or snippet never establishes either a duplicate or an absence.
3. If a fully retrieved item already asks the same question or contains a relevant answer, stop. Identify its title and ID and offer that existing target; do not draft a duplicate, retrieve tags, or call a write action.
4. If the first attempt produces no relevant fully retrieved content, run one broader query that removes incidental detail or uses a close internal synonym. Repeat the full-retrieval duplicate check. If it still produces no relevant content, run one final broader query and repeat the check. Use one focused search and exactly two broadened searches: three calls total. Do not run a fourth search unless the user explicitly asks to continue.
5. No gap claim is permitted until all three successful searches and any possible-match retrievals establish that no relevant content exists. Then explain the searched gap and the queries used. A search, authentication, permission, MCP, or retrieval failure is an unknown access state, not evidence of a gap.
6. Collect only reproducible, answer-neutral context: the internal component or scope, observed behavior or decision blocked, exact error or symptom if known, environment or version when relevant, time bounds, and the question the team needs answered. Remove secrets, credentials, tokens, personal data, customer names, and unnecessary operational detail. Do not suggest, presume, or invent an answer, root cause, owner, policy, or implementation.
7. Call `get_existing_tags` only after the confirmed gap and before a tag-requiring question draft. Select the smallest relevant set only from returned valid tags. If tags cannot be retrieved or no valid tag fits, stop before rendering an approval-ready payload; do not invent tags.
8. Inspect the connected MCP tool's current input schema for the selected `draft_question` or `create_question` action. Construct `intended_action.args` as the complete argument object the live schema requires, using its exact current parameter keys and values. For a connected schema requiring `{title, body, tags, draftReviewed}`, copy the rendered `question` verbatim into `body`; use only valid tags within the schema's cardinality limits; and display the approved Boolean `draftReviewed` value explicitly. Never hide it or infer it after approval. Every argument must visibly copy or derive from the local payload. If the schema is unavailable, ambiguous, or cannot be represented completely, stop without writing.
9. Render this exact local payload, without calling either write tool:

```markdown
title: <focused unanswered question>
question: |
  Context: <reproducible, answer-neutral internal context>
  Observed behavior or decision blocked: <known fact>
  Question: <what company guidance is needed?>
tags: [<only values returned by get_existing_tags>]
draftReviewed: <explicit Boolean reviewed value>
intended_action:
  tool: <draft_question or create_question>
  args:
    title: <title>
    body: <the exact visible question text when required by the connected schema>
    tags: <the exact visible tags>
    draftReviewed: <the exact visible reviewed value>
```

Show the tool, complete arguments, tags, and `draftReviewed` value with the draft. Make clear that it asks for missing guidance and does not assert a proposed answer.

## Approval gate

Stop after showing the exact local payload. Before explicit approval, do not call any write action. Do not call `draft_question` or `create_question` until the user explicitly approves the displayed draft, tags, selected tool, and every exact argument.

Approval covers only the unchanged displayed client payload, action, tags, `draftReviewed` value, and arguments. Any material content, tag, review value, action, schema mapping, or argument change requires redisplaying the full payload and obtaining new approval; a changed payload requires new approval. After approval, call the selected tool with `intended_action.args` byte-for-byte. Never add defaults, transform content, infer a parameter, or switch actions after approval.

## Confirmed result

Report only the confirmed result and returned created or draft content ID when available. Never claim success without server confirmation. If no ID is returned, say that explicitly rather than inventing one.

## Failure handling

- If Stack Internal, MCP connectivity, authentication, or permission fails, report the unavailable access step and ask whether to continue without Stack Internal. Do not call it a knowledge gap, look up tags, render a payload, or attempt a write.
- If a possible match cannot be retrieved in full, label duplicate review incomplete. Do not call it irrelevant, unique, or a gap; do not draft a question until access is restored and that candidate is checked.
- If a fully retrieved duplicate exists, offer its title and ID or an update path. Do not create a competing question or retrieve tags.
- If the bounded search succeeds but finds no relevant content, state the knowledge gap and preserve only the local, answer-neutral draft pending valid tags and approval.
- If a write fails, its outcome is ambiguous, or its response is lost, never blindly retry or reuse prior approval. First reconcile current state read-only with duplicate search and full retrieval of any possible new question, staying within the search limit unless the user authorizes continuation. If the exact approved write already succeeded, report the confirmed result and stop without redisplay, approval, or retry. If reconciliation is inconclusive and a retry remains necessary, rebuild and redisplay the complete exact question payload, action, and arguments, then obtain fresh explicit approval immediately before the call even when nothing changed.
