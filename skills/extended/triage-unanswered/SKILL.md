---
name: triage-unanswered
description: Triage Stack Internal questions without an accepted answer and draft evidence-based answers for review. Use when a user wants to find unanswered questions by topic or tag, reduce a knowledge backlog, or answer a specific internal question. Do not treat "no accepted answer" as "no answers" and never submit or vote without approval.
license: Apache-2.0
compatibility: Requires a connected Stack Internal MCP server and network access.
metadata:
  stack-internal-tier: extended
  stack-internal-version: "0.1.0"
  stack-internal-write-actions: "submit_user_answer,vote"
  stack-internal-adapters: "codex,claude-code,cursor,github-copilot"
---

# Triage Unanswered Stack Internal Questions

Prioritize questions with no accepted answer, then prepare only a supported answer draft. Require `get_questions_to_answer`, `get_question`, and `search`. `submit_user_answer` and `vote` are writes and are permitted only after approval of an exact displayed action.

## Workflow

1. Activate for a Stack Internal backlog by topic or tag, a request to investigate a question without an accepted answer, or a request to prepare an answer for a named internal question. Do not use this workflow to create a question, browse public Stack Overflow, review generic code, or replace an already accepted answer.
2. Call `get_questions_to_answer` with the requested topic or tag scope. Disclose that its results may already contain unaccepted answers: no accepted answer is an acceptance status, not proof that the question has no answers, no useful partial guidance, or no prior work. List candidates with title, ID, tags, and any available status only as a triage queue; do not cite the listing as technical evidence.
3. Prioritize transparently, without assuming an empty question: first topic relevance to the requested scope, then evidence readiness (a question that can be checked against fully retrieved internal guidance), then operational impact (blocked work, safety, customer, or reliability consequences). State those three factors and any uncertainty. If the user has selected a question, retain that selection while reporting where it falls in the priority order.
4. Fetch the chosen question in full with `get_question` before drafting, voting, or treating its status as current. Inspect its title, body, tags, accepted-answer status, and every returned answer. If it now has an accepted answer, report its title and ID and stop. If it has an unaccepted answer, identify it by answer ID and assess it against retrieved evidence; do not add a duplicate answer or vote automatically. A full retrieval authorizes assessment, not reproduction of raw answer text in a vote approval.
5. Build one focused related `search` query from the target's internal component, question, and distinctive terms. Search snippets are discovery data, not evidence. For every promising related question, call `get_question` and use only its fully retrieved question and answers as Stack Internal evidence. This catalog does not declare `get_article`: Never treat an article or search snippet as evidence. If a search result is an article, say it could not be fully retrieved through this skill and exclude it from the draft.
6. If the first fully retrieved related questions do not provide enough evidence, make at most two broadened searches, each followed by full `get_question` retrieval of promising questions. Use one focused search and at most two broadened searches; do not make a fourth search unless the user explicitly asks to continue. Cite every used source by exact title and content ID, and label reasoning not established by a source as `Inference:`.
7. Draft an answer only when the retrieved target and fully retrieved related questions directly support it. Before rendering, inspect every selected question, answer, source, and proposed response for secrets, credentials, tokens, personal data, customer data, and unnecessary operational detail. Never redisplay or resend a sensitive raw value in the evidence, approval-ready payload, or write arguments; record only a safe `sensitive_data_removed` description. For a vote, never redisplay the full raw retrieved answer: show only the question title and ID, answer ID, a safe concise summary or evidence-based reason when safe, the exact direction and action, and complete tool arguments. If no safe summary is possible, omit answer content and show only the IDs/title plus a neutral redaction notice. Make an answer draft direct and scoped to the target question, and include source titles and IDs. Do not turn an unaccepted answer, a snippet, a title, model memory, or an unsupported guess into a conclusion. If evidence is insufficient, contradictory, unavailable, or cannot be retrieved in full, explain the gap and escalate to the relevant owner or subject-matter expert; do not render an answer payload or call a write action.
8. Before rendering a write, inspect the connected MCP tool's current input schema. For the connected schema represented in this workflow, `submit_user_answer` uses `questionId` (number) and `answer` (string); construct those complete arguments from the visible target question ID and exact visible `answer`. The represented `vote` schema uses `questionId` (number), optional `answerId` (number), `isUpvote` (Boolean), and `action` (`add` or `remove`); construct every applicable argument from the fully retrieved target and user-selected operation. Runtime schema inspection still controls every live call. Never guess parameter names, omit visible required fields, or infer a vote direction. A vote is only eligible when the user has specifically requested the displayed supported operation after the target and evidence were reviewed; an unaccepted answer never authorizes a vote by itself.
9. Render one of these complete local payloads and stop. Every action argument must visibly copy or derive from this payload:

