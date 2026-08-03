---
name: onboarding
description: Build a sourced onboarding path from Stack Internal for a company role, repository, service, or workflow. Use when someone needs to learn local setup, architecture, team conventions, deployment, ownership, or a first-task sequence. Do not use for generic career advice or public technology tutorials.
license: Apache-2.0
compatibility: Requires a connected Stack Internal MCP server and network access.
metadata:
  stack-internal-tier: extended
  stack-internal-version: "0.1.0"
  stack-internal-write-actions: "none"
  stack-internal-adapters: "codex,claude-code,cursor,github-copilot"
---

# Stack Internal Onboarding Paths

Build a role- and goal-specific path from retrieved company knowledge. Require only `search`, `get_question`, and `get_article`; this workflow is read-only.

## Workflow

1. Identify the audience, the concrete learning goal, and the available time horizon. Ask for the missing value when it would materially change the path; otherwise state the assumption.
2. Treat prerequisites, setup, architecture, workflows, and first tasks as the required major topics. Search each topic and retain all five sections in the final path. Report `Missing coverage:` for a topic only after its focused search and both permitted broadened searches have produced no relevant fully retrieved content.
3. For each major topic, extract narrow internal terms from the role, repository, service, workflow, team, and goal. Run one focused `search` using those terms. Treat titles, tags, IDs, and snippets only as discovery data.
4. Rank the candidates strongest-first. Retrieve the strongest full question with `get_question` or article with `get_article`, then reassess whether it supports an actionable item for that topic. Retrieve another candidate only if the retrieved content remains insufficient; do not fetch every result eagerly.
5. Broaden the topic query only when the focused result is weak or insufficient. Remove incidental detail or use one close internal synonym, then repeat full retrieval and reassessment. Make at most two broadened searches for that topic, for a maximum of three `search` calls per major topic, unless the user explicitly asks to continue. Stop as soon as the topic has sufficient evidence; otherwise exhaust the two broadened searches before recording missing coverage.
6. Track searches across the whole path. After eight `search` calls, before any further broadening, disclose the completed searches and remaining topics, then ask whether to continue the bounded searches. Do not make another broadening call without that explicit confirmation. This guard never raises the three-search cap for a topic.
7. Include an item only when retrieved full content supports it. Cite every included item with the source's exact title and content ID; state what that source establishes. Put any reasoning beyond a retrieved source under `Inference:` and do not turn it into a required step.
8. Render the path with [the learning-path template](assets/learning-path-template.md). Keep its five sections exactly: prerequisites, setup, architecture, workflows, and first tasks. Put `Missing coverage:` in the relevant section only after its bounded search is exhausted; do not fill a gap with generic setup, guessed ownership, or invented sequencing.

## Response rules

- Prefer a small, usable path over a source dump. Each listed item needs a retrieved source, its exact title, and its ID.
- Use `get_question` for a question result and `get_article` for an article result. A snippet, title, tag, or failed retrieval cannot support an item.
- Clearly distinguish the source-supported item from `Inference:`. If no inference is needed, write `Inference: None.`
- Do not call `draft_question`, `create_question`, `create_QA`, `create_article`, `submit_user_answer`, `update_question`, `update_answer`, or `vote`.

## Failure handling

- If Stack Internal, authentication, permission, or a required read tool is unavailable, report the failed step and ask whether to continue without company knowledge; do not claim a search or retrieval succeeded.
- If full retrieval fails, mark that candidate incomplete and do not use its search result as evidence.
- If a topic has no useful full source after its bounded searches, record `Missing coverage:` in that topic's section and say that Stack Internal did not establish a step.
- If the whole-path guard pauses research and the user does not confirm continuation, report the completed searches and remaining topics as incomplete research; do not render an unresolved topic as missing coverage.
- If sources conflict, cite each title and ID, describe the conflict, and avoid prescribing a single path until the user resolves it or stronger retrieved evidence exists.
