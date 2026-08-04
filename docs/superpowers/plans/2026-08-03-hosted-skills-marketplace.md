# Hosted Stack Internal Skills Marketplace Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the public `EstoesMoises/stack-mcp-skills` repository into a native Codex and Claude Code plugin marketplace with a static GitHub Pages storefront.

**Architecture:** Keep `catalog/skills.json` and `skills/` canonical. A deterministic Python builder generates committed dual-client plugin packages and native marketplace manifests, while a separate post-commit site build creates an uncommitted `dist/` tree using an explicit source SHA. Codex and Claude Code perform installation, caching, upgrades, and removal through their native plugin marketplace commands.

**Tech Stack:** Python 3.11+, standard library, existing `jsonschema`/PyYAML/pytest/skills-ref development dependencies, vanilla HTML/CSS/JavaScript, GitHub Actions, GitHub Pages.

## Global Constraints

- The public repository, every skill, both marketplace manifests, and the GitHub Pages site are public.
- `catalog/skills.json` and the nine canonical directories under `skills/` remain the behavioral source of truth.
- Marketplace identifier: `stack-internal`.
- Public repository: `EstoesMoises/stack-mcp-skills`.
- Public site base URL: `https://estoesmoises.github.io/stack-mcp-skills/`.
- Generate exactly nine one-skill plugins; do not generate a tenth core-bundle plugin.
- Core convenience selection: `efficient-search`, `company-debugging`, and `capture-quality-qa`.
- A generated `plugins/<skill-id>/skills/<skill-id>/` tree must be byte-for-byte equal to its canonical skill directory.
- Generated Codex and Claude plugin versions must exactly match the catalog and `SKILL.md` metadata versions.
- Commit generated plugin wrappers and native marketplace manifests.
- Do not commit `dist/`; build it after the source commit exists and pass the exact 40-character commit SHA explicitly.
- Do not embed a build timestamp, random identifier, absolute path, tenant slug, credential, token, or customer content in generated output.
- The site is framework-free, has no backend, has no form that accepts a tenant value, and loads no third-party analytics or runtime assets.
- Plugins contain skills, README, license, and the two client manifests only; no hooks, executables, bundled MCP server, `.mcp.json`, or `.app.json`.
- All Stack Internal writes retain the canonical exact-payload approval gates.
- All adapter compatibility values remain `experimental` until the existing tenant-backed evidence gate passes for exact versions.
- Codex command-driven marketplace registration is client-managed; do not claim that it has a project-scope flag.
- Claude marketplace registration uses `--scope project`, and its interactive install flow instructs the user to choose project scope.
- Use only existing Python dependencies. Do not add a frontend package manager or template framework.
- Keep GitHub Actions pinned to full commit SHAs.
- Pages action pins resolved on 2026-08-03: `actions/configure-pages@983d7736d9b0ae728b81ab479565c72886d7745b`, `actions/upload-pages-artifact@7b1f4a764d45c48632c6b24a0339c27f5614fb0b`, and `actions/deploy-pages@d6db90164ac5ed86f2b6aed7e0febac5b3c0c03e`.

---

## File and responsibility map

### Canonical configuration

- `catalog/marketplace.json`: marketplace identity, version, repository, site URL, publisher, and category.
- `standards/marketplace-schema.json`: strict schema for `catalog/marketplace.json`.
- `src/stack_skill_catalog/marketplace_config.py`: typed loading and validation of marketplace configuration.

### Package generation

- `src/stack_skill_catalog/plugin_package.py`: build one dual-client plugin tree from one catalog entry.
- `src/stack_skill_catalog/marketplace_distribution.py`: build all nine plugins and both native marketplace manifests; compare expected and committed trees.
- `scripts/build_marketplace.py`: CLI for package write/check, site build, and version output.
- `.agents/plugins/marketplace.json`: committed generated Codex marketplace.
- `.claude-plugin/marketplace.json`: committed generated Claude Code marketplace.
- `plugins/<skill-id>/`: committed generated plugin for each of the exact nine catalog IDs.

### Static site

- `src/stack_skill_catalog/site.py`: normalized site model and deterministic HTML generation.
- `marketplace_web/styles.css`: local responsive and accessible presentation.
- `marketplace_web/app.js`: client-side search, filters, copy buttons, and client tabs.
- `dist/`: ignored, post-commit GitHub Pages artifact.

### Validation and tests

- `src/stack_skill_catalog/validation.py`: include marketplace config and committed-distribution validation.
- `tests/contract/test_marketplace_config.py`: config schema and model tests.
- `tests/contract/test_plugin_package.py`: single-plugin copy and manifest tests.
- `tests/contract/test_marketplace_distribution.py`: nine-plugin and native-manifest tests.
- `tests/contract/test_marketplace_site.py`: page completeness, deterministic output, security, and accessibility contracts.
- `tests/contract/test_marketplace_cli.py`: command modes, exit codes, and drift detection.
- `tests/contract/test_marketplace_docs.py`: public command and scope wording contracts.
- `tests/contract/test_pages_workflow.py`: pinned actions, permissions, triggers, and build/deploy contracts.

### Documentation and delivery

- `README.md`: public marketplace quickstart and browser link.
- `CONTRIBUTING.md`: canonical-only editing and regeneration workflow.
- `adapters/codex/README.md`: native Codex marketplace path first, filesystem copy fallback second.
- `adapters/claude-code/README.md`: native Claude Code marketplace path first, filesystem copy fallback second.
- `docs/marketplace-testing.md`: clean-client and tenant-backed marketplace test matrix.
- `docs/release-checklist.md`: generated-package, site, Pages, and native-client gates.
- `.github/workflows/validate.yml`: package drift and deterministic site checks on PRs and `main`.
- `.github/workflows/pages.yml`: build and deploy the post-commit static site.
- `.gitignore`: ignore `/dist/`.

---

### Task 1: Add the marketplace configuration contract

**Files:**
- Create: `catalog/marketplace.json`
- Create: `standards/marketplace-schema.json`
- Create: `src/stack_skill_catalog/marketplace_config.py`
- Create: `tests/contract/test_marketplace_config.py`
- Modify: `src/stack_skill_catalog/validation.py`
- Modify: `tests/contract/conftest.py`

**Interfaces:**
- Produces: `MarketplaceConfig` dataclass.
- Produces: `load_marketplace_config(path: Path) -> MarketplaceConfig`.
- Produces: `validate_marketplace(root: Path) -> list[str]` for repository orchestration.
- Consumes: existing JSON Schema dependency and stable error-sorting conventions.

