# Stack Internal MCP Skills Catalog Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a validated, Git-distributed catalog of nine portable Agent Skills that teach coding agents to use the Stack Internal MCP server conditionally, efficiently, and safely.

**Architecture:** Each published workflow is a self-contained Agent Skills directory with `SKILL.md`, local evals, and only the references or assets it needs. A small Python validation package checks the Agent Skills format, catalog metadata, resource boundaries, eval coverage, and write-approval invariants; native adapter guides explain installation in Codex, Claude Code, Cursor, and GitHub Copilot.

**Tech Stack:** Markdown and YAML frontmatter, JSON and JSON Schema 2020-12, Python 3.11+, pytest 8.x, PyYAML 6.x, jsonschema 4.x, and `skills-ref` pinned to commit `38a2ff82958afee88dadf4831509e6f7e9d8ef4e`.

## Global Constraints

- Every published skill is independently installable and conforms to the Agent Skills specification.
- `SKILL.md` frontmatter requires `name` and `description`; `name` matches its parent directory, uses lowercase letters/numbers/single hyphens, and is at most 64 characters; `description` is non-empty, states what and when, and is at most 1024 characters.
- Use `license: Apache-2.0`; put project-specific values under string-only `metadata` keys prefixed with `stack-internal-`; omit experimental `allowed-tools`.
- Keep each `SKILL.md` below 500 lines and 20,000 characters, a conservative automated proxy for the recommended 5,000-token limit.
- Keep every skill self-contained. Resource paths are relative to the skill root, one reference hop deep, and never use `..`.
- Create `references/`, `scripts/`, or `assets/` only when populated and explicitly referenced from `SKILL.md` with instructions describing when to load or run them.
- Search automatically only for high-signal company context. Use at most three `search` calls per lookup unless the user explicitly asks to continue.
- Fetch promising full content with `get_question` or `get_article`; never treat a truncated search snippet as sufficient evidence.
- Identify Stack Internal evidence by title and content ID, and label agent inference separately.
- Treat `draft_question`, creation, answer submission, updates, and votes as writes. Search duplicates, retrieve valid tags when required, show the exact payload and target, and obtain explicit approval before the MCP call. A changed payload requires new approval.
- Do not include secrets, credentials, tokens, personal data, or unnecessary customer data in proposed content.
- Automated tests use simulated MCP responses only and never connect to a customer tenant.
- Set every adapter compatibility value to `experimental` during Tasks 2-12. Promote an adapter to `supported` only after its Task 13 tenant-backed smoke tests pass.
- All catalog and skill validation must pass before each task commit.

---

## File Map

### Validation and governance

- `pyproject.toml` — Python version, pinned development dependencies, and pytest configuration.
- `LICENSE` — Apache-2.0 repository license referenced by skills.
- `standards/catalog-schema.json` — JSON Schema for `catalog/skills.json`.
- `standards/policy-contract.md` — maintainer-facing list of cross-skill safety invariants.
- `src/stack_skill_catalog/__init__.py` — package marker and public `validate_repository` export.
- `src/stack_skill_catalog/catalog.py` — load and validate catalog structure and entry/path consistency.
- `src/stack_skill_catalog/skill.py` — parse frontmatter, invoke `skills-ref`, validate resources/evals/policies.
- `src/stack_skill_catalog/validation.py` — aggregate deterministic repository validation errors.
- `scripts/validate_catalog.py` — non-interactive CLI wrapper with JSON output and meaningful exit codes.
- `tests/contract/` — unit and integration tests for schema, Agent Skills format, resources, evals, and policy gates.

### Catalog content

- `catalog/skills.json` — discovery index for all nine skills.
- `skills/core/efficient-search/` — efficient Stack Internal search workflow.
- `skills/core/company-debugging/` — company-grounded debugging workflow.
- `skills/core/capture-quality-qa/` — reusable Q&A capture workflow.
- `skills/extended/onboarding/` — sourced onboarding learning paths.
- `skills/extended/find-sme/` — tag resolution and SME recommendation.
- `skills/extended/incident-to-knowledge/` — incident-to-Q&A/article capture.
- `skills/extended/fill-knowledge-gap/` — question drafting after exhausted search.
- `skills/extended/review-stale-content/` — stale-guidance detection and update proposal.
- `skills/extended/triage-unanswered/` — unanswered-question evidence and answer drafting.

### Distribution

- `adapters/README.md` — compatibility matrix and common prerequisites.
- `adapters/{codex,claude-code,cursor,github-copilot}/README.md` — verified native installation and smoke tests.
- `README.md` — catalog landing page and ten-minute quickstart.
- `CONTRIBUTING.md` — contribution, eval, and review requirements.
- `docs/release-checklist.md` — automated and tenant-backed manual release gates.
- `.github/workflows/validate.yml` — CI validation on pushes and pull requests.

---

### Task 1: Build the validation foundation

**Files:**
- Create: `pyproject.toml`
- Create: `LICENSE`
- Create: `standards/catalog-schema.json`
- Create: `standards/policy-contract.md`
- Create: `catalog/skills.json`
- Create: `src/stack_skill_catalog/__init__.py`
- Create: `src/stack_skill_catalog/catalog.py`
- Create: `src/stack_skill_catalog/skill.py`
- Create: `src/stack_skill_catalog/validation.py`
- Create: `scripts/validate_catalog.py`
- Create: `tests/contract/conftest.py`
- Create: `tests/contract/test_catalog.py`
- Create: `tests/contract/test_skill_contract.py`
- Create: `tests/contract/test_validation_cli.py`

