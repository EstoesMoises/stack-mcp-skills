# Stack Internal skill policy contract

Every catalog skill must preserve these global invariants.

- Search Stack Internal automatically only when the request has high-signal company context; otherwise continue without an automatic search.
- Run at most three `search` calls for one lookup (one focused search and at most two broadened searches) unless the user explicitly asks to continue.
- Retrieve promising questions or articles in full with `get_question` or `get_article`; search snippets are discovery data, not evidence.
- Identify Stack Internal evidence with its title and content ID, and clearly label agent inference separately.
- Before every write, search for duplicate or related content and retrieve valid tags when the intended write requires tags.
- Before every write, show the exact draft, target, tags, and intended action; obtain explicit approval. A changed payload or action requires new approval.
- Remove secrets, credentials, tokens, personal data, and unnecessary customer data from proposed content.
- Report MCP availability, authentication, permission, retrieval, and write failures honestly; never claim a successful MCP action when it failed.