- [ ] **Step 1: Write failing configuration tests**

```python
from pathlib import Path

import pytest

from stack_skill_catalog.marketplace_config import (
    MarketplaceConfig,
    load_marketplace_config,
    validate_marketplace,
)


ROOT = Path(__file__).parents[2]


def test_public_marketplace_config_loads_as_typed_value():
    config = load_marketplace_config(ROOT / "catalog/marketplace.json")

    assert config == MarketplaceConfig(
        schema_version="1.0.0",
        marketplace_version="0.1.0",
        name="stack-internal",
        display_name="Stack Internal Skills",
        repository="EstoesMoises/stack-mcp-skills",
        site_url="https://estoesmoises.github.io/stack-mcp-skills/",
        publisher_name="Stack Internal Skills",
        category="Productivity",
    )


def test_marketplace_schema_rejects_credentials(tmp_path):
    (tmp_path / "catalog").mkdir()
    (tmp_path / "standards").mkdir()
    (tmp_path / "standards/marketplace-schema.json").write_bytes(
        (ROOT / "standards/marketplace-schema.json").read_bytes()
    )
    config = (ROOT / "catalog/marketplace.json").read_text(encoding="utf-8")
    path = tmp_path / "catalog/marketplace.json"
    path.write_text(config[:-2] + ', "token": "secret"}\n', encoding="utf-8")

    with pytest.raises(ValueError, match="Additional properties"):
        load_marketplace_config(path)


def test_repository_validation_reports_missing_marketplace_config(repo_fixture):
    (repo_fixture.root / "catalog/marketplace.json").unlink()
    assert validate_marketplace(repo_fixture.root) == [
        "marketplace config could not be loaded: catalog/marketplace.json"
    ]
```

- [ ] **Step 2: Run the focused tests and confirm the module is missing**

Run: `uv run pytest tests/contract/test_marketplace_config.py -q`

Expected: FAIL during import with `ModuleNotFoundError: stack_skill_catalog.marketplace_config`.

- [ ] **Step 3: Add the strict schema and canonical config**

`catalog/marketplace.json`:

```json
{
  "schema_version": "1.0.0",
  "marketplace_version": "0.1.0",
  "name": "stack-internal",
  "display_name": "Stack Internal Skills",
  "repository": "EstoesMoises/stack-mcp-skills",
  "site_url": "https://estoesmoises.github.io/stack-mcp-skills/",
  "publisher_name": "Stack Internal Skills",
  "category": "Productivity"
}
```

`standards/marketplace-schema.json` must use JSON Schema 2020-12, set `additionalProperties` to `false`, require all eight fields, pin `schema_version` to `1.0.0`, validate both versions with `^\\d+\\.\\d+\\.\\d+$`, require marketplace name `^[a-z0-9]+(?:-[a-z0-9]+)*$`, require repository `^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$`, require an HTTPS `site_url` ending in `/`, and require non-empty publisher/category strings.

- [ ] **Step 4: Implement typed loading and stable errors**

```python
@dataclass(frozen=True)
class MarketplaceConfig:
    schema_version: str
    marketplace_version: str
    name: str
    display_name: str
    repository: str
    site_url: str
    publisher_name: str
    category: str


def load_marketplace_config(path: Path) -> MarketplaceConfig:
    value = json.loads(path.read_text(encoding="utf-8"))
    schema_path = path.parents[1] / "standards/marketplace-schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(value), key=lambda error: list(error.absolute_path))
    if errors:
        raise ValueError("; ".join(error.message for error in errors))
    return MarketplaceConfig(**value)


def validate_marketplace(root: Path) -> list[str]:
    try:
        load_marketplace_config(root / "catalog/marketplace.json")
    except (OSError, ValueError, json.JSONDecodeError) as error:
        return [f"marketplace config could not be loaded: {error}"]
    return []
```

Make the missing-file error deterministic by reporting the repository-relative path rather than the platform's absolute path. Wire `validate_marketplace(root)` into `validate_repository` before the final `sorted(set(errors))`.

Update `repo_fixture` to copy `standards/marketplace-schema.json` and write the same valid marketplace JSON shown above. This preserves the existing `test_valid_empty_catalog_passes` contract after marketplace validation becomes repository-wide.

- [ ] **Step 5: Run focused and repository validation tests**

Run: `uv run pytest tests/contract/test_marketplace_config.py tests/contract/test_catalog.py tests/contract/test_validation_cli.py -q`

Expected: PASS.

- [ ] **Step 6: Commit the configuration contract**

```bash
git add catalog/marketplace.json standards/marketplace-schema.json src/stack_skill_catalog/marketplace_config.py src/stack_skill_catalog/validation.py tests/contract/conftest.py tests/contract/test_marketplace_config.py
git commit -m "feat: define marketplace configuration"
```

---

### Task 2: Generate one safe dual-client plugin package

**Required implementation skill:** `plugin-creator` for the dual-manifest package structure, followed by the task's TDD cycle.

**Files:**
- Create: `src/stack_skill_catalog/plugin_package.py`
- Create: `tests/contract/test_plugin_package.py`

**Interfaces:**
- Consumes: `MarketplaceConfig` and one validated catalog entry.
- Produces: `build_codex_plugin_manifest(entry, config) -> dict[str, object]`.
- Produces: `build_claude_plugin_manifest(entry, config) -> dict[str, object]`.
- Produces: `build_plugin_package(root, entry, config, destination) -> Path`.
- Produces: `plugin_readme(entry, config) -> str`.

- [ ] **Step 1: Write failing package-copy and manifest tests**

