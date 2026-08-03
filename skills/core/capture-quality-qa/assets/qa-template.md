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

For an existing target, add structured `target` data with `question_id`, optional `answer_id`, and `content_type`, plus `target_id` for display compatibility. The action arguments must visibly copy or derive every content, target, and tag value from this payload. For a vote, never copy raw retrieved answer text into the display; retain only the question title, IDs, and safe concise context or a neutral redaction notice. The current modeled simulated-schema shape is:

```json
{
  "title": "Retrieved question title",
  "target": {"question_id": 512, "answer_id": 1512, "content_type": "answer"},
  "target_id": 1512,
  "sanitized_context": "Neutral evidence-based reason for the selected vote.",
  "vote": {"isUpvote": true, "action": "add"},
  "intended_action": {
    "tool": "vote",
    "args": {
      "questionId": 512,
      "answerId": 1512,
      "isUpvote": true,
      "action": "add"
    }
  }
}
```

Set `isUpvote` and `action` to the exact supported direction and `add` or `remove` operation selected by the user; do not choose a default or add an argument after approval. Actual parameter names and permitted operations come only from the current live tool schema. If it is unavailable or ambiguous, stop without writing. After approval, call the selected tool with the displayed `intended_action.args` byte-for-byte.

Build `question` and `answer` from these sections:

- `Problem` — required; state the searchable problem and scope.
- `Context` — include only when environment, component, version, or constraint changes the answer.
- `Reproduction or symptoms` — include only when it helps recognize the issue.
- `Root cause` — include only when verified.
- `Resolution` — include when the fix or action is known.
- `Validation` — include only the check that actually confirmed the outcome.
- `Prevention` — include only an actionable recurring safeguard.

Omit every empty or unsupported optional section instead of leaving a heading, blank field, filler, or a generic conclusion. Never include credentials, tokens, personal data, unnecessary customer names, or unverified claims.
