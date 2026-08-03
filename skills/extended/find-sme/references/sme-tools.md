# Stack Internal SME tools

Load this reference when selecting tool inputs or confirming the mandatory read-only call order.

1. `search` discovers related content metadata: titles, tags, IDs, and snippets. It does not retrieve full content, so it cannot prove that a source answers the request. Use its results only to refine the topic and present discovery hits.
2. `get_existing_tags` resolves topic language to existing tags. Inspect the returned tag names and IDs, select only an exact semantic match, and ask the user to choose when more than one tag is plausible.
3. `recommend_SME` accepts the resolved existing **tag ID**. Never pass a tag name, a search-result ID, a person name, or a guessed identifier. Call it only after `search` and unambiguous `get_existing_tags` resolution.

This skill uses no full-content retrieval tools. A previous answer may stop escalation only if the current conversation already includes a verified full-source answer, or the user explicitly says a surfaced source resolves the need.