**Interfaces:**
- Produces: `validate_repository(root: pathlib.Path) -> list[str]`, returning stable human-readable errors and an empty list on success.
- Produces: CLI `python scripts/validate_catalog.py [ROOT]`, writing an object with Boolean `valid` and string-array `errors` fields to stdout and exiting `0` or `1`.
- Produces: initial catalog object `{ "catalog_version": "1.0.0", "skills": [] }` validated by `standards/catalog-schema.json`.

- [ ] **Step 1: Write failing contract tests**

Create tests that build temporary skill/catalog fixtures and assert these exact cases:

```python
def test_valid_empty_catalog_passes(repo_fixture):
    assert validate_repository(repo_fixture.root) == []

def test_name_must_match_parent(repo_fixture):
    repo_fixture.add_skill(path="skills/core/right-name", name="wrong-name")
    assert "name must match parent directory: right-name" in validate_repository(repo_fixture.root)

def test_write_skill_requires_approval_gate(repo_fixture):
    repo_fixture.add_skill(write_actions="create_QA", body="# Skill\n\n## Workflow\nDraft content.")
    assert "write-capable skill must contain ## Approval gate" in validate_repository(repo_fixture.root)

def test_cli_emits_json_and_nonzero_for_errors(tmp_path, capsys):
    exit_code = main([str(tmp_path)])
    assert exit_code == 1
    assert json.loads(capsys.readouterr().out)["valid"] is False
```

The fixture's valid `SKILL.md` must include compliant frontmatter, `## Workflow`, `## Failure handling`, `evals/evals.json` with two cases, and `evals/trigger-evals.json` with the tier's minimum positive and negative cases.

- [ ] **Step 2: Run the tests and confirm the expected failure**

Run: `python -m pytest tests/contract -q`

Expected: collection fails because `stack_skill_catalog` does not exist.

- [ ] **Step 3: Add project configuration and pinned dependencies**

Create `pyproject.toml` with Python `>=3.11`, package source under `src`, and this development group:

```toml
[dependency-groups]
dev = [
  "jsonschema>=4.23,<5",
  "pytest>=8,<9",
  "PyYAML>=6,<7",
  "skills-ref @ git+https://github.com/agentskills/agentskills.git@38a2ff82958afee88dadf4831509e6f7e9d8ef4e#subdirectory=skills-ref",
]
```

Configure pytest with `pythonpath = ["src"]` and `testpaths = ["tests"]`. Add the complete Apache-2.0 text to `LICENSE`. Run `uv sync --dev` to create `uv.lock`.

- [ ] **Step 4: Define the catalog schema and policy contract**

The schema must require:

```json
{
  "catalog_version": "1.0.0",
  "skills": [{
    "id": "efficient-search",
    "name": "Efficient Stack Internal Search",
    "version": "0.1.0",
    "tier": "core",
    "summary": "One-line discovery summary.",
    "path": "skills/core/efficient-search",
    "tags": ["search"],
    "required_tools": ["search", "get_question", "get_article"],
    "write_actions": [],
    "adapters": {
      "codex": "supported",
      "claude-code": "supported",
      "cursor": "supported",
      "github-copilot": "supported"
    }
  }]
}
```

Enumerate tiers `core|extended`, adapter states `supported|experimental|unsupported`, all documented MCP tools, and write actions including `draft_question`. Set `additionalProperties: false` at every object level. Initialize the real catalog with version `1.0.0` and an empty `skills` array.

Write `standards/policy-contract.md` with the exact global invariants from this plan: conditional search, three-call bound, full retrieval, evidence labeling, duplicate/tag checks, exact-draft approval for every write, sensitive-data removal, and honest MCP failure reporting.

- [ ] **Step 5: Implement the minimal validator**

Implement these exact public interfaces:

```text
catalog.load_catalog(path: Path) -> dict[str, object]
catalog.validate_catalog(root: Path, catalog: dict[str, object]) -> list[str]
skill.discover_skill_dirs(root: Path) -> list[Path]
skill.load_frontmatter(skill_dir: Path) -> tuple[dict[str, object], str]
skill.validate_skill(root: Path, skill_dir: Path, catalog_entry: dict[str, object]) -> list[str]
validation.validate_repository(root: Path) -> list[str]
```

`validate_skill` must call `skills_ref.validate`, enforce metadata/catalog equality, line and character limits, required sections, exact approval heading for non-empty write actions, non-empty optional directories, local one-hop resource links, eval JSON structure/counts, forbidden placeholder markers, and no `allowed-tools` field. Sort paths and errors for deterministic output.

- [ ] **Step 6: Run contract and CLI tests**

Run: `uv run pytest tests/contract -q`

Expected: all tests pass.

Run: `uv run python scripts/validate_catalog.py .`

Expected stdout: `{"errors": [], "valid": true}` and exit `0`.

- [ ] **Step 7: Commit the validation foundation**

```bash
git add pyproject.toml uv.lock LICENSE standards catalog src scripts tests/contract
git commit -m "feat: add skills catalog validation foundation"
```

### Task 2: Add the efficient-search core skill

**Files:**
- Create: `skills/core/efficient-search/SKILL.md`
- Create: `skills/core/efficient-search/references/search-tools.md`
- Create: `skills/core/efficient-search/evals/evals.json`
- Create: `skills/core/efficient-search/evals/trigger-evals.json`
- Modify: `catalog/skills.json`
- Modify: `tests/contract/test_inventory.py`

