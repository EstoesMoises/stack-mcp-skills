# Hosted Stack Internal Skills Marketplace Design

## Summary

Extend the public `stack-mcp-skills` repository into a hosted, installable marketplace for Codex and Claude Code. GitHub remains the distribution source, GitHub Pages provides the public browsing experience, and each client performs installation through its native plugin marketplace commands.

The existing `catalog/skills.json` and canonical directories under `skills/` remain the only hand-edited sources of skill metadata and behavior. Generated plugin wrappers make those skills installable without changing their workflows or safety policies. The MVP runs no model, proxies no MCP calls, stores no customer data, and requires no custom installer or backend.

## Context

The current catalog on `main` contains three core and six extended Agent Skills, a machine-readable index, agent adapter guides, contract validation, behavioral evals, and compatibility evidence gates. Installation currently requires users to copy complete skill directories into client-specific filesystem locations.

Codex and Claude Code now support Git-backed plugin marketplaces. Both clients can package skills inside plugins, add a marketplace from GitHub, install individual entries, and manage updates through native commands. The hosted MVP should use these primitives rather than reproduce download, cache, update, receipt, or uninstall behavior.

## Goals

- Make all nine public skills discoverable through a public GitHub Pages catalog.
- Let users register the public repository as a marketplace through native Codex or Claude Code commands.
- Let users install one skill at a time.
- Provide an "Install core bundle" convenience flow that installs the three core skills individually.
- Default to project-scoped trials where the client supports an explicit project scope.
- Preserve the canonical Agent Skills content and all existing safety contracts.
- Keep marketplace packages, client manifests, website metadata, and skill versions synchronized automatically.
- Give users guided positive, negative, write-approval, and MCP-failure smoke tests after installation.
- Keep the MVP fully static and reproducible from repository content.

## Non-goals

- A hosted model or browser-based skill playground.
- A custom package manager, Python installer, shell installer, or installation receipt format.
- Proxying or storing Stack Internal MCP traffic.
- Collecting tenant slugs, OAuth credentials, customer content, or raw compatibility evidence.
- Publishing immediately to either vendor's universal curated marketplace.
- Marketplace packaging for Cursor or GitHub Copilot in this MVP. Their existing filesystem adapters remain supported by the canonical catalog.
- Organization administration, billing, usage analytics, ratings, reviews, or recommendations.

## Approved product decisions

- The repository, skills, and marketplace are public.
- Users try skills in their local Codex or Claude Code client, not in a hosted playground.
- Project-local installation is the preferred trial scope.
- The marketplace offers individual skills plus one core-selection shortcut.
- Hosting is static GitHub Pages with no application backend.
- Codex and Claude Code native plugin marketplace commands replace a custom installer.
- GitHub is both the source host and installable marketplace; GitHub Pages is the human-friendly storefront.

## Architecture

```text
Canonical source                    Generated distribution

catalog/skills.json ─────┐          .agents/plugins/marketplace.json
                         ├─ builder ─.claude-plugin/marketplace.json
skills/**/SKILL.md ──────┤          plugins/<skill-id>/
skills/**/{assets,...} ──┤          site-data/catalog.json
compatibility/evidence ──┘          dist/ (GitHub Pages)
```

### Canonical catalog

`catalog/skills.json` remains the discovery index. Each `skills/core/<id>/` or `skills/extended/<id>/` directory remains the behavioral source of truth. Contributors do not edit generated plugin packages or site data directly.

The existing schema, validation library, policy contract, evals, and compatibility evidence registry continue to govern the canonical content. Marketplace work adds validations; it does not replace existing checks.

### Marketplace builder

A focused Python builder uses the repository's existing Python runtime and catalog loader. It performs these deterministic operations:

1. Validate the canonical catalog and skills.
2. Create one generated plugin wrapper per skill.
3. Create Codex and Claude Code marketplace manifests.
4. Create normalized static site data.
5. Render the framework-free GitHub Pages site into `dist/`.

The builder has a write mode for maintainers and a check mode for CI. Check mode generates into a temporary directory and compares the result with committed generated files. Any difference blocks the release.

### Generated plugin wrappers

Each catalog skill becomes one plugin at `plugins/<skill-id>/`:

