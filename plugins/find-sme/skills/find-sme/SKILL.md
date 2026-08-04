---
name: find-sme
description: Find an internal subject-matter expert for a technical topic using Stack Internal activity. Use when a user needs the right person to ask, especially after existing content is missing or insufficient. Resolve an existing tag ID before calling the SME tool; do not infer expertise from names, titles, or generic organizational assumptions.
license: Apache-2.0
compatibility: Requires a connected Stack Internal MCP server and network access.
metadata:
  stack-internal-tier: extended
  stack-internal-version: "0.1.0"
  stack-internal-write-actions: "none"
  stack-internal-adapters: "codex,claude-code,cursor,github-copilot"
---

# Find a Stack Internal Subject-Matter Expert

Use this read-only workflow only when the user asks for an internal expert, owner to consult, help from a knowledgeable colleague, or an escalation for a company-specific technical topic. Do not use it for public celebrities, Git authors, organizational charts, or generic technology questions.

Load [the SME tool reference](references/sme-tools.md) only when tool input semantics or the required call order are unclear.

## Workflow

1. Confirm the technical topic and what help the user still needs. If the request has no company-specific context or is not an internal-expert request, continue without Stack Internal.
2. Run one focused `search` for the topic, using distinctive internal component, error, workflow, or technology terms. Search may return titles, tags, IDs, and snippets; these are discovery metadata, not a full-source answer. Do not call `get_question` or `get_article`.
3. Present relevant search hits as discovery, with their title and ID when available. Do not state that a hit answers the question or treat its snippet as evidence. If a successful search has no relevant results or only irrelevant discovery metadata, state `No relevant sources were found.` This is an honest zero-source result, not a search failure.
4. Avoid SME escalation only when the current conversation already contains a verified full-source answer, or the user says a surfaced source resolves the need. A `search` result alone cannot establish either condition. Otherwise, if the user still needs help, continue to `get_existing_tags` even after a successful zero-source result when the topic is clear.
5. Inspect the live `get_existing_tags` input schema. For the supported catalog shape, call it with no filter arguments, then filter the returned tags locally against the topic terms and candidate tags from discovery. Do not pass a topic filter unless the live schema explicitly declares one. Select a tag only when it is an exact semantic match for the topic. If several returned tags are plausible, show the alternatives and ask the user which tag they mean; do not call `recommend_SME` until they choose. If no returned tag is an exact semantic match, say that no matching existing tag was found and do not guess or create one.
6. Call `recommend_SME` only with the resolved existing tag ID, never a tag name. Report its candidates as recommendations associated with that tag; do not infer expertise from names, job titles, generic organizational assumptions, or unrelated activity.
7. If `recommend_SME` returns no candidates, say `No SME candidates were returned for tag <name> (ID: <id>).` Offer to refine the topic or choose another existing tag only with the user's direction.

## Response rules

- State the focused search query and label its results `Discovery:`. Include a title and content ID for every surfaced hit when available.
- For a successful search with no relevant discovery, state `No relevant sources were found.` and continue the clear-topic SME workflow; do not describe this absence as an MCP failure.
- State `Resolved tag:` with the exact tag name and ID before listing candidates.
- State `SME candidates:` only after `recommend_SME` succeeds. If it returns none, use the no-candidate wording from the workflow; do not substitute a guessed person.
- Keep discovery separate from a verified answer. This skill cannot retrieve full sources, so it must not claim that search snippets fully answer the user's need.
- Do not call `draft_question`, `create_question`, `create_QA`, `create_article`, `submit_user_answer`, `update_question`, `update_answer`, or `vote`.

## Failure handling

- If `search` is unavailable or fails, report the tool or access failure honestly and ask whether the user wants to retry, refine the topic, or continue without Stack Internal. Do not claim that internal content was searched successfully when the call failed.
- If `get_existing_tags` is unavailable or fails, report that tag resolution could not be completed and do not call `recommend_SME`.
- If tag choice is ambiguous, pause for clarification rather than selecting the closest-looking tag.
- If `recommend_SME` fails, report the failed recommendation step and do not claim that a person was recommended. If it succeeds with an empty result, report no candidates rather than an error or an inferred expert.