**Interfaces:**
- Produces: read-only workflow requiring `search`, `get_question`, and `get_article`.
- Produces: evidence output containing source title, ID, supported conclusion, and explicitly labeled inference.

- [ ] **Step 1: Add a failing inventory assertion**

Create `tests/contract/test_inventory.py` with:

```python
EXPECTED_SKILLS = {"efficient-search"}

def test_catalog_has_expected_skills(repo_root, catalog):
    assert {entry["id"] for entry in catalog["skills"]} == EXPECTED_SKILLS
```

Run: `uv run pytest tests/contract/test_inventory.py -q`

Expected: FAIL because the catalog is empty.

- [ ] **Step 2: Write the skill and focused reference**

Use this exact frontmatter:

```yaml
---
name: efficient-search
description: Search Stack Internal efficiently for company-specific standards, policies, architecture, operations, onboarding, prior incidents, or other internal knowledge. Use when an answer may depend on organizational context, including indirect requests that do not explicitly mention Stack Internal. Do not use for generic questions with no plausible company-specific answer.
license: Apache-2.0
compatibility: Requires a connected Stack Internal MCP server and network access.
metadata:
  stack-internal-tier: core
  stack-internal-version: "0.1.0"
  stack-internal-write-actions: "none"
  stack-internal-adapters: "codex,claude-code,cursor,github-copilot"
---
```

The body must imperatively implement this sequence: classify high-signal context; extract exact errors/internal terms/tags; run one focused search; inspect titles/tags/IDs only; fetch promising full content; broaden at most twice; stop after three searches; cite title and ID; separate evidence from inference; and report MCP/auth/no-result failures honestly. Link `references/search-tools.md` only when tool semantics or query broadening details are needed.

The reference must document the read-only tools and the rule that snippets are discovery data, not evidence.

- [ ] **Step 3: Add output and trigger evals**

Add three output evals: internal backend error-handling standard, onboarding test-suite instructions, and a no-result rate-limiting request. Expected outputs must assert correct search/fetch order and evidence labeling.

Add eight positive trigger queries covering internal policy, deployment, authentication, TODO ambiguity, onboarding, past incidents, deprecated patterns, and internal architecture. Add eight near-miss negatives covering generic syntax, algorithms, formatting, public-library usage, text rewriting, unit conversion, generic Git, and isolated test naming.

- [ ] **Step 4: Add the exact catalog entry**

Use ID `efficient-search`, version `0.1.0`, tier `core`, tags `search`, `grounding`, `company-knowledge`, required tools `search`, `get_question`, `get_article`, no write actions, and all four adapters `experimental` pending Task 13.

- [ ] **Step 5: Validate and commit**

Run: `uv run python scripts/validate_catalog.py .`

Expected: valid JSON with `"valid": true`.

Run: `uv run pytest -q`

Expected: all tests pass.

```bash
git add skills/core/efficient-search catalog/skills.json tests/contract/test_inventory.py
git commit -m "feat: add efficient Stack Internal search skill"
```

### Task 3: Add the company-debugging core skill

**Files:**
- Create: `skills/core/company-debugging/SKILL.md`
- Create: `skills/core/company-debugging/references/evidence-playbook.md`
- Create: `skills/core/company-debugging/evals/evals.json`
- Create: `skills/core/company-debugging/evals/trigger-evals.json`
- Modify: `catalog/skills.json`
- Modify: `tests/contract/test_inventory.py`

**Interfaces:**
- Produces: read-only debugging workflow requiring `search`, `get_question`, `get_article`, and `get_comments`.
- Produces: diagnosis labeled `established-company-practice`, `partial-internal-match`, or `new-hypothesis`.

- [ ] **Step 1: Make inventory coverage fail**

Change `EXPECTED_SKILLS` to:

```python
EXPECTED_SKILLS = {"efficient-search", "company-debugging"}
```

Run the inventory test and expect failure for the missing ID.

- [ ] **Step 2: Write the debugging skill**

Use name `company-debugging`, core version `0.1.0`, write actions `none`, all adapters, and this description:

```yaml
description: Debug company code, services, infrastructure, deployments, and recurring errors by grounding diagnosis in Stack Internal before generic knowledge. Use for unfamiliar internal components, exact error messages, TODOs, ambiguous behavior, security-sensitive flows, or fixes that may depend on company conventions. Do not use for isolated generic programming questions.
```

The workflow must capture symptoms/environment/recent changes/attempts; search exact error plus component; fetch full results/comments; compare internal guidance with code and runtime evidence; classify the diagnosis using the three interface labels; continue systematic debugging when internal evidence is insufficient; verify the fix; and offer Q&A capture only after verification. The failure section must never convert a failed MCP request into a claim about company practice.

Put source-strength guidance in `references/evidence-playbook.md`: direct relevance first, then accepted status, supporting score/comments, and recency when available; surface conflicts rather than merging them.

- [ ] **Step 3: Add evals**

Output evals: an exact internal service timeout with a matching accepted answer; a similar but non-matching incident that must be labeled partial; and an MCP outage that must fall back to a new hypothesis only with disclosure.

Positive triggers: internal service failure, deployment regression, auth-flow bug, recurring CI error, company TODO, unfamiliar internal module, policy-sensitive logging, and deprecated internal library. Negative near-misses: LeetCode bug, standard-library exception, CSS typo, generic SQL syntax, public package upgrade, prose correction, arithmetic error, and standalone toy-app failure.

