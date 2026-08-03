---
name: review-stale-content
description: Review Stack Internal questions and answers for potentially stale company guidance and propose evidence-based updates. Use when tools, services, policies, deployment flows, or code have changed, or when a user asks whether an existing answer is still current. Do not mark content stale from age alone.
license: Apache-2.0
compatibility: Requires a connected Stack Internal MCP server and network access.
metadata:
  stack-internal-tier: extended
  stack-internal-version: "0.1.0"
  stack-internal-write-actions: "update_question,update_answer"
  stack-internal-adapters: "codex,claude-code,cursor,github-copilot"
---

# Review Stale Stack Internal Content

Review a specific internal question or answer against current, independently verified evidence. Require `search`, `get_question`, `get_article`, and `get_comments`. `update_question` and `update_answer` are writes and are permitted only after approval of an exact displayed edit.

## Workflow

1. Activate only for a request to review possible outdated company guidance, a known migration, a deprecation, a changed policy or deployment flow, or a direct currentness question. Do not use this workflow for grammar cleanup, low votes, timestamps, style preferences, or a request to create new content.
2. Start with one focused `search` for the target system and asserted change. Treat titles, tags, scores, dates, and snippets as discovery data only. Retrieve every promising target in full with `get_question` or `get_article`; make at most two broadened searches if full retrieval leaves the target or related guidance unclear. Do not make a fourth search unless the user explicitly asks to continue.
3. Fetch the complete available discussion before classifying a question or an answer. For a question, call `get_question` and call `get_comments` for the question and for each answer under consideration. For an article, inspect the actual `get_article` response and use comments or feedback only when that response supplies them. If article feedback is absent, explicitly mark that review dimension incomplete; do not manufacture comments or call `get_comments` for an article unless the inspected live schema explicitly supports article comments. Articles are review-only because no article update tool is declared. Do not use a search snippet, unseen answer, or unseen comment as evidence.
4. Gather current comparison evidence from either current code that has been inspected and verified in scope, or an independently verified company practice such as an authoritative, current internal policy, deployment record, or service-owner confirmation. Record the exact source, observed fact, and verification basis. Do not treat model memory, an unverified assertion, a title, an age, a score, or a style difference as current practice.
5. Compare the full target and comments with the current evidence. Cite every Stack Internal source by exact title and content ID, and label any reasoning beyond the sources as `Inference:`. Load [the staleness-signals reference](references/staleness-signals.md) when weighing evidence or deciding a classification.
6. Classify the review exactly once:
   - `confirmed-divergence`: reliable current evidence directly contradicts a material statement in the retrieved target, such as a removed configuration, a verified migration, or an explicit deprecation.
   - `possible-divergence`: the evidence suggests a mismatch but lacks a direct, verified comparison, is incomplete, or needs an owner to interpret it. Do not propose or execute an update.
   - `still-current`: the fully retrieved target remains consistent with current verified code or practice. Do not propose or execute an update.
   Age, score, style, or a weak signal alone never proves stale content. If authoritative sources conflict, report each source and its ID, classify `possible-divergence`, and require human resolution; do not write.
7. For `confirmed-divergence`, choose the narrowest retrieved target. For `update_answer`, the target is the retrieved answer ID, never the parent question ID; retain the parent question ID as required context. For `update_question`, the target is the retrieved question ID. Edit only material text directly contradicted by current evidence. Preserve an unchanged title, body, or tags exactly as fully retrieved; never invent tags or change an unverified non-sensitive field. If an existing field required by the live update schema was not retrieved in full, stop without an edit.
8. Before rendering any update, inspect every retrieved target field, relevant comment, and proposed replacement for secrets, credentials, tokens, personal data, customer data, and unnecessary sensitive operational detail. Never redisplay or resend sensitive data in the evidence comparison, proposed update, or action arguments. Do not preserve a sensitive field unchanged. When safely removing sensitive data expands the edit beyond the stale statement, show a safe description of each removal in `sensitive_data_removed` and include the sanitized replacement in the exact visible payload for approval. If a safe removal would make the intended guidance ambiguous, stop and ask the user for resolution rather than guessing or exposing the value.
9. Before rendering, inspect the connected MCP tool's current input schema for the selected update action. Construct `intended_action.args` as the complete argument object with the live schema's exact keys, types, and values. With the currently connected schemas, `update_question` requires `questionId`, `newTitle`, `newBodyContent`, and `newTags`; `update_answer` requires `questionId`, `answerId`, and `newBodyContent`. If the live schema is unavailable, ambiguous, differs in a way that cannot be mapped completely, or requires an unverified value, stop without writing.
10. Render this exact local payload and stop. It must make the comparison and every changed or preserved field visible without exposing sensitive source material:

