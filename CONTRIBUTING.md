# Contributing to the Stack Internal skills catalog

Each contribution should solve one coherent user goal with one independently installable Agent Skill. New skills enter the extended tier by default; propose the core tier only for a broadly required foundation used by multiple workflows.

## Skill contract

- Follow the [Agent Skills specification](https://agentskills.io/specification). The directory name and frontmatter `name` must match, use lowercase letters, numbers, and single hyphens, and stay within 64 characters. Write a non-empty `description` of no more than 1024 characters that states what the skill does and when it should activate.
- Set `license: Apache-2.0`. Keep project metadata string-only and prefix every key with `stack-internal-`. Do not add the experimental `allowed-tools` field.
- Keep `SKILL.md` under 500 lines and 20,000 characters. Include exact `## Workflow` and `## Failure handling` headings, plus `## Approval gate` for every write-capable skill.
- Keep the skill self-contained. Add `references/`, `scripts/`, or `assets/` only for a concrete progressive-disclosure need, with no empty optional directories. Link every resource from `SKILL.md`, explain when to load or run it, keep paths inside the skill root without `..`, and allow only one reference hop from `SKILL.md`.
- Declare exactly one catalog entry in [catalog/skills.json](catalog/skills.json). Its ID, tier, version, adapters, tools, and write actions must agree with the skill metadata and directory. Use only MCP tools and write actions documented by [the catalog schema](standards/catalog-schema.json); do not introduce an undocumented MCP tool.
- Keep all adapter states `experimental` until the [tenant-backed release gate](docs/release-checklist.md) passes and auditable promotion support exists. An adapter may translate installation paths, but it may not weaken triggers, workflow semantics, or safety rules.

## Behavioral standards

Preserve every invariant in the [policy contract](standards/policy-contract.md): conditional high-signal search, no more than three searches per lookup unless the user requests continuation, full retrieval before evidence, source title and ID attribution, separately labeled inference, duplicate review, valid-tag lookup when required, sensitive-data removal, and honest failure reporting.

For every write:

1. Search for duplicate or related content and fully retrieve plausible targets.
2. Retrieve valid tags when the selected action requires them.
3. Inspect the selected connected MCP tool's current live input schema.
4. Render the exact client payload, target, tags, intended tool, and complete schema-required arguments locally.
5. Obtain explicit approval of that unchanged payload and action before the MCP call. A changed payload requires new approval.
6. Send the displayed arguments byte-for-byte, then report only the server-confirmed result.

Never place secrets, credentials, tokens, personal data, or unnecessary customer data in a proposed or submitted payload.

## Evaluation contract

Add `evals/evals.json` and `evals/trigger-evals.json` beside the skill:

- Start with two or three output evals by default, including a realistic edge case. Expand beyond that default when observed failures need durable coverage. Each case must have a non-empty ID, prompt, and observable expected outcome; read-only cases must forbid every catalog write action.
- A core skill requires at least eight positive and eight negative trigger evals.
- An extended skill requires at least four positive and four negative trigger evals.
- Positive cases must vary phrasing, explicitness, context, and detail. Negative cases must be realistic near misses that protect against false activation.
- Use simulated MCP responses in automated tests. Never connect the automated suite to a customer tenant.
- Update adapter smoke expectations when the workflow changes, without presenting simulated results as tenant compatibility evidence.

## Pull request checklist

- [ ] The skill addresses one coherent user goal and does not duplicate an existing workflow.
- [ ] Frontmatter, local resources, catalog metadata, tool declarations, and write declarations satisfy the contract above.
- [ ] Trigger behavior stays narrow enough that generic work does not search Stack Internal automatically.
- [ ] Every write uses exact live-schema arguments and unchanged-payload approval; no draft, create, answer, update, or vote happens before approval.
- [ ] Output and trigger evals meet the tier requirements and cover relevant failure paths.
- [ ] Relevant adapter guidance remains accurate and compatibility remains experimental pending tenant evidence.
- [ ] `uv sync --locked --dev` succeeds without changing `uv.lock`.
- [ ] `uv run pytest -q` passes.
- [ ] `uv run python scripts/validate_catalog.py .` returns `{"errors": [], "valid": true}`.
- [ ] `uv run skills-ref validate <skill-directory>` reports no validation problems for every changed skill.
- [ ] Documentation links resolve and `git diff --check` is clean.
