# Local Q&A payload template

Render this complete object locally before the approval gate. First inspect the selected connected MCP tool's current input schema; fill `intended_action.args` with its complete required argument object. The parameter keys below are an example from a simulated inspected schema, not portable names to guess or reuse. Fill the payload with sanitized, supported content; do not send it to Stack Internal while rendering.

```json
{
  "title": "Searchable question title",
  "question": "Problem: concise question that can stand alone",
  "answer": "Problem: verified problem\n\nResolution: direct fix and why it works",
  "tags": ["valid-tag"],
  "intended_action": {
    "tool": "create_QA",
    "args": {
      "title": "Searchable question title",
      "question": "Problem: concise question that can stand alone",
      "answer": "Problem: verified problem\n\nResolution: direct fix and why it works",
      "tags": ["valid-tag"]
    }
  }
}
```

For an existing target, add a `target_id` field and copy it into whichever exact input key the live schema requires. Omit `target_id` for a new question or Q&A. The action arguments must visibly copy or derive every content, target, and tag value from this payload. For a vote, preserve the retrieved target's title, question, answer, and tags in the display payload, then use this simulated-schema shape:

```json
{
  "intended_action": {
    "tool": "vote",
    "args": {
      "content_id": "retrieved-answer-id",
      "content_type": "answer",
      "operation": "upvote"
    }
  },
  "target_id": "retrieved-answer-id"
}
```

Set `operation` to the exact supported `upvote`, `downvote`, or `remove` operation selected by the user; do not choose a default or add an argument after approval. Actual parameter names and permitted operations come only from the current live tool schema. If it is unavailable or ambiguous, stop without writing. After approval, call the selected tool with the displayed `intended_action.args` byte-for-byte.

Build `question` and `answer` from these sections:

- `Problem` — required; state the searchable problem and scope.
- `Context` — include only when environment, component, version, or constraint changes the answer.
- `Reproduction or symptoms` — include only when it helps recognize the issue.
- `Root cause` — include only when verified.
- `Resolution` — include when the fix or action is known.
- `Validation` — include only the check that actually confirmed the outcome.
- `Prevention` — include only an actionable recurring safeguard.

Omit every empty or unsupported optional section instead of leaving a heading, blank field, filler, or a generic conclusion. Never include credentials, tokens, personal data, unnecessary customer names, or unverified claims.