```python
import json
from pathlib import Path

from stack_skill_catalog.catalog import load_catalog
from stack_skill_catalog.marketplace_config import load_marketplace_config
from stack_skill_catalog.plugin_package import build_plugin_package


ROOT = Path(__file__).parents[2]


def _files(path: Path) -> dict[str, bytes]:
    return {
        item.relative_to(path).as_posix(): item.read_bytes()
        for item in sorted(path.rglob("*"))
        if item.is_file()
    }


def test_plugin_contains_exact_canonical_skill_and_both_manifests(tmp_path):
    entry = load_catalog(ROOT / "catalog/skills.json")["skills"][0]
    config = load_marketplace_config(ROOT / "catalog/marketplace.json")

    plugin = build_plugin_package(ROOT, entry, config, tmp_path)

    canonical = ROOT / entry["path"]
    packaged = plugin / "skills" / entry["id"]
    assert _files(packaged) == _files(canonical)
    assert json.loads((plugin / ".codex-plugin/plugin.json").read_text())["version"] == entry["version"]
    assert json.loads((plugin / ".claude-plugin/plugin.json").read_text())["version"] == entry["version"]
    assert (plugin / "LICENSE").read_bytes() == (ROOT / "LICENSE").read_bytes()


def test_plugin_contains_no_executable_or_mcp_surface(tmp_path):
    entry = load_catalog(ROOT / "catalog/skills.json")["skills"][0]
    config = load_marketplace_config(ROOT / "catalog/marketplace.json")
    plugin = build_plugin_package(ROOT, entry, config, tmp_path)

    relative = {path.relative_to(plugin).as_posix() for path in plugin.rglob("*")}
    assert not {"hooks", ".mcp.json", ".app.json"} & relative
    codex = json.loads((plugin / ".codex-plugin/plugin.json").read_text())
    assert not {"hooks", "mcpServers", "apps"} & codex.keys()
```

- [ ] **Step 2: Run the focused tests and verify the missing implementation failure**

Run: `uv run pytest tests/contract/test_plugin_package.py -q`

Expected: FAIL during import with `ModuleNotFoundError: stack_skill_catalog.plugin_package`.

- [ ] **Step 3: Implement stable JSON and client manifests**

```python
def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_codex_plugin_manifest(entry: dict[str, object], config: MarketplaceConfig) -> dict[str, object]:
    write_actions = entry["write_actions"]
    return {
        "name": entry["id"],
        "version": entry["version"],
        "description": entry["summary"],
        "author": {"name": config.publisher_name},
        "homepage": f"{config.site_url}skills/{entry['id']}/",
        "repository": f"https://github.com/{config.repository}",
        "license": "Apache-2.0",
        "keywords": entry["tags"],
        "skills": "./skills/",
        "interface": {
            "displayName": entry["name"],
            "shortDescription": entry["summary"],
            "developerName": config.publisher_name,
            "category": config.category,
            "capabilities": ["Read"] if not write_actions else ["Read", "Approval-gated writes"],
            "websiteURL": f"{config.site_url}skills/{entry['id']}/",
        },
    }


def build_claude_plugin_manifest(entry: dict[str, object], config: MarketplaceConfig) -> dict[str, object]:
    return {
        "name": entry["id"],
        "version": entry["version"],
        "description": entry["summary"],
        "author": {"name": config.publisher_name},
        "homepage": f"{config.site_url}skills/{entry['id']}/",
        "repository": f"https://github.com/{config.repository}",
        "license": "Apache-2.0",
        "keywords": entry["tags"],
    }
```

- [ ] **Step 4: Implement safe package copying**

```python
def build_plugin_package(
    root: Path,
    entry: dict[str, object],
    config: MarketplaceConfig,
    destination: Path,
) -> Path:
    plugin_root = destination / str(entry["id"])
    source = root / str(entry["path"])
    for path in source.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"canonical skills may not contain symlinks: {path.relative_to(root)}")
    shutil.copytree(source, plugin_root / "skills" / str(entry["id"]), copy_function=shutil.copyfile)
    shutil.copyfile(root / "LICENSE", plugin_root / "LICENSE")
    _write_json(plugin_root / ".codex-plugin/plugin.json", build_codex_plugin_manifest(entry, config))
    _write_json(plugin_root / ".claude-plugin/plugin.json", build_claude_plugin_manifest(entry, config))
    (plugin_root / "README.md").write_text(plugin_readme(entry, config), encoding="utf-8")
    return plugin_root
```

`plugin_readme` must state the plugin and skill IDs, version, canonical source URL, required MCP tools, declared write actions, separate MCP/OAuth prerequisite, Codex invocation `$<plugin-id>:<skill-id>`, Claude invocation `/<plugin-id>:<skill-id>`, and experimental compatibility status. It must not include a tenant slug value.

- [ ] **Step 5: Add negative tests for symlinks and version mismatch**

Create a temporary canonical skill symlink and assert `ValueError` contains `may not contain symlinks`. Copy an entry and change its version away from `stack-internal-version` in `SKILL.md`; assert package generation refuses it with `catalog and skill versions differ` before writing any destination files.

- [ ] **Step 6: Run the focused tests**

Run: `uv run pytest tests/contract/test_plugin_package.py -q`

Expected: PASS.

- [ ] **Step 7: Commit the single-package generator**

```bash
git add src/stack_skill_catalog/plugin_package.py tests/contract/test_plugin_package.py
git commit -m "feat: generate dual-client skill plugins"
```

---

### Task 3: Generate the complete native marketplace distribution

**Files:**
- Create: `src/stack_skill_catalog/marketplace_distribution.py`
- Create: `scripts/build_marketplace.py`
- Create: `tests/contract/test_marketplace_distribution.py`
- Create: `tests/contract/test_marketplace_cli.py`
- Create: `.agents/plugins/marketplace.json` through the generator
- Create: `.claude-plugin/marketplace.json` through the generator
- Create: `plugins/.generated-marketplace` through the generator
- Create: generated `plugins/<skill-id>/` for all nine IDs

**Interfaces:**
- Consumes: `build_plugin_package`, `load_catalog`, and `load_marketplace_config`.
- Produces: `build_codex_marketplace(entries, config) -> dict[str, object]`.
- Produces: `build_claude_marketplace(entries, config) -> dict[str, object]`.
- Produces: `generate_distribution(root: Path, output_root: Path) -> None`.
- Produces: `distribution_diff(root: Path) -> list[str]` with `missing:`, `unexpected:`, and `changed:` messages.
- Produces: CLI `packages --mode write|check --root ROOT`.

- [ ] **Step 1: Write failing nine-plugin and marketplace tests**

```python
import json
from pathlib import Path

from stack_skill_catalog.catalog import load_catalog
from stack_skill_catalog.marketplace_distribution import generate_distribution


ROOT = Path(__file__).parents[2]


def test_distribution_contains_all_catalog_plugins_in_catalog_order(tmp_path):
    generate_distribution(ROOT, tmp_path)
    ids = [entry["id"] for entry in load_catalog(ROOT / "catalog/skills.json")["skills"]]

    assert {path.name for path in (tmp_path / "plugins").iterdir() if path.is_dir()} == set(ids)
    codex = json.loads((tmp_path / ".agents/plugins/marketplace.json").read_text())
    claude = json.loads((tmp_path / ".claude-plugin/marketplace.json").read_text())
    assert [entry["name"] for entry in codex["plugins"]] == ids
    assert [entry["name"] for entry in claude["plugins"]] == ids


def test_core_is_a_selection_not_a_generated_plugin(tmp_path):
    generate_distribution(ROOT, tmp_path)

    assert not (tmp_path / "plugins/core").exists()
    assert not (tmp_path / "plugins/stack-internal-core").exists()
```

