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

- [ ] Confirm generated packages and native manifests match their canonical sources:

  ```bash
  uv run python scripts/build_marketplace.py packages --mode check --root .
  ```

- [ ] Confirm two site builds from the exact current commit are byte-identical:

  ```bash
  uv run python scripts/build_marketplace.py site --root . --output dist-a --source-commit "$(git rev-parse HEAD)"
  uv run python scripts/build_marketplace.py site --root . --output dist-b --source-commit "$(git rev-parse HEAD)"
  diff -ru dist-a dist-b
  ```

Record the commit SHA, CI run URL, result, and reviewer for these gates.

## GitHub Pages publication guard

- [ ] In GitHub repository settings, configure and verify the `github-pages` environment allows deployments only from the `main` branch. This externally managed setting is not configured or verified by this repository.

## Manual no-tenant review

- [ ] Read every changed description and confirm it states what and when, triggers on high-signal company context, and avoids routine generic work.
- [ ] Exercise representative positive triggers and false-positive near misses against simulated fixtures; record unexpected activations and misses.
- [ ] Review every displayed and submitted field for secrets, credentials, tokens, personal data, unnecessary customer data, and unsafe reproduction of retrieved content.
- [ ] Resolve every relative documentation and skill-resource link.
- [ ] Re-check each changed adapter's official client documentation and confirm installation paths, invocation instructions, authentication flow, and limitations are current.
- [ ] Confirm all adapter states remain `experimental`; simulated checks and a manual no-tenant review do not justify `supported`.

Record the commit SHA, reviewer, review date, changed skills and adapters, pass/fail result, and notes.

## Native marketplace manual gates

- [ ] In a clean project using the exact Codex version recorded in [the marketplace testing matrix](marketplace-testing.md), test the Codex native flow: marketplace add, plugin list, individual install, three-plugin core install, explicit invocation, update, disablement, and removal.
- [ ] In a clean project using the exact Claude Code version recorded in [the marketplace testing matrix](marketplace-testing.md), test the Claude Code native flow: marketplace add, plugin list, individual install, three-plugin core install, explicit invocation, update, disablement, and removal.
- [ ] Record the observed project-scope behavior separately for Codex and Claude Code. Codex command-driven marketplace registration is client-managed; do not claim a Codex project-scope flag. Claude marketplace add uses `--scope project` and its interactive install flow chooses project scope.
- [ ] Navigate the public GitHub Pages URL `https://estoesmoises.github.io/stack-mcp-skills/`; confirm it presents the exact source commit deployed by Pages, lists exactly nine plugin entries, and its install instructions and linked skill pages resolve.
- [ ] Run all four tenant-backed smokes for the exact Codex and Claude Code client, plugin, and skill versions; record only redacted results under the fixed tenant purpose `non-production skill validation`.

Exact client versions and pass/fail results are manual evidence fields. Do not record raw tenant data, tenant identifiers, slugs, credentials, tokens, personal data, customer data, or raw retrieved content.

## Task 8 pre-evidence rehearsal status — 2026-08-04

The exercised pre-evidence rehearsal candidate was `46c91c8200b78abbbde83b39f80e42c8f91b7da0` (marketplace version `0.1.0`), not a tenant-evidence candidate. `claude plugin validate .` and all nine generated plugin directories passed with Claude Code `2.1.220`; Codex `0.142.5` completed the local isolated-profile add/list/install/remove rehearsal for `efficient-search@stack-internal` version `0.1.0`. This verifies only local structural/native validation and the limited isolated Codex lifecycle.

The corresponding Claude project-scoped local add was blocked before configuration when the client attempted to open its personal known-marketplace cache and received `EPERM`. No personal client state was changed, and no global or user scope was used. The Codex and Claude public GitHub-source rehearsals are pending because this candidate has not been published to public `main`. No tenant was authorized; no tenant data was accessed, no smoke artifacts were created, and `compatibility/evidence.json` remains empty.

### Outstanding publication and evidence gates

- [ ] Publish the exact candidate to public `main`, then run the public GitHub-source add/list/install rehearsal for both native clients. Do not substitute the local rehearsal for this gate.
- [ ] Deploy and inspect the public Pages catalog at `https://estoesmoises.github.io/stack-mcp-skills/`; confirm its displayed source commit, nine plugin entries, installation instructions, and linked skill pages.
- [ ] In a clean authorized Codex profile, complete the remaining native lifecycle checks: the three independent core installs, explicit invocation, marketplace refresh/update, and any supported disable/remove behavior. Codex registration is client-managed; do not claim a project-scope flag.
- [ ] In a clean Claude Code environment that does not touch personal state, complete the project-scoped marketplace add/list/install/update/disable/remove checks. Resolve the blocked personal-cache behavior before treating that lifecycle as exercised.
- [ ] With an authorized non-production tenant and the fixed purpose `non-production skill validation`, run all four redacted smokes for each required adapter/client and exact plugin/skill versions.
- [ ] Create and validate the required redacted smoke artifacts and compatibility records only after the authorized smokes pass on their exact evidence-bearing candidate.

Until every applicable publication, native lifecycle, and authorized tenant gate above has passed, every adapter remains `experimental`.

## Tenant-backed release gate

Using an authorized test tenant, run all four adapter smoke tests from each adapter guide for Codex, Claude Code, Cursor, and GitHub Copilot. Test the exact release candidate skill content. Confirm conditional search, the generic negative trigger, the write-approval pause, and honest MCP failure handling from observable tool calls and responses.

Create one evidence record per client and skill version in `compatibility/evidence.json`, validated by `standards/adapter-evidence-schema.json`. Set `release_candidate_commit` to the exact tested Git commit. It must be a real ancestor commit in this repository, and every record's `catalog_commit` must match it exactly. Leave the field `null` while the registry is empty.

Each smoke-test entry must reference an existing nonempty JSON artifact below `compatibility/smoke-evidence/`. The artifact must be present unchanged in the release-candidate commit, validate against `standards/smoke-evidence-schema.json`, identify the same adapter and numbered smoke test, use only the fixed redacted check identifier, and contain no raw retrieved content or tenant data. Absolute paths, traversal, dangling references, and unrelated test artifacts fail validation.

| Date | Client | Client version | Skill version | Commit SHA | Tenant purpose | Smoke tests | Pass/fail | Notes | Reviewer |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| YYYY-MM-DD | Codex, Claude Code, Cursor, or GitHub Copilot | Exact tested version | Exact tested catalog/skill version | Tested commit | non-production skill validation | 1-4 with non-sensitive evidence references | Pass or fail | Limitations and failures | Name |

- [ ] Every client has results for smoke tests 1 through 4.
- [ ] The release-candidate commit exists in this repository, is an ancestor of the validating checkout, and matches every record.
- [ ] Every numbered smoke reference resolves to the exact redacted structured artifact committed with that release candidate.
- [ ] Evidence records only the fixed tenant purpose `non-production skill validation`. It must not record a public or private tenant identifier, slug, name, credentials, tokens, raw retrieved content, personal data, or customer data.
- [ ] Failures and client limitations are documented; no simulated result is substituted for a live run.
- [ ] The evidence record is reviewed before any compatibility metadata changes.

An adapter must not be marked or promoted to `supported` until this tenant-backed release gate passes for its exact client and skill versions and the repository has an auditable mechanism to record and validate that evidence. A release with any incomplete tenant gate keeps that adapter `experimental`; `unsupported` remains valid for an adapter the catalog does not offer.
