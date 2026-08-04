# Stack Internal search tools

Use this reference only to resolve tool semantics or choose a bounded broader query.

## Read-only tools

- `search`: Discover candidate questions and articles from a focused query. Use titles, tags, IDs, and any snippets only to decide what to retrieve next.
- `get_question`: Retrieve the complete content for a selected question by its ID.
- `get_article`: Retrieve the complete content for a selected article by its ID.

Search results are discovery data, not evidence. Cite and summarize a source only after `get_question` or `get_article` returns its full content. If retrieval fails, say that the evidence is incomplete.

## Bounded query broadening

Start with the most distinctive exact error, internal service name, tag, or policy phrase. If it is weak or produces no relevant retrieved content, remove an incidental version, host, request ID, or environment detail. If needed, make one final search with a close internal synonym or the component plus its responsibility. Stop after the focused search and at most two broadened searches unless the user explicitly requests further searching.
