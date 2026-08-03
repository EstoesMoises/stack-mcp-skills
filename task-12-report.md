# Task 12 implementation report

## Scope

Added the public catalog README, contribution contract, release checklist, GitHub Actions validation workflow, and final acceptance coverage. No tenant-backed smoke test was run, no adapter was promoted, and no ledger was created or changed.

## RED evidence

Command:

```bash
.venv/bin/python -m pytest tests/contract/test_catalog.py tests/contract/test_skill_contract.py::test_every_write_action_is_covered_by_exact_approval tests/contract/test_release_workflow.py -q
```

Initial result:

```text
..........FFFFFF                                                         [100%]
6 failed, 10 passed in 0.26s
```

The failures were the intended missing contracts: `README.md`, `CONTRIBUTING.md`, `docs/release-checklist.md`, `.github/workflows/validate.yml`, and the exact changed-payload approval wording in write-capable skills. One regex syntax error surfaced during the first GREEN run; it was corrected before acceptance.

## GREEN and verification evidence

Focused acceptance:

```text
................                                                         [100%]
16 passed in 0.14s
```

Locked dependency sync, using the available temporary `uv` binary and a writable temporary cache:

```text
Resolved 19 packages in 1ms
Checked 17 packages in 1ms
```

`uv.lock` SHA-256 before and after sync:

```text
3c47199272ca38d2246c37cbddb79d3f3c2ccdb9316ce98cb2a0ec9d73a11560  uv.lock
```

Full suite:

```text
...............................................                          [100%]
47 passed in 0.22s
```

Catalog CLI:

```json
{"errors": [], "valid": true}
```

Direct reference validation:

```text
Valid skill: skills/core/capture-quality-qa
Valid skill: skills/core/company-debugging
Valid skill: skills/core/efficient-search
Valid skill: skills/extended/fill-knowledge-gap
Valid skill: skills/extended/find-sme
Valid skill: skills/extended/incident-to-knowledge
Valid skill: skills/extended/onboarding
Valid skill: skills/extended/review-stale-content
Valid skill: skills/extended/triage-unanswered
```

The focused relative-link check reported `1 passed in 0.01s`. `git diff --check` produced no output. README/catalog parity, CI commands, release-gate separation, tier counts, tool enumeration, write-action declarations, and exact re-approval language are covered by the passing contract suite.

## Release state

All four adapters remain `experimental`. Task 13's authorized-tenant evidence remains required before any adapter may be marked `supported`.
