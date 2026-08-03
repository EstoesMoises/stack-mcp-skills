# Stack Internal Q&A tool map

Load this reference when selecting an action, identifying its target, or deciding whether tags and confirmation are required.

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
| `vote` | Write | Retrieve the target and confirm that the vote expresses the user's intended judgment. | Explicit approval of the unchanged action and target is required first; a vote is never automatic. |

For every write, server-added provenance is acceptable only when it leaves the approved client payload unchanged and visible. Any client-field, target, tag, or action change requires a new rendered payload and confirmation.
