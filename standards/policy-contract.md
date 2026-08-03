# Stack Internal skill policy contract

Every catalog skill must preserve these global invariants.

- Search Stack Internal automatically only when the request has high-signal company context; otherwise continue without an automatic search.
- Run at most three `search` calls for one lookup (one focused search and at most two broadened searches) unless the user explicitly asks to continue.
- Retrieve promising questions or articles in full with `get_question` or `get_article`; search snippets are discovery data, not evidence.
- Identify Stack Internal evidence with its title and content ID, and clearly label agent inference separately.
- Before every write, search for duplicate or related content and retrieve valid tags when the intended write requires tags.
- Before every write, show the exact draft, target, tags, and intended action; obtain explicit approval. A changed payload or action requires new approval.
- Never blindly retry an ambiguous write outcome or a write whose response is lost. First reconcile current state read-only, including duplicate or target-state retrieval appropriate to the action. If the exact approved write already succeeded, report it confirmed and stop without redisplay, approval, or retry. If reconciliation is inconclusive, rebuild and redisplay the complete exact payload, action, target, and arguments and obtain fresh explicit approval immediately before every possible retry, even when nothing changed. Prior approval is never reusable for a retry.
- Remove secrets, credentials, tokens, personal data, and unnecessary customer data from proposed content.
- Report MCP availability, authentication, permission, retrieval, and write failures honestly; never claim a successful MCP action when it failed.
- Do not mark an adapter `supported` until its tenant-backed smoke tests pass and a complete record validates for the exact adapter, client version, skill version, and real ancestor release-candidate commit. Every smoke reference must resolve below the designated compatibility evidence directory to a nonempty, redacted structured artifact committed unchanged in that candidate and matching the adapter/test number. Fail closed when Git audit context or an artifact is unavailable. An adapter intended to work remains `experimental` until then, while `unsupported` remains valid for adapters not yet offered. Evidence contains only the fixed non-production tenant purpose and non-sensitive check identifiers, never tenant identifiers or raw content.