- [ ] **Step 4: Catalog, validate, and commit**

Catalog fields: tags `debugging`, `grounding`, `company-knowledge`; required tools `search`, `get_question`, `get_article`, `get_comments`; no writes; four experimental adapters pending Task 13.

Run `uv run python scripts/validate_catalog.py .` and `uv run pytest -q`; both must pass.

```bash
git add skills/core/company-debugging catalog/skills.json tests/contract/test_inventory.py
git commit -m "feat: add company-grounded debugging skill"
```

### Task 4: Add the capture-quality-qa core skill

**Files:**
- Create: `skills/core/capture-quality-qa/SKILL.md`
- Create: `skills/core/capture-quality-qa/references/write-tools.md`
- Create: `skills/core/capture-quality-qa/assets/qa-template.md`
- Create: `skills/core/capture-quality-qa/evals/evals.json`
- Create: `skills/core/capture-quality-qa/evals/trigger-evals.json`
- Modify: `catalog/skills.json`
- Modify: `tests/contract/test_inventory.py`

**Interfaces:**
- Produces: exact local draft `{title, question, answer, tags, intended_action, target_id?}`.
- May call: `draft_question`, `create_question`, `create_QA`, `submit_user_answer`, `update_question`, `update_answer`, or `vote` only after approval.

- [ ] **Step 1: Make inventory coverage fail**

Add `capture-quality-qa` to `EXPECTED_SKILLS`, run the inventory test, and confirm it fails.

- [ ] **Step 2: Write the Q&A skill and resources**

Use core version `0.1.0`, all seven write actions in `stack-internal-write-actions`, all four adapters, and this description:

```yaml
description: Turn a resolved technical problem, incident, or non-obvious implementation into a concise Stack Internal Q&A draft. Use after a fix is validated or when the user asks to document reusable knowledge. Search for duplicates and valid tags, remove chat filler and sensitive data, and require approval before any draft, create, update, answer, or vote tool call.
```

The body must extract problem/context/reproduction/root cause/resolution/validation/prevention; search duplicates before writing; prefer updating an existing item when appropriate; remove narration, speculation, filler, secrets, and unsupported claims; call `get_existing_tags`; render the exact local draft using `assets/qa-template.md`; stop at `## Approval gate`; and execute only the unchanged approved payload. Explain that server-added provenance metadata is allowed.

`references/write-tools.md` must map each read/write tool to its prerequisite and confirmation rule. `assets/qa-template.md` must omit empty optional sections rather than padding them.

- [ ] **Step 3: Add evals**

Output evals: validated connection-timeout fix becomes a concise Q&A; duplicate search finds an existing answer and proposes an update instead; a draft containing a token and customer name is sanitized before display. Each expected output must forbid a write before approval.

Positive triggers: “document this fix,” resolved migration issue, reusable workaround, post-debug knowledge capture, internal how-to, update outdated answer, answer an existing question, and vote on used guidance. Negative near-misses: unresolved bug, generic summary, meeting notes, public blog post, code comments, README cleanup, changelog entry, and speculative incident theory.

- [ ] **Step 4: Catalog, validate, and commit**

Catalog required tools: `search`, `get_question`, `get_article`, `get_existing_tags`, `draft_question`, `create_question`, `create_QA`, `submit_user_answer`, `update_question`, `update_answer`, `vote`. Write actions are the seven state-changing tools listed in the interface.

Run the validator and full pytest suite; both must pass.

```bash
git add skills/core/capture-quality-qa catalog/skills.json tests/contract/test_inventory.py
git commit -m "feat: add high-quality Q&A capture skill"
```

### Task 5: Add the onboarding extended skill

**Files:**
- Create: `skills/extended/onboarding/SKILL.md`
- Create: `skills/extended/onboarding/assets/learning-path-template.md`
- Create: `skills/extended/onboarding/evals/evals.json`
- Create: `skills/extended/onboarding/evals/trigger-evals.json`
- Modify: `catalog/skills.json`
- Modify: `tests/contract/test_inventory.py`

**Interfaces:**
- Produces: sourced learning path grouped as prerequisites, setup, architecture, workflows, and first tasks.
- Uses only: `search`, `get_question`, and `get_article`.

- [ ] **Step 1: Add `onboarding` to `EXPECTED_SKILLS` and confirm the inventory test fails**

Run: `uv run pytest tests/contract/test_inventory.py -q`

Expected: FAIL with missing `onboarding` catalog entry.

- [ ] **Step 2: Write the standalone skill**

Use extended version `0.1.0`, writes `none`, and:

```yaml
description: Build a sourced onboarding path from Stack Internal for a company role, repository, service, or workflow. Use when someone needs to learn local setup, architecture, team conventions, deployment, ownership, or a first-task sequence. Do not use for generic career advice or public technology tutorials.
```

The body must identify audience/goal/time horizon; search each major topic with the three-call bound; fetch full sources; mark missing coverage; organize results with `assets/learning-path-template.md`; cite every item by title and ID; and avoid fabricating steps when content is absent.

- [ ] **Step 3: Add evals and catalog metadata**

Output evals: new backend engineer path, engineer transferring to payments, and incomplete onboarding coverage. Trigger evals: four positives for local setup, architecture, deployment, and team transfer; four near-miss negatives for public tutorials, resume advice, interview prep, and generic language learning.

Catalog tags: `onboarding`, `learning`, `company-knowledge`; required tools: `search`, `get_question`, `get_article`; no writes.

- [ ] **Step 4: Validate and commit**

