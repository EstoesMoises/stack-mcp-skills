---
name: incident-to-knowledge
description: Turn a resolved internal incident into a sourced Stack Internal article or Q&A. Use for outages, degraded service, failed deployments, security events, and operational incidents after the facts are sufficiently verified. Search related incidents first and require approval of the exact article or Q&A before publishing.
license: Apache-2.0
compatibility: Requires a connected Stack Internal MCP server and network access.
metadata:
  stack-internal-tier: extended
  stack-internal-version: "0.1.0"
  stack-internal-write-actions: "create_article,create_QA"
  stack-internal-adapters: "codex,claude-code,cursor,github-copilot"
---

# Capture a Resolved Incident as Stack Internal Knowledge

Turn a verified internal incident into a concise, factual knowledge record. Require `search`, `get_question`, `get_article`, and `get_existing_tags`; only `create_article` and `create_QA` may be used after exact approval. Do not use this workflow for hypothetical disaster planning, generic monitoring setup, a news summary, or unresolved debugging.

## Preconditions

- Use this skill only for a completed incident with sufficiently verified facts. Facts must come from objective incident evidence such as incident records, timestamps, metrics, logs, reviewed changes, and validation results; identify the evidence source for every material conclusion.
- Treat impact, timeline, root cause, resolution, and validation as material facts. Keep conflicting, missing, or uncertain facts in `unresolved_facts`. Reject a speculative root cause: do not phrase a hypothesis as the cause.
- Do not render an approval-ready draft or publish while unresolved material facts remain. Ask for evidence, corrections, or the completed investigation instead. Non-material open questions may remain visibly marked as unresolved only when they do not alter the incident's scope, cause, resolution, or validation.
- Remove credentials, tokens, personal data, unnecessary customer data, chat narration, blame, and unsupported claims before any draft is displayed.

## Workflow

1. Collect the objective incident record: a concise summary, measured impact and scope, timestamped timeline, verified root cause, resolution, validation, and owned follow-up actions. Keep exact times, time zone when known, measurement units, and observed effects. Label each claim as incident evidence, retrieved Stack Internal evidence, or `Inference:`; do not convert an inference into a fact.
2. Search Stack Internal for related incidents, mitigations, and prior guidance using one concise focused query made from the affected component, distinctive symptom, and incident type. Titles, tags, IDs, and snippets are discovery data, not evidence. Retrieve the strongest promising question with `get_question` or article with `get_article` before relying on it. This is retrieve-before-broaden: retrieve and reassess the strongest result before making a broader query; retrieve another candidate only when the current full content is insufficient.
3. If the focused result is weak or insufficient, make up to two broader searches by removing incidental detail or using a close internal synonym. Make no more than three `search` calls for this lookup unless the user explicitly asks to continue. Stop once sufficient related evidence is retrieved. Cite every used related source by exact title and content ID; a prior incident can inform prevention actions, but cannot prove this incident's root cause or validation.
4. Reconcile the retrieved material with the incident record. Mark every unknown, contradiction, or unverified claim in `unresolved_facts`. If a material fact remains unresolved, state what evidence is needed and stop before tag lookup, rendering, approval, and publishing.
5. Call `get_existing_tags` only after all material facts are sufficiently verified. Select the smallest relevant set from returned valid tags; never invent a tag or replace it with a similar-looking tag.
6. Choose the intended format. Prefer an article for a full incident record, broad reference material, or a chronological account. Prefer Q&A when the durable learning is best expressed as a focused operational question and answer. If article versus Q&A is unclear, ask the user to choose article or Q&A before rendering an approval payload.
7. Before rendering, inspect the selected connected MCP tool's current input schema for `create_article` or `create_QA`. Use the live schema's exact required keys, types, and values to construct the complete `intended_action.args`; tool descriptions and template examples do not establish portable parameter names. If the schema is unavailable, ambiguous, or cannot be mapped completely from the visible payload, stop without writing.
8. Render the complete local record with [the incident template](assets/incident-template.md). Show the entire sanitized draft, its target, valid tags, selected action, and complete exact arguments. Every action argument must visibly copy or derive a value from the displayed record. Rendering is local only; do not call either write tool while composing the draft.

## Approval gate

Stop after showing the complete local payload. Before explicit approval, do not call any write action. Do not call `create_article` or `create_QA` unless the user explicitly approves the displayed draft, target, tags, selected action, and every exact argument.

Approval covers only the unchanged displayed client payload, intended action, target, and arguments. Any material content, unresolved-fact status, tag, action, target, schema mapping, or argument change requires redisplaying the entire payload and obtaining new approval; a changed payload requires new approval. After approval, replay `intended_action.args` byte-for-byte with the selected tool; never add defaults, transform content, infer a parameter, or select a different action. Server-added provenance or system metadata is allowed only when it does not change or hide a client payload field.

## Confirmed result

After the approved call returns, report only the confirmed result and the returned created content ID when available. Never claim success without server confirmation. If the response has no ID, say that the publication result was confirmed but no content ID was returned.

## Failure handling

- If Stack Internal, authentication, permission, a required read tool, or the selected write tool is unavailable, report the failed step honestly. Do not claim a search, retrieval, tag lookup, or publication succeeded.
- If full retrieval fails, mark that related source incomplete and do not use its snippet as evidence. Continue only within the bounded search policy; otherwise report the incomplete related-incident review.
- If no related item is found after the bounded search, state the knowledge gap. A sufficiently verified incident may still have a local draft, but only after valid tags are retrieved and the approval gate is met.
- If valid tags cannot be retrieved, the draft contains unresolved material facts, the format is still unclear, or the live schema cannot be mapped completely, stop without approval or a write.
- If an approved write fails or lacks confirmation, preserve the approved local payload and state that publication was not confirmed. Require an explicit retry after the underlying issue is addressed.
