# Local incident knowledge payload template

Use this template only after all material incident facts are verified, related sources have been fully retrieved as needed, valid tags have been returned, and the user has selected a format when necessary. Render it locally; rendering must not call `create_article` or `create_QA`.

`summary`, `impact`, each timeline entry, `root_cause`, `resolution`, `validation`, and each follow-up must be supported by incident evidence or a retrieved source. `unresolved_facts` must be empty for every material fact before the approval gate. Keep a non-material unknown visible rather than silently omitting it.

```json
{
  "format": "article or qa",
  "article_type": "Required only for an article: one value accepted by the connected create_article schema.",
  "title": "Searchable incident title",
  "question": "Required only for Q&A: the visible searchable operational question.",
  "draftReviewed": "Required only when the connected write schema declares it; display the exact Boolean before approval.",
  "body": "Required only for an article: complete rendered incident record.",
  "answer": "Required only for Q&A: complete rendered incident record.",
  "summary": "Objective one-paragraph description of what happened.",
  "impact": "Measured user, system, and duration impact.",
  "timeline": [
    {
      "timestamp": "2026-08-01T14:03:00Z",
      "event": "Observed event supported by the incident record."
    }
  ],
  "root_cause": "Verified causal mechanism; never a hypothesis.",
  "resolution": "Completed mitigation or permanent fix.",
  "validation": "The specific checks that confirmed recovery or the fix.",
  "follow_ups": [
    {
      "action": "Concrete prevention action.",
      "owner": "Team or role when verified",
      "status": "planned, completed, or otherwise verified"
    }
  ],
  "unresolved_facts": [],
  "related_sources": [
    {
      "title": "Retrieved Stack Internal source title",
      "id": "content-id",
      "establishes": "What its full content supports."
    }
  ],
  "tags": ["valid-returned-tag"],
  "target": "new article or new Q&A",
  "intended_action": {
    "tool": "create_article or create_QA",
    "args": {
      "exact_live_schema_parameter": "value visibly copied or derived from this displayed record"
    }
  }
}
```

For an article, render the title, summary, impact, chronological timeline, root cause, resolution, validation, follow-ups, unresolved-fact status, and related-source citations into the visible article body. For Q&A, render the visible `question` and an answer containing the same factual sections; copy both into the selected tool's exact live-schema arguments. The `args` object must use the complete current input schema for the selected tool, including its exact parameter names; the example key above is intentionally not portable. Every displayed action argument must be complete before approval, and after approval it is replayed byte-for-byte.

Omit only non-material empty optional details. Never pad the record with generic conclusions, hide open material facts, include secrets or personal data, or publish an incident with a speculative root cause.