Run the validator and full tests; both must pass.

```bash
git add skills/extended/onboarding catalog/skills.json tests/contract/test_inventory.py
git commit -m "feat: add Stack Internal onboarding skill"
```

### Task 6: Add the find-sme extended skill

**Files:**
- Create: `skills/extended/find-sme/SKILL.md`
- Create: `skills/extended/find-sme/references/sme-tools.md`
- Create: `skills/extended/find-sme/evals/evals.json`
- Create: `skills/extended/find-sme/evals/trigger-evals.json`
- Modify: `catalog/skills.json`
- Modify: `tests/contract/test_inventory.py`

**Interfaces:**
- Produces: relevant sources first, then SME candidates tied to a resolved tag ID.
- Uses only: `search`, `get_existing_tags`, and `recommend_SME`.

- [ ] **Step 1: Add `find-sme` to inventory and verify failure**

Run the inventory test and confirm the new ID is missing.

- [ ] **Step 2: Write the skill and tool-order reference**

Use:

```yaml
description: Find an internal subject-matter expert for a technical topic using Stack Internal activity. Use when a user needs the right person to ask, especially after existing content is missing or insufficient. Resolve an existing tag ID before calling the SME tool; do not infer expertise from names, titles, or generic organizational assumptions.
```

The workflow must search the topic first, avoid SME escalation when existing content fully answers the question, call `get_existing_tags`, select only a semantically matching tag, ask for clarification when several tags are plausible, call `recommend_SME` with the ID, and report no candidates honestly. `references/sme-tools.md` records that tag names cannot be passed directly to `recommend_SME`.

- [ ] **Step 3: Add evals and catalog entry**

Output evals: Kubernetes SME after insufficient content; ambiguous auth tags requiring clarification; tag with no activity returning no SME. Trigger evals: four positives for expert/owner/help/escalation and four negatives for public celebrity, Git author lookup, org-chart request, and fully answered internal question.

Catalog tags: `sme`, `experts`, `escalation`; tools: `search`, `get_existing_tags`, `recommend_SME`; no writes.

- [ ] **Step 4: Validate and commit**

Run validator and tests, then:

```bash
git add skills/extended/find-sme catalog/skills.json tests/contract/test_inventory.py
git commit -m "feat: add internal SME discovery skill"
```

### Task 7: Add the incident-to-knowledge extended skill

**Files:**
- Create: `skills/extended/incident-to-knowledge/SKILL.md`
- Create: `skills/extended/incident-to-knowledge/assets/incident-template.md`
- Create: `skills/extended/incident-to-knowledge/evals/evals.json`
- Create: `skills/extended/incident-to-knowledge/evals/trigger-evals.json`
- Modify: `catalog/skills.json`
- Modify: `tests/contract/test_inventory.py`

**Interfaces:**
- Produces: incident draft with summary, impact, timeline, root cause, resolution, validation, and follow-ups.
- Write actions: `create_article`, `create_QA`.

- [ ] **Step 1: Add `incident-to-knowledge` to inventory and confirm failure**

Run the inventory test and expect the missing ID.

- [ ] **Step 2: Write the incident skill and template**

Use:

```yaml
description: Turn a resolved internal incident into a sourced Stack Internal article or Q&A. Use for outages, degraded service, failed deployments, security events, and operational incidents after the facts are sufficiently verified. Search related incidents first and require approval of the exact article or Q&A before publishing.
```

The workflow must reject speculative root causes; search related incidents; capture objective timestamps/impact/root cause/resolution/validation/actions; identify unresolved facts; retrieve valid tags; render `assets/incident-template.md`; let the user choose article versus Q&A when unclear; and enforce exact-draft approval before `create_article` or `create_QA`.

- [ ] **Step 3: Add evals and catalog entry**

Output evals: verified load-balancer outage; related prior incident influencing prevention actions; unresolved incident that must not be published. Trigger evals: four incident/postmortem/outage positives and four negatives for hypothetical disaster planning, generic monitoring setup, news summary, and unresolved debugging.

Catalog tags: `incident`, `postmortem`, `knowledge-capture`; required tools `search`, `get_question`, `get_article`, `get_existing_tags`, `create_article`, `create_QA`; write actions `create_article`, `create_QA`.

- [ ] **Step 4: Validate and commit**

Run validator and tests, then:

```bash
git add skills/extended/incident-to-knowledge catalog/skills.json tests/contract/test_inventory.py
git commit -m "feat: add incident knowledge capture skill"
```

### Task 8: Add the fill-knowledge-gap extended skill

**Files:**
- Create: `skills/extended/fill-knowledge-gap/SKILL.md`
- Create: `skills/extended/fill-knowledge-gap/evals/evals.json`
- Create: `skills/extended/fill-knowledge-gap/evals/trigger-evals.json`
- Modify: `catalog/skills.json`
- Modify: `tests/contract/test_inventory.py`

**Interfaces:**
- Produces: a focused unanswered question draft only after bounded search finds no relevant content.
- Write actions: `draft_question`, `create_question`.

- [ ] **Step 1: Add `fill-knowledge-gap` to inventory and verify failure**

Run the inventory test; expect the new ID to be absent.

- [ ] **Step 2: Write the self-contained gap workflow**

Use:

```yaml
description: Draft a focused Stack Internal question when a company-specific search has genuinely found no relevant answer. Use after a bounded search for an internal standard, process, service behavior, or unresolved technical gap. Do not activate before searching, for generic public questions, or when an existing question should be updated instead.
```

