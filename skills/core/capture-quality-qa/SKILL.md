---
name: capture-quality-qa
description: Turn a resolved technical problem, incident, or non-obvious implementation into a concise Stack Internal Q&A draft. Use after a fix is validated or when the user asks to document reusable knowledge. Search for duplicates and valid tags, remove chat filler and sensitive data, and require approval before any draft, create, update, answer, or vote tool call.
license: Apache-2.0
compatibility: Requires a connected Stack Internal MCP server and network access.
metadata:
  stack-internal-tier: core
  stack-internal-version: "0.1.0"
  stack-internal-write-actions: "draft_question,create_question,create_QA,submit_user_answer,update_question,update_answer,vote"
  stack-internal-adapters: "codex,claude-code,cursor,github-copilot"
---

# Capture High-Quality Stack Internal Q&A

Turn verified, reusable knowledge into a concise Q&A without copying conversation noise or publishing on the user's behalf. Require `search`, `get_question`, `get_article`, and `get_existing_tags`; the only permitted write capabilities are `draft_question`, `create_question`, `create_QA`, `submit_user_answer`, `update_question`, `update_answer`, and `vote`.

## Workflow

1. Confirm the learning is reusable and sufficiently validated. Extract only supported facts: problem, relevant context, minimal reproduction or symptoms, root cause, resolution, validation, and prevention. If the root cause or validation is still speculative, ask for evidence or keep investigating; do not capture a speculative incident theory as settled knowledge.
2. Search Stack Internal once using the distinctive problem, component, and error or behavior. Search results, titles, tags, and snippets are discovery data, not evidence. Retrieve each promising near match in full with `get_question` or `get_article`; make at most two broadened searches if needed, then stop unless the user asks to continue.
3. Prefer an update when a retrieved item already answers the same problem, has an outdated answer, or is the correct existing question. Select the narrowest matching action and show a structured `target` containing the retrieved `question_id`, optional `answer_id`, and `content_type`; retain `target_id` as the answer ID for answer operations and the question ID otherwise. An answer update or vote must preserve both IDs because the current modeled schema uses `update_answer(questionId, answerId, newBodyContent)` and `vote(questionId, optional answerId, isUpvote, action)`. Runtime schema inspection remains authoritative. Create a new item only when no appropriate existing target remains after duplicate review.
4. Call `get_existing_tags` before composing an action that requires tags. Use only returned valid tags, selecting the smallest relevant set. Do not invent a tag or substitute a similarly named one.
5. Remove chat narration, greetings, repeated context, filler, speculation, unsupported claims, credentials, tokens, personal data, and unnecessary customer names before display. Keep a claim only when it is verified by the resolved work or retrieved source; label any remaining inference rather than presenting it as fact.
6. Before rendering, inspect the connected MCP tool's current input schema for the selected action. Public tool descriptions identify purposes, not portable parameter names. Construct `intended_action.args` as the complete argument object that the live schema requires, using its exact current parameter keys and values. Copy or derive every content, target, and tag value visibly from the top-level payload. If the schema is unavailable or ambiguous, or the complete arguments cannot be rendered, stop without writing.
7. Render the complete local payload with [the Q&A template](assets/qa-template.md). Include the visible structured target for existing content and exact schema-derived `intended_action.args`. For a vote, never preserve or reproduce raw retrieved answer text: show IDs, question title, exact Boolean direction and add-or-remove action, plus only a sanitized concise context or neutral redaction notice. Every executable argument must visibly derive from the displayed payload. Do this locally: `draft_question` is also a state-changing call and is forbidden before approval.
8. Show the user the rendered local payload, including its exact intended-action tool and complete arguments and target ID where present. Load [the write-tool map](references/write-tools.md) when choosing a tool, target, tag requirement, vote operation, live schema mapping, or confirmation prerequisite.

## Approval gate

Stop after showing the exact local payload. Do not call `draft_question`, `create_question`, `create_QA`, `submit_user_answer`, `update_question`, `update_answer`, or `vote` until the user explicitly approves that displayed payload, its intended action and exact arguments, and its target.

Approval covers only the unchanged displayed client payload, action, arguments, and target. Any material content, tag, action, argument, or target change requires redisplaying the full payload and obtaining new approval; a changed payload requires new approval. After approval, call the selected tool with `intended_action.args` byte-for-byte. Never transform, infer, default, or invent action arguments after approval. Server-added provenance or system metadata is allowed only when it does not change or hide any client payload field; if the server changes a client field, redisplay it and obtain approval again.

## Confirmed result

After the approved call returns: Report the confirmed result and returned created or updated content ID when available. Never claim success without server confirmation. If the server does not return an ID, say that explicitly rather than inventing one.

## Failure handling

- If Stack Internal, authentication, permission, or a required tool is unavailable, report the failed step honestly. Do not claim that a search, retrieval, or write succeeded.
- If duplicate retrieval is incomplete, say the duplicate check is incomplete and do not claim the new Q&A is unique. Preserve the local draft only for review; do not write it.
- If no relevant item is found after the bounded search, state the knowledge gap and prepare a new local draft only when the resolved evidence is sufficient.
- If valid tags cannot be retrieved for an action that requires them, stop before the approval gate and ask for the missing access or valid tags; do not invent them.
- If the selected write tool's current input schema is unavailable, ambiguous, or cannot be mapped completely from the visible payload, stop before the approval gate; do not guess parameter names or omitted values.
- If a write fails, its outcome is ambiguous, or its response is lost, never blindly retry or reuse prior approval. First reconcile the current server state read-only with duplicate search and the appropriate current question/answer retrieval. Before every retry, rebuild and redisplay the complete exact payload, target, action, and arguments, then obtain fresh explicit approval immediately before the call even when nothing changed.
