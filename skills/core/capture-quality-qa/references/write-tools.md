# Stack Internal Q&A tool map

Load this reference when selecting an action, identifying its target, or deciding whether tags and confirmation are required.

Before any write, inspect the selected connected MCP tool's current input schema. Its parameter names are the only authoritative names; the semantic mappings below describe values, not portable request keys. Render the complete schema-required `intended_action.args` object before approval, visibly copying or deriving each value from the top-level payload. If the schema is unavailable, ambiguous, or cannot be mapped completely, stop without writing. After approval, pass those exact args byte-for-byte.

| Tool | Kind | Prerequisite | Confirmation rule |
| --- | --- | --- | --- |
| `search` | Read | A resolved or reusable internal learning and one focused duplicate query. | No confirmation; use results only to discover candidates. |
| `get_question` | Read | A promising question ID from search or a user-specified target. | No confirmation; retrieve full content before relying on it or targeting it. |
| `get_article` | Read | A promising article ID from search or a user-specified target. | No confirmation; retrieve full content before relying on it as duplicate evidence. |
| `get_existing_tags` | Read | A selected prospective action that requires tags. | No confirmation; use only returned tags in the local payload. |
| `draft_question` | Write | Duplicate review, required tag lookup, sanitization, and a rendered exact local payload. | Explicit approval of that payload, action, and target (if any) is required first. |
| `create_question` | Write | Duplicate review shows no suitable existing target; required tag lookup, sanitization, and a rendered exact local payload. | Explicit approval of that payload and action is required first. |
| `create_QA` | Write | Duplicate review shows no suitable existing target; required tag lookup, sanitization, and a rendered exact local payload. | Explicit approval of that payload and action is required first. |
| `submit_user_answer` | Write | Retrieve the target question, review duplicates, obtain required tags if applicable, sanitize, and render the payload with `target_id`. | Explicit approval of the unchanged payload, `submit_user_answer`, and target is required first. |
| `update_question` | Write | Retrieve the target question, confirm that an update is better than a duplicate, obtain required tags, sanitize, and render the payload with `target_id`. | Explicit approval of the unchanged payload, `update_question`, and target is required first. |
| `update_answer` | Write | Retrieve the target question or answer context, confirm the answer is the proper target, sanitize, and render the payload with `target_id`. | Explicit approval of the unchanged payload, `update_answer`, and target is required first. |
| `vote` | Write | Retrieve the question and optional answer target; confirm the exact Boolean direction and supported `add` or `remove` action. Render structured IDs and those values without raw answer text. | Explicit approval of the unchanged action, exact arguments, and target is required first; a vote is never automatic and no argument may be invented afterward. |

## Write argument semantics

- `draft_question`: map the visible title, question body, and valid tags.
- `create_question`: map the visible title, body, and valid tags.
- `create_QA`: map the visible title, question, answer, and valid tags.
- `submit_user_answer`: map the retrieved question ID and visible answer.
- `update_question`: map the retrieved question ID and the exact changed title, body, and tags.
- `update_answer`: map the retrieved question ID, answer ID, and exact changed answer body. The current modeled schema is `questionId`, `answerId`, and `newBodyContent`; inspect runtime schema before calling.
- `vote`: map the retrieved question ID, optional answer ID, exact Boolean direction, and exact user-selected `add` or `remove` action. The current modeled schema is `questionId`, optional `answerId`, `isUpvote`, and `action`; inspect runtime schema before calling. Never include raw retrieved answer text in a vote display or call.

For every write, server-added provenance is acceptable only when it leaves the approved client payload unchanged and visible. Any client-field, target, tag, or action change requires a new rendered payload and confirmation.