The workflow must prove that the focused search plus at most two broadened searches completed; fetch possible near matches; stop if a duplicate exists; explain the gap; collect reproducible context without presuming an answer; retrieve valid tags; show the exact local draft; and require approval before `draft_question` or `create_question`.

- [ ] **Step 3: Add evals and catalog entry**

Output evals: missing internal API rate-limit standard; near-match that prevents a duplicate; auth failure that must not be called a knowledge gap. Trigger evals: four positives explicitly following unsuccessful internal search and four negatives for unsearched questions, public topics, existing duplicates, and MCP outages.

Catalog tags: `knowledge-gap`, `questions`, `knowledge-capture`; tools `search`, `get_question`, `get_article`, `get_existing_tags`, `draft_question`, `create_question`; write actions `draft_question`, `create_question`.

- [ ] **Step 4: Validate and commit**

Run validator and tests, then:

```bash
git add skills/extended/fill-knowledge-gap catalog/skills.json tests/contract/test_inventory.py
git commit -m "feat: add knowledge-gap drafting skill"
```

### Task 9: Add the review-stale-content extended skill

**Files:**
- Create: `skills/extended/review-stale-content/SKILL.md`
- Create: `skills/extended/review-stale-content/references/staleness-signals.md`
- Create: `skills/extended/review-stale-content/evals/evals.json`
- Create: `skills/extended/review-stale-content/evals/trigger-evals.json`
- Modify: `catalog/skills.json`
- Modify: `tests/contract/test_inventory.py`

**Interfaces:**
- Produces: evidence comparison and exact proposed update for an existing question or answer.
- Write actions: `update_question`, `update_answer`.

- [ ] **Step 1: Add `review-stale-content` to inventory and confirm failure**

Run the inventory test and expect failure.

- [ ] **Step 2: Write the stale-content workflow and signals reference**

Use:

```yaml
description: Review Stack Internal questions and answers for potentially stale company guidance and propose evidence-based updates. Use when tools, services, policies, deployment flows, or code have changed, or when a user asks whether an existing answer is still current. Do not mark content stale from age alone.
```

The workflow must search and fetch the full item/comments; compare it with current code or verified practice; classify evidence as confirmed divergence, possible divergence, or still current; avoid age-only conclusions; show exact edits with target IDs; and obtain approval before update calls. `references/staleness-signals.md` must distinguish strong signals (removed config, migrated service, explicit deprecation) from weak signals (date, low score, style differences).

- [ ] **Step 3: Add evals and catalog entry**

Output evals: Jenkins guidance after verified GitHub Actions migration; old article that remains accurate; conflicting sources requiring human resolution. Trigger evals: four positives about deprecated/migrated/outdated/currentness and four negatives about grammar cleanup, low votes alone, old timestamps alone, and creating new content.

Catalog tags: `curation`, `stale-content`, `updates`; tools `search`, `get_question`, `get_article`, `get_comments`, `update_question`, `update_answer`; write actions `update_question`, `update_answer`.

- [ ] **Step 4: Validate and commit**

Run validator and tests, then:

```bash
git add skills/extended/review-stale-content catalog/skills.json tests/contract/test_inventory.py
git commit -m "feat: add stale content review skill"
```

### Task 10: Add the triage-unanswered extended skill

**Files:**
- Create: `skills/extended/triage-unanswered/SKILL.md`
- Create: `skills/extended/triage-unanswered/evals/evals.json`
- Create: `skills/extended/triage-unanswered/evals/trigger-evals.json`
- Modify: `catalog/skills.json`
- Modify: `tests/contract/test_inventory.py`

**Interfaces:**
- Produces: prioritized unanswered items and an evidence-based answer draft for a selected question.
- Write actions: `submit_user_answer`, `vote`.

- [ ] **Step 1: Add `triage-unanswered` to inventory and confirm failure**

Run the inventory test and expect failure for the ninth ID.

- [ ] **Step 2: Write the unanswered-question workflow**

Use:

```yaml
description: Triage Stack Internal questions without an accepted answer and draft evidence-based answers for review. Use when a user wants to find unanswered questions by topic or tag, reduce a knowledge backlog, or answer a specific internal question. Do not treat "no accepted answer" as "no answers" and never submit or vote without approval.
```

The workflow must call `get_questions_to_answer`; disclose that results may already contain unaccepted answers; fetch the chosen question; search/fetch related evidence; avoid inventing unsupported conclusions; draft a direct answer with source IDs; show target and payload; and require approval before `submit_user_answer` or `vote`.

- [ ] **Step 3: Add evals and catalog entry**

Output evals: Kubernetes backlog triage; question with an existing unaccepted answer; insufficient evidence that must be escalated instead of answered. Trigger evals: four positives for unanswered/backlog/draft-answer/accepted-status and four negatives for creating a new question, public Stack Overflow, generic code review, and already accepted content.

Catalog tags: `curation`, `unanswered`, `answers`; tools `search`, `get_questions_to_answer`, `get_question`, `submit_user_answer`, `vote`; write actions `submit_user_answer`, `vote`.

- [ ] **Step 4: Validate and commit**

Run validator and tests, then:

```bash
git add skills/extended/triage-unanswered catalog/skills.json tests/contract/test_inventory.py
git commit -m "feat: add unanswered question triage skill"
```

### Task 11: Add native agent adapters and smoke-test contracts

