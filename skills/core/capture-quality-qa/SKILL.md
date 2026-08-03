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
3. Prefer an update when a retrieved item already answers the same problem, has an outdated answer, or is the correct existing question. Select the narrowest matching action and its `target_id`: update a question or answer, submit an answer, or vote only when the intended target is retrieved and clear. For `update_answer`, `target_id` is the retrieved answer ID, never its parent question ID. Create a new item only when no appropriate existing target remains after duplicate review.
4. Call `get_existing_tags` before composing an action that requires tags. Use only returned valid tags, selecting the smallest relevant set. Do not invent a tag or substitute a similarly named one.
5. Remove chat narration, greetings, repeated context, filler, speculation, unsupported claims, credentials, tokens, personal data, and unnecessary customer names before display. Keep a claim only when it is verified by the resolved work or retrieved source; label any remaining inference rather than presenting it as fact.
6. Render the complete local payload with [the Q&A template](assets/qa-template.md). It must contain exactly `{title, question, answer, tags, intended_action, target_id?}`; omit `target_id` only when the action has no existing target. `intended_action` is an object with the exact `tool` and every required `args`. For a vote, include the exact supported `operation` (`upvote`, `downvote`, or `remove` only when the documented tool contract supports it) and `target_type`. Do this locally: `draft_question` is also a state-changing call and is forbidden before approval.
7. Show the user the rendered local payload, including its exact intended-action tool and arguments and target ID where present. Load [the write-tool map](references/write-tools.md) when choosing a tool, target, tag requirement, vote operation, or confirmation prerequisite.

## Approval gate

Stop after showing the exact local payload. Do not call `draft_question`, `create_question`, `create_QA`, `submit_user_answer`, `update_question`, `update_answer`, or `vote` until the user explicitly approves that displayed payload, its intended action and exact arguments, and its target.

Approval covers only the unchanged displayed client payload, action, arguments, and target. Any material content, tag, action, argument, or target change requires redisplaying the full payload and obtaining new approval; a changed payload requires new approval. After approval, execute only that unchanged payload. Never infer, default, or invent action arguments after approval. Server-added provenance or system metadata is allowed only when it does not change or hide any client payload field; if the server changes a client field, redisplay it and obtain approval again.

## Confirmed result

After the approved call returns: Report the confirmed result and returned created or updated content ID when available. Never claim success without server confirmation. If the server does not return an ID, say that explicitly rather than inventing one.

## Failure handling

- If Stack Internal, authentication, permission, or a required tool is unavailable, report the failed step honestly. Do not claim that a search, retrieval, or write succeeded.
- If duplicate retrieval is incomplete, say the duplicate check is incomplete and do not claim the new Q&A is unique. Preserve the local draft only for review; do not write it.
- If no relevant item is found after the bounded search, state the knowledge gap and prepare a new local draft only when the resolved evidence is sufficient.
- If valid tags cannot be retrieved for an action that requires them, stop before the approval gate and ask for the missing access or valid tags; do not invent them.
- If the approved write fails or returns no confirmation, preserve the approved payload, report that publication was not confirmed, and require an explicit retry after the cause is addressed.
