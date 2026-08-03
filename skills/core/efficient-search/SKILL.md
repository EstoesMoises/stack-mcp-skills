---
name: efficient-search
description: Search Stack Internal efficiently for company-specific standards, policies, architecture, operations, onboarding, prior incidents, or other internal knowledge. Use when an answer may depend on organizational context, including indirect requests that do not explicitly mention Stack Internal. Do not use for generic questions with no plausible company-specific answer.
license: Apache-2.0
compatibility: Requires a connected Stack Internal MCP server and network access.
metadata:
  stack-internal-tier: core
  stack-internal-version: "0.1.0"
  stack-internal-write-actions: "none"
  stack-internal-adapters: "codex,claude-code,cursor,github-copilot"
---

# Efficient Stack Internal Search

Use this read-only workflow to find the smallest sufficient set of company sources. Require the `search`, `get_question`, and `get_article` capabilities; do not substitute a write action.

## Workflow

1. Classify the request before calling Stack Internal. Search only for high-signal company context: an internal standard, policy, service, architecture, deployment, onboarding process, incident, security or authentication practice, ambiguous implementation note, or undocumented local behavior. For a generic question with no plausible company-specific answer, continue without Stack Internal.
2. Extract distinctive evidence from the request: exact error text, internal component or service names, acronyms, tags, and the narrowest topic phrase. Form one concise focused query; do not paste the whole request.
3. Call `search` once with that query. Inspect each result's declared type and its title, tags, and IDs to select promising question, answer, or article hits. Treat every returned snippet as discovery data, never evidence.
4. Rank promising candidates strongest-first from their titles and tags. Retrieve a question with `get_question` or an article with `get_article` before relying on it. An answer hit is retrieved through its parent question: use only the parent question ID supplied by that result and call `get_question` with it. If an answer result has no parent question ID, do not guess an ID, cite the answer, or treat its snippet as evidence; report the full-retrieval limitation and continue within the same bounded search budget. Reassess after each full retrieval and fetch the next candidate only when evidence remains insufficient.
5. If the retrieved content is not relevant or search results are weak, broaden the query by removing incidental details or using one close internal synonym. Make at most two broadened searches, for a maximum of three `search` calls total. Stop as soon as sufficient relevant evidence is found; do not keep searching unless the user explicitly asks.
6. Respond with only supported conclusions. For every source used, give its title and ID, then state what its full content supports. Put any reasoning beyond the source under an explicit `Inference:` label. Do not represent a title, tag, or snippet as proof.

Load [the search-tool reference](references/search-tools.md) only when tool semantics, response fields, or safe query broadening need clarification.

## Response shape

Use this structure when Stack Internal produces relevant material:

```markdown
Evidence
- Source: <title> (ID: <id>)
  Supported conclusion: <what the retrieved full content establishes>

Inference: <reasoning that goes beyond the retrieved sources, or "None.">
```

If no retrieved source supports a requested conclusion, say that it is not established by Stack Internal rather than filling the gap with an implied company standard.

## Failure handling

- If Stack Internal or the MCP connection is unavailable, say it could not be accessed and ask whether to continue with general knowledge.
- If authentication or permission fails, report the access failure and do not try to bypass it.
- If full-content retrieval fails, label the source evidence incomplete; do not rely on its search result as evidence.
- If an answer hit omits its parent question ID, report that the answer could not be fully retrieved; do not guess or cite it.
- If all three searches produce no useful result, report the knowledge gap, state that no company guidance was found, and offer to use a knowledge-gap workflow. Do not create or update content automatically.