```text
plugins/<skill-id>/
├── .codex-plugin/
│   └── plugin.json
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   └── <skill-id>/
│       ├── SKILL.md
│       ├── evals/
│       └── any referenced assets or references
├── README.md
└── LICENSE
```

The directory under `skills/<skill-id>/` is a byte-for-byte copy of the canonical skill directory. Both manifests use the catalog skill ID as the plugin name and the catalog skill version as the plugin version. Client-specific presentation fields may differ, but identity, version, description, included skill, source URL, and license must agree.

The generated package includes no hooks, executable installer, bundled MCP server, tenant URL, or authentication material. The foreign client's manifest may coexist in the plugin directory; each client uses its own manifest.

### Native marketplace manifests

The repository exposes two generated manifests:

- `.agents/plugins/marketplace.json` for Codex.
- `.claude-plugin/marketplace.json` for Claude Code.

Both use `stack-internal` as the marketplace identifier and contain the same nine plugin IDs in the same order. Entries point to `./plugins/<skill-id>` within the public repository and include client-appropriate presentation and install-policy metadata.

Separate manifests are used instead of relying on one client's compatibility parser. This permits strict validation against each native schema and avoids limiting either catalog to their overlapping fields.

### Static marketplace

GitHub Pages serves a framework-free static site. It has no server-side rendering, database, identity system, model runtime, or MCP connection. All content is generated from the repository at build time.

The homepage includes:

- Search across names, summaries, and tags.
- Core and extended tier filters.
- Tag, client, and read-only/write-capable filters.
- A primary "Install core bundle" action.
- One card per catalog skill.
- A visible experimental-compatibility notice.

Each skill page includes:

- Purpose and automatic triggering conditions.
- Tier, version, source commit, and tags.
- Required Stack Internal MCP tools.
- A read-only or approval-gated-write indicator.
- Codex and Claude Code installation tabs.
- MCP connection instructions with a literal `[tenant-slug]` placeholder.
- Explicit invocation syntax after plugin namespacing.
- Positive, negative, MCP-failure, and applicable write-approval smoke prompts.
- Expected observable behavior for every smoke.
- Links to the canonical `SKILL.md`, release, source commit, adapter guide, and compatibility status.

## Installation experience

### Codex quick test

The public page presents native commands using the public GitHub repository:

```bash
codex plugin marketplace add EstoesMoises/stack-mcp-skills
codex plugin add efficient-search@stack-internal
```

Codex then manages the marketplace snapshot, plugin cache, enablement, upgrades, and removal. The page also shows `codex plugin marketplace list` and `codex plugin list --json` as verification commands.

The current Codex marketplace-add command does not expose an explicit project-scope flag. Therefore the command-driven quick test uses Codex's client-managed marketplace configuration. For a repository-shared setup, the site additionally provides a copyable repo-scoped `.agents/plugins/marketplace.json` configuration that points to the selected Git-backed plugin source. The UI labels this distinction instead of claiming that the CLI flag is project-scoped.

### Claude Code project trial

The public page presents the project-scoped marketplace command:

```bash
claude plugin marketplace add EstoesMoises/stack-mcp-skills --scope project
```

The user then installs from Claude Code and chooses project scope in the native installation flow:

```text
/plugin install efficient-search@stack-internal
/reload-plugins
```

Claude Code manages the marketplace cache, plugin cache, enablement, updates, and removal.

### Core selection

The core selection is a UI convenience, not a tenth plugin. It expands to three native installs:

- `efficient-search`
- `company-debugging`
- `capture-quality-qa`

The marketplace is registered only once. Each core plugin remains independently updatable, disableable, and removable. This prevents duplicate skill identities when a user later adds or removes an individual core workflow.

### MCP setup and trying a skill

Plugin installation and Stack Internal connection are deliberately separate. After installation, the page guides users through three observable states:

1. Marketplace registered.
2. Plugin installed, enabled, and discoverable.
3. Stack Internal MCP configured and authenticated for the user's tenant.

The site never asks the user to submit a tenant slug. It shows local setup commands with `[tenant-slug]` as a placeholder and links to the existing adapters. Once connected, the user runs the page's copyable smoke prompts in a new or reloaded client session.