- [ ] **Step 2: Run the tests and verify the module is missing**

Run: `uv run pytest tests/contract/test_marketplace_distribution.py -q`

Expected: FAIL during import with `ModuleNotFoundError: stack_skill_catalog.marketplace_distribution`.

- [ ] **Step 3: Implement the two marketplace manifest builders**

```python
def build_codex_marketplace(entries, config: MarketplaceConfig) -> dict[str, object]:
    return {
        "name": config.name,
        "interface": {"displayName": config.display_name},
        "plugins": [
            {
                "name": entry["id"],
                "source": {"source": "local", "path": f"./plugins/{entry['id']}"},
                "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                "category": config.category,
            }
            for entry in entries
        ],
    }


def build_claude_marketplace(entries, config: MarketplaceConfig) -> dict[str, object]:
    return {
        "name": config.name,
        "description": "Public Stack Internal Agent Skills for company-grounded coding workflows.",
        "owner": {"name": config.publisher_name},
        "plugins": [
            {
                "name": entry["id"],
                "source": f"./plugins/{entry['id']}",
                "description": entry["summary"],
                "version": entry["version"],
                "author": {"name": config.publisher_name},
            }
            for entry in entries
        ],
    }
```

Generate entries in catalog order. Before building, reject duplicate IDs, IDs that do not equal the final segment of `path`, and a catalog whose tier counts differ from three core and six extended.

- [ ] **Step 4: Implement isolated generation and tree comparison**

`generate_distribution` writes only inside the supplied output root. It creates the marker `plugins/.generated-marketplace` containing `generated; edit catalog/skills.json or skills/ instead\n`, builds all plugin packages, and writes both native manifests with sorted JSON keys and a trailing newline.

`distribution_diff(root)` generates expected output in `TemporaryDirectory`, compares these exact committed surfaces, and returns sorted messages:

```python
SURFACES = (
    Path("plugins"),
    Path(".agents/plugins/marketplace.json"),
    Path(".claude-plugin/marketplace.json"),
)
```

Compare bytes, not parsed JSON. Include unexpected files under `plugins/` so stale packages cannot survive a rename.

- [ ] **Step 5: Implement safe package write/check CLI modes**

```python
def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = args.root.resolve()
    if args.command == "packages" and args.mode == "check":
        differences = distribution_diff(root)
        print(json.dumps({"differences": differences, "valid": not differences}, sort_keys=True))
        return 0 if not differences else 1
    if args.command == "packages" and args.mode == "write":
        write_distribution(root)
        print(json.dumps({"generated": True, "root": str(root)}, sort_keys=True))
        return 0
    parser.error("unsupported command")
```

`write_distribution` must refuse to replace an existing `plugins/` directory unless `plugins/.generated-marketplace` exists with the exact marker content. Generate into a sibling temporary directory, then replace only `plugins/` and the two manifest files. Do not remove `.agents/` or `.claude-plugin/` wholesale.

- [ ] **Step 6: Add drift and destructive-safety tests**

Test these exact cases in `tests/contract/test_marketplace_cli.py`:

- `packages --mode check` returns 1 and JSON containing `missing:` before generation.
- `packages --mode write` creates all surfaces and returns 0.
- A second check returns `{"differences": [], "valid": true}`.
- Editing one generated byte produces `changed:`.
- Adding `plugins/stale/file.txt` produces `unexpected:`.
- An unmarked existing `plugins/keep-me.txt` makes write mode return 1 and leaves the file unchanged.

- [ ] **Step 7: Generate and inspect the committed marketplace packages**

Run:

```bash
uv run python scripts/build_marketplace.py packages --mode write --root .
uv run python scripts/build_marketplace.py packages --mode check --root .
uv run pytest tests/contract/test_plugin_package.py tests/contract/test_marketplace_distribution.py tests/contract/test_marketplace_cli.py -q
```

Expected: check JSON is `{"differences": [], "valid": true}` and tests PASS.

- [ ] **Step 8: Commit the native marketplace**

```bash
git add src/stack_skill_catalog/marketplace_distribution.py scripts/build_marketplace.py tests/contract/test_marketplace_distribution.py tests/contract/test_marketplace_cli.py .agents/plugins/marketplace.json .claude-plugin/marketplace.json plugins
git commit -m "feat: add native skill marketplaces"
```

---

### Task 4: Build the deterministic static marketplace site

**Required implementation skill:** `impeccable` for the frontend interaction and accessibility review, followed by the task's TDD cycle.

**Files:**
- Create: `src/stack_skill_catalog/site.py`
- Create: `marketplace_web/styles.css`
- Create: `marketplace_web/app.js`
- Create: `tests/contract/test_marketplace_site.py`

**Interfaces:**
- Consumes: canonical catalog, marketplace config, canonical skill frontmatter, and explicit source commit.
- Produces: `build_site_model(root: Path, source_commit: str) -> dict[str, object]`.
- Produces: `write_site(root: Path, output_root: Path, source_commit: str) -> None`.
- Produces: generated `index.html`, `skills/<id>/index.html`, `catalog.json`, `assets/styles.css`, and `assets/app.js`.

- [ ] **Step 1: Write failing site-model and output tests**

```python
import json
from pathlib import Path

from stack_skill_catalog.site import build_site_model, write_site


ROOT = Path(__file__).parents[2]
SHA = "a" * 40


def test_site_model_has_nine_skills_and_exact_core_selection():
    model = build_site_model(ROOT, SHA)

    assert model["source_commit"] == SHA
    assert len(model["skills"]) == 9
    assert model["core_skill_ids"] == [
        "efficient-search", "company-debugging", "capture-quality-qa"
    ]


def test_site_build_is_byte_deterministic(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    write_site(ROOT, first, SHA)
    write_site(ROOT, second, SHA)

    files = lambda root: {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*")) if path.is_file()
    }
    assert files(first) == files(second)


def test_every_skill_page_has_native_commands_and_smokes(tmp_path):
    write_site(ROOT, tmp_path / "dist", SHA)
    for entry in json.loads((ROOT / "catalog/skills.json").read_text())["skills"]:
        body = (tmp_path / "dist/skills" / entry["id"] / "index.html").read_text()
        assert f"codex plugin add {entry['id']}@stack-internal" in body
        assert f"/plugin install {entry['id']}@stack-internal" in body
        assert "How should I structure logging in this service?" in body
        assert "Write a Python function that reverses a string." in body
```

