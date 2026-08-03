# Local Q&A payload template

Render this complete object locally before the approval gate. Fill it with sanitized, supported content; do not send it to Stack Internal while rendering.

```json
{
  "title": "Searchable question title",
  "question": "Problem: concise question that can stand alone",
  "answer": "Problem: verified problem\n\nResolution: direct fix and why it works",
  "tags": ["valid-tag"],
  "intended_action": {
    "tool": "create_QA",
    "args": {}
  }
}
```

For an existing target, add a `target_id` field and the exact target type in `intended_action.args` to that same object. Omit `target_id` for a new question or Q&A. For a vote, preserve the retrieved target's title, question, answer, and tags in the display payload, then use this exact action shape:

```json
{
  "intended_action": {
    "tool": "vote",
    "args": {
      "operation": "upvote",
      "target_type": "answer"
    }
  },
  "target_id": "retrieved-answer-id"
}
```

Set `operation` to the exact supported `upvote`, `downvote`, or `remove` operation selected by the user; do not choose a default or add an argument after approval. Do not use an operation the documented vote tool contract does not support.

Build `question` and `answer` from these sections:

- `Problem` — required; state the searchable problem and scope.
- `Context` — include only when environment, component, version, or constraint changes the answer.
- `Reproduction or symptoms` — include only when it helps recognize the issue.
- `Root cause` — include only when verified.
- `Resolution` — include when the fix or action is known.
- `Validation` — include only the check that actually confirmed the outcome.
- `Prevention` — include only an actionable recurring safeguard.

Omit every empty or unsupported optional section instead of leaving a heading, blank field, filler, or a generic conclusion. Never include credentials, tokens, personal data, unnecessary customer names, or unverified claims.