```markdown
Question triage
- Target: <retrieved question title> (question ID: <question-id>)
- Accepted-answer status: <none or retrieved answer ID>
- Existing unaccepted answers: <answer IDs and concise retrieved assessment, or None.>
- Priority rationale:
  - Topic relevance: <reason>
  - Evidence readiness: <reason>
  - Impact: <reason>

Evidence
- <related question title> (ID: <content-id>): <fact established by full retrieval>
- Inference: <reasoning beyond the sources, or None.>

Proposed answer
target:
  question_id: <retrieved question ID>
target_id: <retrieved question ID>
answer: <exact sanitized answer>
sources:
  - title: <related question title>
    id: <content ID>
    establishes: <supported fact>
sensitive_data_removed:
  - <safe description of each omitted sensitive value; omit only when none was present>
intended_action:
  tool: submit_user_answer
  args: <complete live-schema argument object>
```

```markdown
Question triage
- Target: <retrieved question title> (question ID: <question-id>; answer ID: <answer-id>)
- Existing unaccepted answer: <safe concise summary or evidence-based reason; omit content when no safe summary is possible>
- Redaction notice: <neutral notice when content is omitted or redacted; omit only when no sensitive content was present>
- Evidence: <fully retrieved supporting source title and ID>

Proposed vote
target:
  question_id: <retrieved question ID>
  answer_id: <retrieved answer ID>
target_id: <retrieved answer ID>
existing_unaccepted_answer_summary: <safe concise summary; omit when no safe summary is possible>
sources:
  - title: <related question title>
    id: <content ID>
    establishes: <supported fact>
sensitive_data_removed:
  - <neutral safe redaction description; omit only when none was present>
vote:
  isUpvote: <true for upvote; false for downvote>
  action: <add or remove>
intended_action:
  tool: vote
  args: <complete live-schema object including question ID, optional answer ID, Boolean direction, and exact user-selected add-or-remove action>
```

Show the target, every source, the complete payload, selected tool, and every argument. For a vote, show only safe metadata needed for informed approval; do not display the full raw retrieved answer. Do this locally: Before explicit approval, do not call any write action.

## Approval gate

Stop after displaying the exact local payload. Do not call `submit_user_answer` or `vote` until the user explicitly approves the displayed evidence, target, selected action, and every exact argument. A vote additionally requires approval of its exact Boolean direction, add-or-remove action, and target type.

Approval covers only the unchanged displayed client payload, target IDs, sources, sensitive-data removals, action, arguments, and vote operation. Any material content, evidence, source interpretation, target, action, schema mapping, argument, target type, vote direction, add-or-remove action, or sensitive-data removal change requires redisplaying the complete payload and obtaining new approval. After approval, call only the selected tool with `intended_action.args` byte-for-byte. Never add defaults, transform content, infer an argument, substitute a target, or switch an answer submission into a vote after approval.

## Confirmed result

Report only the confirmed result and returned answer ID when available. Never claim success without server confirmation. If the server confirms a vote without returning an ID, report the confirmed vote result and that no ID was returned.

## Failure handling

- If Stack Internal, MCP connectivity, authentication, permission, `get_questions_to_answer`, search, retrieval, schema access, or the selected write tool fails, state the failed step honestly. Do not claim a queue, source, answer, or vote was confirmed.
- If the chosen question cannot be retrieved in full, do not rely on its listing, draft an answer, render a vote, or write.
- If a related question cannot be retrieved in full, treat it as unavailable discovery data rather than evidence. Continue only within the bounded search policy; otherwise escalate without an answer draft.
- If the chosen question has an existing accepted answer, identify the retrieved target and stop. If it has an unaccepted answer, report it accurately and do not duplicate, replace, submit, or vote on it without the separate evidence and approval gates.
- If evidence is insufficient or conflicts, state what source or owner is needed. Do not render an approval-ready payload and do not write.
- If sensitive data is found, omit its raw value from every evidence rendering, approval-ready payload, and write argument. If safe sanitization makes the answer ambiguous, stop for user resolution rather than exposing, preserving, or guessing the value.
- If a vote target's answer has no safe concise summary, retain the retrieved question title and IDs, answer ID, evidence-based reason when available, exact `isUpvote` and `action`, and complete arguments. Add a neutral redaction notice; do not display, preserve, or send answer text because vote arguments never require it.
- If the live input schema is unavailable, ambiguous, or cannot be mapped completely from the visible payload, stop before approval; do not guess arguments, vote direction, or add-or-remove action.
- If an approved submission or vote fails or lacks confirmation, preserve the approved payload and report that no result was confirmed. Require explicit approval again after any retry-relevant change.