- [ ] **Step 2: Run the tests and verify the site module is missing**

Run: `uv run pytest tests/contract/test_marketplace_site.py -q`

Expected: FAIL during import with `ModuleNotFoundError: stack_skill_catalog.site`.

- [ ] **Step 3: Implement the normalized site model**

```python
def build_site_model(root: Path, source_commit: str) -> dict[str, object]:
    if not re.fullmatch(r"[0-9a-f]{40}", source_commit):
        raise ValueError("source commit must be a lowercase 40-character Git SHA")
    config = load_marketplace_config(root / "catalog/marketplace.json")
    catalog = load_catalog(root / "catalog/skills.json")
    skills = []
    for entry in catalog["skills"]:
        metadata, _ = load_frontmatter(root / entry["path"])
        skills.append({
            **entry,
            "description": metadata["description"],
            "write_capable": bool(entry["write_actions"]),
            "source_url": f"https://github.com/{config.repository}/tree/{source_commit}/{entry['path']}",
            "site_url": f"{config.site_url}skills/{entry['id']}/",
            "codex_install": f"codex plugin add {entry['id']}@{config.name}",
            "claude_install": f"/plugin install {entry['id']}@{config.name}",
            "codex_invoke": f"${entry['id']}:{entry['id']}",
            "claude_invoke": f"/{entry['id']}:{entry['id']}",
            "codex_project_manifest": json.dumps({
                "name": config.name,
                "interface": {"displayName": config.display_name},
                "plugins": [{
                    "name": entry["id"],
                    "source": {
                        "source": "git-subdir",
                        "url": f"https://github.com/{config.repository}.git",
                        "path": f"./plugins/{entry['id']}",
                        "ref": "main",
                    },
                    "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                    "category": config.category,
                }],
            }, indent=2, sort_keys=True),
        })
    return {
        "marketplace": asdict(config),
        "source_commit": source_commit,
        "core_skill_ids": [entry["id"] for entry in catalog["skills"] if entry["tier"] == "core"],
        "skills": skills,
        "smokes": SMOKE_TESTS,
    }
```

Define `SMOKE_TESTS` as immutable dictionaries for the four existing release smokes: conditional search/full retrieval, generic no-call, exact write approval, and honest MCP failure. Use the exact public positive and negative prompts already present in `README.md`; the write smoke must say to use a verified non-sensitive resolution and a non-production result.

- [ ] **Step 4: Implement semantic HTML rendering**

Use `html.escape` on every catalog- or frontmatter-derived value. The index must contain a skip link, one `h1`, a labeled search input, fieldsets for tier/client/write filters, a core-install section, and skill cards with `data-tier`, `data-tags`, `data-clients`, and `data-write-capable` attributes.

Each skill page must contain one `h1` and sections headed Purpose, Requirements, Safety, Install in Codex, Install in Claude Code, Connect Stack Internal MCP, Try it, Troubleshooting, Compatibility, and Source. Troubleshooting must distinguish: missing plugin commands, marketplace Git/policy failures, plugin-not-found refresh, installed-but-undiscovered reload, and separate MCP/OAuth failure. The Codex section must distinguish the client-managed quick command from a copyable repo-scoped `.agents/plugins/marketplace.json` block rendered from `codex_project_manifest`; it must not attach `--scope project` to a Codex command. Include this CSP without external origins:

```html
<meta http-equiv="Content-Security-Policy"
      content="default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'self'; form-action 'none'">
```

Render navigation and asset links relative to the page depth. Always include readable install instructions in HTML so the no-JavaScript path remains usable.

- [ ] **Step 5: Add accessible local CSS and behavior**

`marketplace_web/styles.css` must define local system-font stacks, visible `:focus-visible`, at least 44px interactive targets, responsive single-column behavior below 720px, readable light/dark color schemes, and `prefers-reduced-motion: reduce`. It must not contain `@import` or remote URLs.

`marketplace_web/app.js` must:

```javascript
const normalize = (value) => value.toLocaleLowerCase().trim();

function applyFilters() {
  const query = normalize(document.querySelector("#skill-search")?.value ?? "");
  document.querySelectorAll("[data-skill-card]").forEach((card) => {
    const matchesText = normalize(card.textContent).includes(query);
    const matchesTier = selected("tier", card.dataset.tier);
    const matchesClient = selected("client", card.dataset.clients);
    const matchesWrite = selected("write", card.dataset.writeCapable);
    card.hidden = !(matchesText && matchesTier && matchesClient && matchesWrite);
  });
}
```

Implement `selected` so an empty checkbox group means all values. Add copy buttons with an `aria-live="polite"` status. Add client tabs using buttons, `aria-selected`, `aria-controls`, and keyboard Left/Right navigation. No script may send network requests.

- [ ] **Step 6: Add security, accessibility, and completeness assertions**

Extend `test_marketplace_site.py` to assert:

- `catalog.json` equals the normalized model and contains the explicit SHA but no clock-shaped field.
- All nine skill page paths exist.
- Every write-capable page lists its exact `write_actions`; every read-only page says `Read-only`.
- `[tenant-slug]` appears only in displayed local MCP commands.
- No generated file contains `http://`, `<form`, `fetch(`, `XMLHttpRequest`, `analytics`, or an absolute local path.
- HTML includes the CSP, skip link, labels, and focusable controls.
- Every skill page includes all five named troubleshooting states and never recommends bypassing managed marketplace policy.
- CSS contains `:focus-visible` and `prefers-reduced-motion` and contains no `@import`.
- The index's core install commands contain exactly three plugin add/install operations.
- Every Codex page contains one valid repo-scoped manifest with a `git-subdir` source for that page's plugin and no other plugin.

- [ ] **Step 7: Run focused site tests**

Run: `uv run pytest tests/contract/test_marketplace_site.py -q`

Expected: PASS.

- [ ] **Step 8: Commit the static site generator**

```bash
git add src/stack_skill_catalog/site.py marketplace_web/styles.css marketplace_web/app.js tests/contract/test_marketplace_site.py
git commit -m "feat: generate static skills marketplace"
```

---