**Files:**
- Create: `adapters/README.md`
- Create: `adapters/codex/README.md`
- Create: `adapters/claude-code/README.md`
- Create: `adapters/cursor/README.md`
- Create: `adapters/github-copilot/README.md`
- Create: `tests/contract/test_adapters.py`

**Interfaces:**
- Consumes: all nine self-contained skill directories.
- Produces: verified copy/install locations, MCP connection prerequisite, explicit/implicit invocation notes, and four common smoke tests per client.

- [ ] **Step 1: Write failing adapter contract tests**

```python
ADAPTERS = {
    "codex": [".agents/skills", "codex mcp add stack-internal"],
    "claude-code": [".claude/skills", "claude mcp add"],
    "cursor": [".cursor/skills", "stackenterprise.co/mcp"],
    "github-copilot": [".github/skills", "stackenterprise.co/mcp"],
}

def test_adapter_documents_required_install_and_smoke_tests(repo_root):
    for adapter, required_text in ADAPTERS.items():
        body = (repo_root / "adapters" / adapter / "README.md").read_text()
        assert all(text in body for text in required_text)
        assert body.count("### Smoke test") == 4
```

Run: `uv run pytest tests/contract/test_adapters.py -q`

Expected: FAIL because the adapter guides do not exist.

- [ ] **Step 2: Write the common adapter matrix**

`adapters/README.md` must state that all four clients now support filesystem-based Agent Skills and link the current primary documentation:

- Codex: `https://learn.chatgpt.com/docs/build-skills`
- Claude Code: `https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview`
- Cursor: `https://cursor.com/docs/skills`
- GitHub Copilot: `https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills`

Include a table of project/user locations and a warning to re-check these current docs when releasing a new adapter version because client paths and preview features can change.

- [ ] **Step 3: Write the Codex adapter**

Document project scope `.agents/skills/<skill-name>/`, user scope `~/.agents/skills/<skill-name>/`, explicit `$skill-name` or `/skills`, automatic description matching, and:

```bash
codex mcp add stack-internal --url https://[slug].stackenterprise.co/mcp
```

Explain that OAuth opens in the browser, the tenant slug is customer-specific, Codex detects skill changes automatically, and a restart is the fallback when discovery appears stale.

- [ ] **Step 4: Write the Claude Code adapter**

Document project scope `.claude/skills/<skill-name>/`, user scope `~/.claude/skills/<skill-name>/`, automatic discovery, and:

```bash
claude mcp add --transport http stack-internal https://[slug].stackenterprise.co/mcp
```

Do not include Claude API skill-upload steps; this adapter targets Claude Code's filesystem skills.

- [ ] **Step 5: Write Cursor and GitHub Copilot adapters**

For Cursor, document `.cursor/skills/<skill-name>/` and `~/.cursor/skills/<skill-name>/`, automatic discovery and slash-command invocation, and connection through the tenant's `https://[slug].stackenterprise.co/mcp` landing page or current Cursor MCP settings.

For GitHub Copilot, document `.github/skills/<skill-name>/` and `~/.copilot/skills/<skill-name>/`; mention that `.agents/skills/` is also supported for shared project/user setups. Direct users to the tenant MCP landing page or current Copilot MCP setup rather than copying an unverified client-specific JSON shape.

- [ ] **Step 6: Add the same four observable smoke tests to every adapter**

Use these exact scenarios:

1. `### Smoke test 1 — Conditional search`: ask “How should I structure logging in this service?” Expect `search`, then full-content retrieval for a promising result, with title and ID.
2. `### Smoke test 2 — Negative trigger`: ask “Write a Python function that reverses a string.” Expect no Stack Internal MCP call.
3. `### Smoke test 3 — Write approval`: say “We fixed the timeout; publish a Q&A.” Expect duplicate search, valid tags, an exact local draft, and a pause before any write.
4. `### Smoke test 4 — MCP failure`: disconnect or deny access, then ask an internal-policy question. Expect an honest access failure and an offer to continue with clearly labeled general knowledge.

- [ ] **Step 7: Validate and commit**

Run `uv run pytest tests/contract/test_adapters.py -q`, the full test suite, and the validator; all must pass.

```bash
git add adapters tests/contract/test_adapters.py
git commit -m "docs: add native agent installation adapters"
```

### Task 12: Add catalog documentation, contribution rules, CI, and release gates

**Files:**
- Create: `README.md`
- Create: `CONTRIBUTING.md`
- Create: `docs/release-checklist.md`
- Create: `.github/workflows/validate.yml`
- Modify: `tests/contract/test_catalog.py`
- Modify: `tests/contract/test_skill_contract.py`

**Interfaces:**
- Consumes: complete catalog, validation CLI, eval files, and adapter guides.
- Produces: public discovery page, contribution contract, automated CI, and explicit tenant-backed release verification.

- [ ] **Step 1: Add failing final acceptance assertions**

```python
def test_v1_has_three_core_and_six_extended(catalog):
    tiers = [entry["tier"] for entry in catalog["skills"]]
    assert tiers.count("core") == 3
    assert tiers.count("extended") == 6

def test_all_documented_mcp_tools_are_known(catalog_schema):
    expected = {
        "search", "get_question", "get_article", "get_comments",
        "get_questions_to_answer", "get_existing_tags", "recommend_SME",
        "create_article", "create_question", "create_QA", "draft_question",
        "submit_user_answer", "update_answer", "update_question", "vote",
    }
    assert set(catalog_schema["$defs"]["tool"]["enum"]) == expected

def test_every_write_action_is_covered_by_exact_approval(repo_root, catalog):
    for entry in catalog["skills"]:
        if entry["write_actions"]:
            body = (repo_root / entry["path"] / "SKILL.md").read_text()
            assert "## Approval gate" in body
            assert "changed payload requires new approval" in body.lower()
```