```markdown
Evidence comparison
- Target: <exact target title> (question ID: <question-id>; answer ID: <answer-id when updating an answer>)
- Retrieved content says: <material existing statement>
- Retrieved comments say: <relevant comment facts, with IDs>
- Current verified evidence: <source, observed fact, and verification basis>
- Classification: confirmed-divergence
- Inference: <reasoning beyond the sources, or None.>

Proposed update
target:
  question_id: <retrieved question ID>
  answer_id: <retrieved answer ID when updating an answer>
target_id: <question ID for update_question; answer ID for update_answer>
proposed_title: <exact replacement title, or retrieved title when unchanged>
proposed_body: <exact replacement question body, or retrieved body when unchanged>
proposed_tags: [<exact retrieved tags when update_question requires them>]
proposed_answer: <exact replacement answer body when updating an answer>
sensitive_data_removed:
  - <safe description of each removed sensitive value; omit only when none was present>
intended_action:
  tool: <update_question or update_answer>
  args: <complete live-schema argument object copied from this payload>
```

Show the complete target, tool, action, and every argument. Do this locally: before explicit approval, do not call `draft_question`, `create_question`, `create_QA`, `create_article`, `submit_user_answer`, `update_question`, `update_answer`, or `vote`.

## Approval gate

Stop after displaying the exact evidence comparison and proposed update. Do not call `update_question` or `update_answer` until the user explicitly approves the displayed classification, evidence comparison, target, selected action, and every exact argument.

Approval covers only the unchanged client payload, target IDs, action, arguments, and each visible sensitive-data removal. Any material edit, source interpretation, classification, target, action, schema mapping, argument, or sensitive-data removal change requires redisplaying the complete payload and obtaining approval again; a changed payload requires new approval. After approval, replay `intended_action.args` byte-for-byte with the approved update tool. Never add defaults, transform content, infer a field, substitute a target, or switch actions after approval.

## Confirmed result

Report only the confirmed result and returned updated content ID when available. Never claim success without server confirmation. If the server does not return an ID, say that explicitly rather than inventing one.

## Failure handling

- If Stack Internal, MCP connectivity, authentication, permission, search, retrieval, or comments access fails, state the failed step honestly. Do not claim the target was fully reviewed, do not classify it as stale or current, and do not write.
- If current code or practice cannot be independently verified, classify only `possible-divergence` when a concern remains. Explain the missing evidence and ask for a verified source or owner; do not draft an update.
- If the content is still current, report the evidence comparison and `still-current` classification. Do not make a cosmetic edit.
- If an article has confirmed divergence, report the evidence comparison and that no article update tool is declared. Do not render an approval-ready update or use a different write tool.
- If sources conflict, show the conflict and all source IDs, request human resolution, and do not render an approval-ready payload or write.
- If sensitive data is found, omit its raw value from every displayed or sent field. Show only the safe removal description and sanitized exact replacement. If safe sanitization would leave ambiguous guidance, stop for user resolution; do not preserve, redisplay, or resend the sensitive field.
- If the selected update schema cannot be fully represented from retrieved and verified fields, stop before the approval gate; do not guess a parameter name, tag, or replacement value.
- If a write fails, its outcome is ambiguous, or its response is lost, never blindly retry or reuse prior approval. First reconcile current state read-only with duplicate search and full target/current-answer retrieval (and available question comments). If the exact approved write already succeeded, report the confirmed result and stop without redisplay, approval, or retry. If reconciliation is inconclusive and a retry remains necessary, rebuild and redisplay the complete exact evidence, payload, target, action, and arguments, then obtain fresh explicit approval immediately before the call even when nothing changed.