### Task 5: Complete the build CLI and deterministic checks

**Files:**
- Modify: `scripts/build_marketplace.py`
- Modify: `tests/contract/test_marketplace_cli.py`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: `write_site` and marketplace configuration.
- Produces: CLI `site --root ROOT --output OUTPUT --source-commit SHA`.
- Produces: CLI `version --root ROOT` printing only the marketplace version.

- [ ] **Step 1: Write failing CLI tests for site and version modes**

```python
def test_site_command_requires_explicit_commit(tmp_path, capsys):
    with pytest.raises(SystemExit) as error:
        main(["site", "--root", str(ROOT), "--output", str(tmp_path)])
    assert error.value.code == 2
    assert "--source-commit" in capsys.readouterr().err


def test_site_command_builds_dist_from_explicit_commit(tmp_path):
    output = tmp_path / "dist"
    assert main([
        "site", "--root", str(ROOT), "--output", str(output),
        "--source-commit", "b" * 40,
    ]) == 0
    assert (output / "index.html").is_file()


def test_version_command_prints_only_semver(capsys):
    assert main(["version", "--root", str(ROOT)]) == 0
    assert capsys.readouterr().out == "0.1.0\n"
```

- [ ] **Step 2: Run the focused tests and confirm missing subcommands**

Run: `uv run pytest tests/contract/test_marketplace_cli.py -q`

Expected: FAIL because `site` and `version` are not accepted commands.

- [ ] **Step 3: Add site and version subcommands**

The `site` command must resolve `--root` and `--output`, reject an output equal to or above the repository root, remove only the exact output directory after validating that boundary, call `write_site`, and emit stable JSON:

```json
{"output": "dist", "source_commit": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", "valid": true}
```

Represent `output` relative to the repository when it is inside the repository; never print an absolute path. The `version` command prints the raw semantic version followed by one newline so workflows can compose it.

- [ ] **Step 4: Add output-boundary and determinism tests**

Assert the site command refuses `--output .`, `--output ..`, and the repository root without deleting anything. Build twice into two temporary outputs with the same SHA and assert identical relative paths and bytes. Build with a different SHA and assert only `catalog.json` plus source/release links in HTML differ.

- [ ] **Step 5: Ignore only the root Pages output**

Add this exact line to `.gitignore`:

```gitignore
/dist/
```

Do not ignore `plugins/`, `.agents/plugins/marketplace.json`, or `.claude-plugin/marketplace.json`.

- [ ] **Step 6: Run all generator checks**

```bash
uv run pytest tests/contract/test_marketplace_config.py tests/contract/test_plugin_package.py tests/contract/test_marketplace_distribution.py tests/contract/test_marketplace_site.py tests/contract/test_marketplace_cli.py -q
uv run python scripts/build_marketplace.py packages --mode check --root .
uv run python scripts/build_marketplace.py site --root . --output dist --source-commit "$(git rev-parse HEAD)"
```

Expected: all tests PASS, package check is valid, and `dist/index.html` exists while `git status --short` does not show `dist/`.

- [ ] **Step 7: Commit the complete build interface**

```bash
git add scripts/build_marketplace.py tests/contract/test_marketplace_cli.py .gitignore
git commit -m "feat: add marketplace build commands"
```

---

### Task 6: Document native installation and contributor workflows

**Files:**
- Create: `docs/marketplace-testing.md`
- Create: `tests/contract/test_marketplace_docs.py`
- Modify: `README.md`
- Modify: `CONTRIBUTING.md`
- Modify: `adapters/codex/README.md`
- Modify: `adapters/claude-code/README.md`
- Modify: `docs/release-checklist.md`

**Interfaces:**
- Consumes: marketplace name, public repository, generated plugin IDs, native commands, and four existing smoke contracts.
- Produces: one public quickstart and one exact clean-client test matrix.

- [ ] **Step 1: Write failing documentation contract tests**

```python
from pathlib import Path


ROOT = Path(__file__).parents[2]


def test_readme_has_native_marketplace_quickstart():
    body = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "codex plugin marketplace add EstoesMoises/stack-mcp-skills" in body
    assert "codex plugin add efficient-search@stack-internal" in body
    assert "claude plugin marketplace add EstoesMoises/stack-mcp-skills --scope project" in body
    assert "/plugin install efficient-search@stack-internal" in body


def test_codex_docs_do_not_claim_a_project_scope_flag():
    body = (ROOT / "adapters/codex/README.md").read_text(encoding="utf-8").lower()
    assert "client-managed" in body
    assert "codex plugin marketplace add" in body
    assert "codex plugin marketplace add" not in "\n".join(
        line for line in body.splitlines() if "--scope project" in line
    )


def test_contributing_marks_generated_surfaces():
    body = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
    assert "Do not edit `plugins/`" in body
    assert "packages --mode write" in body
    assert "packages --mode check" in body
```

- [ ] **Step 2: Run the tests and confirm missing marketplace documentation**

Run: `uv run pytest tests/contract/test_marketplace_docs.py -q`

Expected: FAIL on the first missing native command.

- [ ] **Step 3: Rewrite the README quickstart around the public marketplace**

Add a `## Install from the public marketplace` section before the filesystem quickstart. Include:

```bash
codex plugin marketplace add EstoesMoises/stack-mcp-skills
codex plugin add efficient-search@stack-internal
```

and:

```bash
claude plugin marketplace add EstoesMoises/stack-mcp-skills --scope project
```

followed by:

```text
/plugin install efficient-search@stack-internal
/reload-plugins
```

Link the GitHub Pages catalog, explain that the core action installs three independent plugins, retain direct filesystem copying as a fallback, and remove the old statement that a hosted marketplace is beyond v1.

- [ ] **Step 4: Update client adapters without weakening existing smoke text**

Codex order: native marketplace add, native plugin add, list verification, namespaced invocation, client-managed scope caveat, repo-scoped manifest option, MCP setup, four existing smokes, filesystem fallback.

Claude order: project-scoped marketplace add, interactive project-scope install, reload, namespaced invocation, MCP setup, four existing smokes, filesystem fallback.

Preserve every phrase required by `test_adapter_write_smoke_is_deterministic_multiturn`, including `verified non-sensitive resolution`, `byte-for-byte`, changed action/payload, fresh approval, unchanged payload, and non-production result.

- [ ] **Step 5: Document canonical editing and marketplace testing**