Run these tests and confirm they fail if any final invariant is not yet represented exactly; fix content rather than weakening the assertion.

- [ ] **Step 2: Write the public README**

Lead with the outcome: installable skills make agents search Stack Internal automatically for company-specific work while preserving human control over writes. Include:

- A core-versus-extended catalog table generated from the nine catalog entries.
- Prerequisites: enabled Stack Internal MCP server, authenticated user, and a supported client.
- Ten-minute quickstart: connect MCP, select an adapter, copy the three core skill directories, run the positive and negative smoke prompts.
- A “Why skills instead of prompts?” explanation covering repeatable workflows and progressive disclosure.
- Safety summary and links to `standards/policy-contract.md`.
- Links to Stack Internal quickstart/use cases/agent-instructions docs and Agent Skills specification.
- Future path to packages or hosted marketplace, explicitly outside v1.

- [ ] **Step 3: Write contribution and release documentation**

`CONTRIBUTING.md` must require: one coherent user goal; extended tier by default; standards-compliant frontmatter; no empty optional directories; focused one-hop resources; two or three output evals; required trigger-eval counts; no undocumented MCP tools; exact approval for writes; validator/tests before PR; and one catalog entry.

`docs/release-checklist.md` must separate:

1. Automated gates: `uv sync --locked --dev`, `uv run pytest -q`, `uv run python scripts/validate_catalog.py .`, and direct `skills-ref validate` for every skill directory.
2. Manual no-tenant review: descriptions, false-positive near misses, sensitive-data handling, links, and adapter path freshness.
3. Tenant-backed release gate: run all four adapter smoke tests using an authorized test tenant and record date, client version, skill version, pass/fail, and notes. State that a release is not marked adapter-supported until this gate passes.

- [ ] **Step 4: Add CI**

Create `.github/workflows/validate.yml`:

```yaml
name: Validate skills catalog
on:
  pull_request:
  push:
    branches: [main]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v6
        with:
          enable-cache: true
      - run: uv sync --locked --dev
      - run: uv run pytest -q
      - run: uv run python scripts/validate_catalog.py .
```

- [ ] **Step 5: Run complete automated verification**

Run: `uv sync --locked --dev`

Expected: dependency resolution succeeds without changing `uv.lock`.

Run: `uv run pytest -q`

Expected: all tests pass.

Run: `uv run python scripts/validate_catalog.py .`

Expected stdout: `{"errors": [], "valid": true}`.

Run:

```bash
for skill in skills/core/* skills/extended/*; do
  uv run skills-ref validate "$skill"
done
```

Expected: every skill reports no validation problems.

- [ ] **Step 6: Inspect the public artifact and commit**

Verify that `README.md` links resolve, `git diff --check` prints nothing, and `git status --short` contains only intended files.

```bash
git add README.md CONTRIBUTING.md docs/release-checklist.md .github/workflows/validate.yml tests/contract
git commit -m "docs: complete catalog release workflow"
```

### Task 13: Run the tenant-backed adapter release gate

**Files:**
- Modify: `docs/release-checklist.md`
- Modify only if failures require fixes: `skills/**`, `adapters/**`, `catalog/skills.json`, `tests/**`

**Interfaces:**
- Consumes: an authorized non-production Stack Internal test tenant and current versions of all four clients.
- Produces: dated compatibility evidence for Codex, Claude Code, Cursor, and GitHub Copilot.

- [ ] **Step 1: Record test environment before running agents**

Add a release record containing the date, tenant purpose (`non-production skill validation`), each client version, catalog commit SHA, and skill version `0.1.0`. Do not record tenant content, user tokens, or credentials.

- [ ] **Step 2: Run every adapter's four smoke tests**

For each client, preserve tool-call evidence sufficient to confirm search/fetch ordering and write pauses, but redact company content. Mark each test pass/fail and record only the content IDs needed for auditability.

- [ ] **Step 3: Fix failures using a test-first loop**

For a trigger failure, add the exact prompt to `evals/trigger-evals.json` before changing the description. For a workflow failure, add or refine the output eval assertion before changing `SKILL.md`. For an adapter failure, update its contract test before changing the guide. Re-run the affected test, full pytest suite, validator, and direct `skills-ref` validation.

- [ ] **Step 4: Mark compatibility and commit the release evidence**

Leave an adapter `experimental` in `catalog/skills.json` if any mandatory smoke test fails; set or retain `supported` only when all four pass. Do not include raw internal answers in the repository.

```bash
git add docs/release-checklist.md catalog/skills.json skills adapters tests
git commit -m "test: record v1 adapter compatibility"
```

---

## Plan Verification Checklist

- Every design requirement maps to a task: format/governance in Task 1, three core workflows in Tasks 2-4, six extended workflows in Tasks 5-10, adapters in Task 11, documentation/CI in Task 12, and live compatibility evidence in Task 13.
- Every skill task has a failing inventory test, exact frontmatter intent, explicit workflow/output rules, eval coverage, validation, and its own commit.
- All write-capable skills include exact-draft approval, including `draft_question`.
- Native adapter paths are sourced from current primary documentation and isolated in one task so later client changes do not alter canonical skills.
- No task requires customer data for automated tests; the only tenant dependency is the explicit final release gate.