## Versioning and release flow

Skill versions remain independent semantic versions in `catalog/skills.json` and `SKILL.md` metadata. Any installable behavior or packaged resource change requires that skill's version to increase. Documentation-only changes outside an installed package do not require a skill version bump.

The marketplace has its own version because entry ordering, presentation metadata, and the core selection can change without changing a skill. The generated static data records the marketplace version and source commit. It does not embed the current clock time, so repeated builds from the same commit remain identical.

A release follows this sequence:

1. Edit canonical catalog or skill files.
2. Increase every affected skill version.
3. Run the generator to update plugins, native manifests, and site data.
4. Run repository, generator, native-manifest, and site checks.
5. Merge only an internally consistent, installable state to `main`.
6. Tag the exact catalog state and create a GitHub Release.
7. Deploy GitHub Pages from the same successful commit.

The public marketplace follows `main`, which must remain releasable. The exact release commit provides the immutable identity for evidence and reproducible testing, while its version tag provides the human-readable release name. Marketplace entries may be pinned to that commit during compatibility testing.

Users refresh through native commands:

```bash
codex plugin marketplace upgrade stack-internal
claude plugin marketplace update stack-internal
```

A refreshed marketplace does not silently justify a compatibility promotion. Adapter status remains tied to the exact client, skill version, catalog commit, and tenant-backed evidence required by the existing release gate.

## Data flow

### Browse flow

1. GitHub Pages loads generated static catalog data from the same deployment.
2. Search and filtering run entirely in the browser.
3. Selecting a skill opens a generated detail page.
4. Selecting a client reveals native commands and client-specific smoke guidance.
5. No user input or tenant value is sent to a marketplace backend because none exists.

### Install flow

1. The user adds the GitHub repository as a native marketplace.
2. The client reads its native marketplace manifest.
3. The user selects a plugin.
4. The client resolves and caches the generated plugin directory.
5. The client reads its plugin manifest and discovers the packaged skill.
6. The user enables or reloads the plugin as required by the client.
7. The user configures Stack Internal MCP separately and authenticates through the provider's OAuth flow.
8. The user runs the smoke prompts and observes tool calls and responses locally.

### Update flow

1. A maintainer releases an updated catalog with bumped affected versions.
2. The user refreshes the registered marketplace.
3. The client detects newer plugin metadata.
4. The user updates through the native client.
5. The client replaces its cached package according to its own lifecycle.

The repository does not mutate a consumer project through a custom program and does not maintain a parallel installation state.

## Safety and privacy

- Public packages contain only public skill instructions, public fixtures, public metadata, and public documentation.
- Tenant slugs, OAuth tokens, credentials, Stack Internal content, personal data, and customer identifiers are forbidden in generated output.
- The GitHub Pages site has no tenant form and no MCP proxy.
- The MVP adds no third-party analytics or tracking scripts.
- Plugins include no install hooks, lifecycle hooks, arbitrary executables, or bundled MCP server.
- Installation never implies permission to call Stack Internal; the user must configure and authorize MCP separately.
- Installation never grants permission to write content. Existing exact-payload approval rules remain inside every write-capable skill.
- The site identifies every write-capable skill and lists its declared write actions.
- Compatibility remains `experimental` until the exact released packages pass the tenant-backed evidence gate.

## Failure handling

- **Plugin command unavailable:** tell the user to update the client to a release that supports plugin marketplaces.
- **Marketplace add fails:** preserve local state and point to Git/GitHub access, repository spelling, client policy, and manifest validation checks.
- **Marketplace policy blocks the source:** identify the managed allowlist restriction; do not recommend bypassing administrator policy.
- **Plugin is not found:** refresh the marketplace, confirm the `stack-internal` marketplace name, and check that the plugin ID appears in the native list command.
- **Plugin install fails validation:** report the plugin ID and version and link to the release issue path. Do not fall back to running unvalidated scripts.
- **Plugin is installed but undiscovered:** enable or reload it, start a new session when necessary, and verify namespaced invocation.
- **MCP is unavailable or unauthorized:** keep the installed plugin intact, report the separate connection problem, and show the documented MCP login flow.
- **A smoke test fails:** record the exact client version, plugin version, skill version, commit, smoke number, and redacted result; do not promote support.
- **Generated output drifts:** fail CI with the differing paths and require regeneration from canonical source.
- **A local plugin file is modified:** native client cache behavior governs replacement; the marketplace does not claim to preserve hand-edited cached packages.

