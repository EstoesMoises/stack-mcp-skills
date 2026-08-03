# Catalog release checklist

Record evidence for each gate. Automated and manual no-tenant checks validate repository quality, but neither is live adapter compatibility evidence.

## Automated gates

- [ ] Install exactly the locked development environment without modifying `uv.lock`:

  ```bash
  uv sync --locked --dev
  ```

- [ ] Run the complete contract suite:

  ```bash
  uv run pytest -q
  ```

- [ ] Run the repository validator and confirm `{"errors": [], "valid": true}`:

  ```bash
  uv run python scripts/validate_catalog.py .
  ```

- [ ] Run the upstream reference validator for every canonical skill:

  ```bash
  for skill in skills/core/* skills/extended/*; do
    uv run skills-ref validate "$skill"
  done
  ```

Record the commit SHA, CI run URL, result, and reviewer for these gates.

## Manual no-tenant review

- [ ] Read every changed description and confirm it states what and when, triggers on high-signal company context, and avoids routine generic work.
- [ ] Exercise representative positive triggers and false-positive near misses against simulated fixtures; record unexpected activations and misses.
- [ ] Review every displayed and submitted field for secrets, credentials, tokens, personal data, unnecessary customer data, and unsafe reproduction of retrieved content.
- [ ] Resolve every relative documentation and skill-resource link.
- [ ] Re-check each changed adapter's official client documentation and confirm installation paths, invocation instructions, authentication flow, and limitations are current.
- [ ] Confirm all adapter states remain `experimental`; simulated checks and a manual no-tenant review do not justify `supported`.

Record the commit SHA, reviewer, review date, changed skills and adapters, pass/fail result, and notes.

## Tenant-backed release gate

Using an authorized test tenant, run all four adapter smoke tests from each adapter guide for Codex, Claude Code, Cursor, and GitHub Copilot. Test the exact release candidate skill content. Confirm conditional search, the generic negative trigger, the write-approval pause, and honest MCP failure handling from observable tool calls and responses.

Create one evidence record per client and skill version in `compatibility/evidence.json`, validated by `standards/adapter-evidence-schema.json`:

| Date | Client | Client version | Skill version | Commit SHA | Tenant purpose | Smoke tests | Pass/fail | Notes | Reviewer |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| YYYY-MM-DD | Codex, Claude Code, Cursor, or GitHub Copilot | Exact tested version | Exact tested catalog/skill version | Tested commit | non-production skill validation | 1-4 with non-sensitive evidence references | Pass or fail | Limitations and failures | Name |

- [ ] Every client has results for smoke tests 1 through 4.
- [ ] Evidence records only the fixed tenant purpose `non-production skill validation`. It must not record a public or private tenant identifier, slug, name, credentials, tokens, raw retrieved content, personal data, or customer data.
- [ ] Failures and client limitations are documented; no simulated result is substituted for a live run.
- [ ] The evidence record is reviewed before any compatibility metadata changes.

An adapter must not be marked or promoted to `supported` until this tenant-backed release gate passes for its exact client and skill versions and the repository has an auditable mechanism to record and validate that evidence. A release with any incomplete tenant gate keeps that adapter `experimental`; `unsupported` remains valid for an adapter the catalog does not offer.