In `CONTRIBUTING.md`, state that contributors edit `catalog/skills.json`, `catalog/marketplace.json`, and canonical `skills/`; `plugins/` and native manifests are generated. Document package write/check commands, site build with explicit `git rev-parse HEAD`, and the semantic-version bump rule.

In `docs/marketplace-testing.md`, provide a table with columns: Client, exact client version, marketplace add, plugin list, individual install, core install, explicit invocation, update, disable/remove, project-scope observation, smoke 1-4, result, reviewer. State that raw tenant data is forbidden and use the fixed tenant purpose `non-production skill validation`.

- [ ] **Step 6: Extend the release checklist**

Add these automated gates verbatim:

```bash
uv run python scripts/build_marketplace.py packages --mode check --root .
uv run python scripts/build_marketplace.py site --root . --output dist-a --source-commit "$(git rev-parse HEAD)"
uv run python scripts/build_marketplace.py site --root . --output dist-b --source-commit "$(git rev-parse HEAD)"
diff -ru dist-a dist-b
```

Add manual gates for the native marketplace add/list/install/update/remove paths, project-scope observation, GitHub Pages navigation, and all four tenant-backed smokes for exact Codex and Claude versions.

- [ ] **Step 7: Run documentation and existing adapter tests**

Run: `uv run pytest tests/contract/test_marketplace_docs.py tests/contract/test_adapters.py tests/contract/test_release_workflow.py -q`

Expected: PASS.

- [ ] **Step 8: Commit the public documentation**

```bash
git add README.md CONTRIBUTING.md adapters/codex/README.md adapters/claude-code/README.md docs/marketplace-testing.md docs/release-checklist.md tests/contract/test_marketplace_docs.py
git commit -m "docs: add marketplace installation workflow"
```

---

### Task 7: Add CI drift checks and GitHub Pages deployment

**Files:**
- Create: `.github/workflows/pages.yml`
- Create: `tests/contract/test_pages_workflow.py`
- Modify: `.github/workflows/validate.yml`
- Modify: `tests/contract/test_release_workflow.py`

**Interfaces:**
- Consumes: build CLI package check and site command.
- Produces: PR/main validation for generated drift and deterministic site output.
- Produces: Pages deployment from the exact pushed `main` commit.

- [ ] **Step 1: Write failing workflow contract tests**

```python
import re
from pathlib import Path

import yaml


ROOT = Path(__file__).parents[2]


def test_pages_workflow_uses_pinned_actions_and_minimal_permissions():
    text = (ROOT / ".github/workflows/pages.yml").read_text(encoding="utf-8")
    workflow = yaml.safe_load(text)
    uses = [
        step["uses"]
        for job in workflow["jobs"].values()
        for step in job.get("steps", [])
        if "uses" in step
    ]
    assert "actions/configure-pages@983d7736d9b0ae728b81ab479565c72886d7745b" in uses
    assert "actions/upload-pages-artifact@7b1f4a764d45c48632c6b24a0339c27f5614fb0b" in uses
    assert "actions/deploy-pages@d6db90164ac5ed86f2b6aed7e0febac5b3c0c03e" in uses
    assert all(re.search(r"@[0-9a-f]{40}$", action) for action in uses)
    assert workflow["permissions"] == {"contents": "read", "pages": "write", "id-token": "write"}


def test_validation_checks_packages_and_repeatable_site_builds():
    text = (ROOT / ".github/workflows/validate.yml").read_text(encoding="utf-8")
    assert "packages --mode check --root ." in text
    assert text.count("scripts/build_marketplace.py site") == 2
    assert "diff -ru dist-a dist-b" in text
```

- [ ] **Step 2: Run workflow tests and verify the missing Pages workflow failure**

Run: `uv run pytest tests/contract/test_pages_workflow.py -q`

Expected: FAIL with `FileNotFoundError: .github/workflows/pages.yml`.

- [ ] **Step 3: Extend validation without changing its least-privilege permissions**

After existing catalog validation steps, add:

```yaml
      - run: uv run python scripts/build_marketplace.py packages --mode check --root .
      - run: uv run python scripts/build_marketplace.py site --root . --output dist-a --source-commit "$GITHUB_SHA"
      - run: uv run python scripts/build_marketplace.py site --root . --output dist-b --source-commit "$GITHUB_SHA"
      - run: diff -ru dist-a dist-b
```

Keep `permissions: contents: read`, the existing pinned checkout/setup-uv actions, PR trigger, and `main` push trigger.

- [ ] **Step 4: Add the pinned Pages workflow**

`.github/workflows/pages.yml` must:

- Trigger on pushes to `main` and `workflow_dispatch`.
- Set top-level permissions exactly to contents read, Pages write, and ID token write.
- Use a `pages` concurrency group with `cancel-in-progress: false`.
- Build in a `build` job using the repository's pinned checkout and setup-uv actions.
- Run locked dependency sync, full tests, catalog validation, package check, and one site build with `--source-commit "$GITHUB_SHA"`.
- Configure Pages with the pinned configure-pages SHA.
- Upload `dist/` with the pinned upload-pages-artifact SHA.
- Deploy in a separate `deploy` job with `environment.name: github-pages` and the pinned deploy-pages SHA.

The build command must be:

```yaml
      - run: uv run python scripts/build_marketplace.py site --root . --output dist --source-commit "$GITHUB_SHA"
```

- [ ] **Step 5: Extend release workflow tests**

Add the marketplace package check and both deterministic site commands to `REQUIRED_AUTOMATED_COMMANDS` in `test_release_workflow.py`. Add assertions that the release checklist mentions GitHub Pages URL review, exact source commit, nine plugin entries, and both native clients.

- [ ] **Step 6: Run workflow and release tests**

Run: `uv run pytest tests/contract/test_pages_workflow.py tests/contract/test_release_workflow.py -q`

Expected: PASS.

- [ ] **Step 7: Run the complete automated gate locally**

```bash
uv sync --locked --dev
uv run pytest -q
uv run python scripts/validate_catalog.py .
uv run python scripts/build_marketplace.py packages --mode check --root .
uv run python scripts/build_marketplace.py site --root . --output dist-a --source-commit "$(git rev-parse HEAD)"
uv run python scripts/build_marketplace.py site --root . --output dist-b --source-commit "$(git rev-parse HEAD)"
diff -ru dist-a dist-b
```

Expected: all commands exit 0; pytest reports zero failures; catalog JSON reports `{"errors": [], "valid": true}`; package JSON reports `{"differences": [], "valid": true}`; diff emits no output.

- [ ] **Step 8: Commit CI and Pages delivery**