## Verification strategy

### Canonical and generator contracts

- All existing catalog and skill tests continue to pass.
- Every catalog skill produces exactly one plugin.
- Generated skill directories are byte-for-byte copies of canonical skill directories.
- Codex and Claude manifests agree on identity, version, description, source, license, and included skill.
- Marketplace entries are unique, ordered deterministically, and resolve within the repository.
- Each manifest version agrees with `catalog/skills.json` and `SKILL.md` metadata.
- The core selection contains exactly the three catalog entries whose tier is `core`.
- Two generator runs from the same commit produce identical output.
- Generator check mode reports no diff after committed output is refreshed.

### Static-site checks

- Every catalog entry produces a reachable detail page.
- Search and every filter work without an API.
- Codex and Claude commands contain the correct repository, marketplace, and plugin IDs.
- The core-selection action produces exactly three native installs.
- Source, release, adapter, and smoke links resolve.
- Generated pages contain no forbidden tenant or credential fields.
- The site remains usable with JavaScript unavailable for basic browsing and installation instructions.
- Accessibility checks cover keyboard navigation, focus visibility, headings, labels, contrast, and reduced motion.

### Native client integration

From a clean test project in the exact target Codex and Claude Code versions:

1. Add the marketplace from the public GitHub repository.
2. Confirm that all nine plugins appear.
3. Install one individual plugin.
4. Install the three core plugins through the displayed convenience flow.
5. Confirm explicit namespaced invocation and automatic discovery.
6. Refresh the marketplace and update a deliberately older test version.
7. Disable and remove a plugin and confirm it is no longer active.
8. Verify and document the exact project-scope behavior for that client version.

Claude's native validator runs against the marketplace root and every generated plugin. Codex checks exercise marketplace add, list, plugin add, list, upgrade, and remove with automation-friendly JSON where available.

### Behavior and compatibility checks

For both clients, run the existing four release smokes against the exact generated plugin and skill versions:

1. Conditional search followed by full-content retrieval.
2. Generic negative trigger with no Stack Internal call.
3. Changed-payload reapproval and byte-for-byte approved write arguments.
4. Honest MCP failure reporting.

The resulting evidence follows the existing redacted evidence schemas and release-candidate commit rules.

## MVP acceptance criteria

The MVP is complete when:

- The public GitHub repository can be added as a marketplace by current Codex and Claude Code clients.
- Both clients list the same nine plugin IDs and versions.
- An individual skill can be installed without manually copying files.
- The core convenience flow installs the three core plugins without introducing a duplicate bundle plugin.
- A new user can browse the GitHub Pages catalog, select a client, install, connect their own Stack Internal tenant, and execute the guided smokes.
- Marketplace packages contain the exact canonical skill content and no tenant-specific material.
- Generated output, native manifests, static pages, and versions pass CI consistency checks.
- Installation, update, disablement, and removal work through native client mechanisms.
- Failed or missing tenant-backed smokes leave compatibility marked `experimental`.

## Rollout

1. Add the generator and generated dual-client plugin packages.
2. Add native marketplace manifests and contract tests.
3. Add native local-marketplace integration tests.
4. Add the static GitHub Pages site and build checks.
5. Test the marketplace from GitHub in clean Codex and Claude Code projects.
6. Run the four tenant-backed smokes for the release candidate.
7. Tag the release and deploy the public site from the same commit.

The first release advertises Codex and Claude Code marketplace installation while retaining the existing direct-filesystem adapters for troubleshooting and for clients outside this MVP.

## References

- [Codex developer commands](https://learn.chatgpt.com/docs/developer-commands)
- [Package plugins for Codex and ChatGPT](https://developers.openai.com/plugins/build/plugins)
- [Claude Code plugin marketplaces](https://code.claude.com/docs/en/plugin-marketplaces)
- [Create Claude Code plugins](https://code.claude.com/docs/en/plugins)
- [Agent Skills specification](https://agentskills.io/specification)