```bash
git add .github/workflows/validate.yml .github/workflows/pages.yml tests/contract/test_pages_workflow.py tests/contract/test_release_workflow.py
git commit -m "ci: publish skills marketplace pages"
```

---

### Task 8: Rehearse native clients and seal the MVP release evidence

**Files:**
- Modify: `docs/marketplace-testing.md`
- Modify: `docs/release-checklist.md`
- Create when live tests run: `compatibility/smoke-evidence/<adapter>-<skill-id>-<version>-<number>.json`
- Modify when live tests pass: `compatibility/evidence.json`

**Interfaces:**
- Consumes: exact release-candidate commit, generated marketplace, native clients, authorized non-production Stack Internal tenant, and existing evidence schemas.
- Produces: redacted smoke artifacts and evidence records tied to the exact release candidate.

- [ ] **Step 1: Create an exact release-candidate commit and record versions**

Run:

```bash
git status --short
git rev-parse HEAD
uv run python scripts/build_marketplace.py version --root .
codex --version
claude --version
```

Expected: clean status; one 40-character commit; marketplace version `0.1.0`; exact client versions captured in `docs/marketplace-testing.md`.

- [ ] **Step 2: Validate the marketplace with both native clients before tenant access**

Run Claude's native validator against the root and each plugin:

```bash
claude plugin validate .
for plugin in plugins/*; do claude plugin validate "$plugin"; done
```

For Codex, add the local marketplace in an isolated test profile, list available plugins as JSON, install `efficient-search`, confirm its installed version, then remove it. Use a temporary `CODEX_HOME` dedicated to this test so personal plugin state is not changed. Record commands and redacted results in `docs/marketplace-testing.md`.

Expected: nine available plugins, `efficient-search` version `0.1.0`, and no plugin remaining after removal.

- [ ] **Step 3: Test the public GitHub source in clean projects**

Codex:

```bash
codex plugin marketplace add EstoesMoises/stack-mcp-skills
codex plugin list --available --json
codex plugin add efficient-search@stack-internal --json
```

Claude Code:

```bash
claude plugin marketplace add EstoesMoises/stack-mcp-skills --scope project
claude plugin install efficient-search@stack-internal
```

Expected: both clients resolve the `stack-internal` marketplace and install the same plugin version. If the release candidate is not on public `main` yet, use the documented local marketplace path for this rehearsal and repeat the GitHub-source portion after publication.

- [ ] **Step 4: Verify the core convenience flow and lifecycle**

Install `efficient-search`, `company-debugging`, and `capture-quality-qa` individually in each client. Confirm discovery and namespaced invocation. Refresh the marketplace, update, disable, and remove each plugin using native commands. Record project-scope behavior separately for Codex and Claude; do not claim a Codex project-scope flag.

- [ ] **Step 5: Run all four tenant-backed smokes for both clients**

Using the fixed tenant purpose `non-production skill validation`, run:

1. Internal logging question: observe `search`, full retrieval, title, and content ID.
2. Generic Python reverse-string question: observe no Stack Internal call.
3. Verified non-sensitive write scenario: observe duplicate search, valid tags, exact displayed payload/action, changed-payload reapproval, byte-for-byte approved arguments, and only a non-production result.
4. Disconnected/denied MCP scenario: observe an honest access failure and clearly labeled general-knowledge fallback offer.

Do not store raw retrieved content, tenant identifiers, slugs, credentials, tokens, personal data, or customer data.

- [ ] **Step 6: Commit schema-valid redacted smoke artifacts without changing the evidence registry**

Each artifact contains only:

```json
{
  "schema_version": "1.0.0",
  "adapter": "codex",
  "smoke_test": 1,
  "passed": true,
  "redacted": true,
  "check_id": "conditional-search-and-full-retrieval"
}
```

Use the existing fixed check ID for each smoke number. Review the files, leave `compatibility/evidence.json` unchanged, and commit only the artifacts:

```bash
git add compatibility/smoke-evidence
git commit -m "test: add marketplace smoke artifacts"
git rev-parse HEAD
```

The resulting commit is the evidence-bearing candidate. This intermediate commit is necessary because the existing validator requires every referenced artifact to exist byte-for-byte in the release-candidate commit.

- [ ] **Step 7: Re-run the live smokes on the evidence-bearing candidate and add records**

Run all four live smokes again on the new exact commit from Step 6. Confirm the committed redacted artifacts still describe the observed pass/fail results. Only then set `compatibility/evidence.json.release_candidate_commit` and every new record's `catalog_commit` to that Step 6 commit. Add one record per tested adapter and skill version only when all four referenced artifacts are present and accurate.

Record exact client versions and redacted outcomes in `docs/marketplace-testing.md`, then validate the uncommitted registry against the candidate:

```bash
uv run pytest -q
uv run python scripts/validate_catalog.py .
uv run python scripts/build_marketplace.py packages --mode check --root .
for skill in skills/core/* skills/extended/*; do uv run skills-ref validate "$skill"; done
for plugin in plugins/*; do claude plugin validate "$plugin"; done
```

Expected: every command exits 0 and the validator confirms that the Step 6 candidate is an ancestor containing each referenced artifact exactly. If any native or tenant-backed test fails, record the limitation and keep the associated adapters `experimental`.

- [ ] **Step 8: Commit the reviewed evidence registry and test matrix**

```bash
git add compatibility/evidence.json docs/marketplace-testing.md docs/release-checklist.md
git commit -m "test: record marketplace compatibility evidence"
```

Re-run `uv run python scripts/validate_catalog.py .` after the commit and require exit 0. Do not create either evidence commit when no live tenant test was run; instead leave the empty evidence registry valid and document the outstanding manual gate in the release checklist.

---

## Final verification and release handoff

- [ ] Run the complete automated gate from Task 7 on the final commit.
- [ ] Run `git diff origin/main...HEAD --check` and inspect `git diff --stat origin/main...HEAD`.
- [ ] Confirm `git status --short` is empty.
- [ ] Confirm `plugins/` contains exactly nine generated plugin directories plus `.generated-marketplace`.
- [ ] Confirm both native marketplace manifests list the same nine IDs and exact versions.
- [ ] Confirm `dist/` is ignored and reproducible but absent from the commit.
- [ ] Confirm Pages deploys from the same commit shown on every generated skill page.
- [ ] Confirm missing live evidence leaves compatibility `experimental`.
- [ ] Tag the approved marketplace version only after all required release gates pass.
