"""Deterministic static-site generation for the public skills marketplace."""

from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
from dataclasses import asdict
from html import escape
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

from .catalog import load_catalog
from .marketplace_config import load_marketplace_config
from .skill import load_frontmatter


_SHA_PATTERN = re.compile(r"[0-9a-f]{40}")
_CSP = (
    "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
    "object-src 'none'; base-uri 'self'; form-action 'none'"
)
_DIRECTION_CONTRACT = """<!--
THESIS: Release Field Manual makes public skill installation read like an auditable technical guide and refuses the generic SaaS grid of interchangeable soft cards.
OWN-WORLD: Cool paper and navy ink use ruled dividers, squared index tabs, registration blue for action, and amber only for approval-gated write capability.
STORY: Understand native public installation, scan the nine-skill ledger, open one record, install it for a chosen client, connect MCP separately, and run observable smokes.
FIRST VIEWPORT: The title and product truth share the opening field with a visible three-plugin core-install ledger; filter controls and the first directory rows begin immediately below.
FORM: Release Field Manual, grounded candidate 5, seed 6d37fffd.
FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, and DESIGN.md
-->"""

SMOKE_TESTS: tuple[Mapping[str, str], ...] = (
    MappingProxyType(
        {
            "id": "conditional-search",
            "name": "Conditional search and full retrieval",
            "prompt": "How should I structure logging in this service?",
            "expected": (
                "Expect search, then full-content retrieval for a promising result, "
                "with the source title and content ID."
            ),
        }
    ),
    MappingProxyType(
        {
            "id": "negative-trigger",
            "name": "Generic request makes no internal call",
            "prompt": "Write a Python function that reverses a string.",
            "expected": "Expect no Stack Internal MCP call.",
        }
    ),
    MappingProxyType(
        {
            "id": "write-approval",
            "name": "Exact write approval",
            "prompt": (
                "Use a verified non-sensitive resolution in a deterministic multi-turn test. "
                "Ask to publish it, request a payload or action change, then approve the unchanged payload."
            ),
            "expected": (
                "Expect duplicate search, valid tags, exact displayed action and payload, no write after a "
                "change without fresh approval, byte-for-byte approved arguments, and only a non-production result."
            ),
        }
    ),
    MappingProxyType(
        {
            "id": "mcp-failure",
            "name": "Honest MCP failure",
            "prompt": "Disconnect or deny access, then ask an internal-policy question.",
            "expected": (
                "Expect an honest access failure and an offer to continue with clearly labeled general knowledge."
            ),
        }
    ),
)


def _json_text(value: object) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _script_json(value: object) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False).replace("<", "\\u003c").replace(
        ">", "\\u003e"
    ).replace("&", "\\u0026")


def build_site_model(root: Path, source_commit: str) -> dict[str, object]:
    """Return the normalized, JSON-serializable model for a source commit."""
    if _SHA_PATTERN.fullmatch(source_commit) is None:
        raise ValueError("source commit must be a lowercase 40-character Git SHA")

    root = Path(root)
    config = load_marketplace_config(root / "catalog" / "marketplace.json")
    catalog = load_catalog(root / "catalog" / "skills.json")
    catalog_skills = catalog.get("skills")
    if not isinstance(catalog_skills, list):
        raise ValueError("catalog skills must be a list")

    skills: list[dict[str, object]] = []
    for raw_entry in catalog_skills:
        if not isinstance(raw_entry, dict):
            raise ValueError("catalog skill entries must be objects")
        entry = dict(raw_entry)
        skill_id = entry["id"]
        skill_path = entry["path"]
        if not isinstance(skill_id, str) or not isinstance(skill_path, str):
            raise ValueError("catalog skill id and path must be strings")
        metadata, _ = load_frontmatter(root / skill_path)
        description = metadata.get("description")
        if not isinstance(description, str):
            raise ValueError(f"skill description must be a string: {skill_id}")
        write_actions = entry.get("write_actions")
        if not isinstance(write_actions, list):
            raise ValueError(f"skill write_actions must be a list: {skill_id}")
        manifest = {
            "interface": {"displayName": config.display_name},
            "name": config.name,
            "plugins": [
                {
                    "category": config.category,
                    "name": skill_id,
                    "policy": {"authentication": "ON_INSTALL", "installation": "AVAILABLE"},
                    "source": {
                        "path": f"./plugins/{skill_id}",
                        "ref": "main",
                        "source": "git-subdir",
                        "url": f"https://github.com/{config.repository}.git",
                    },
                }
            ],
        }
        skills.append(
            {
                **entry,
                "claude_install": f"/plugin install {skill_id}@{config.name}",
                "claude_invoke": f"/{skill_id}:{skill_id}",
                "codex_install": f"codex plugin add {skill_id}@{config.name}",
                "codex_invoke": f"${skill_id}:{skill_id}",
                "codex_project_manifest": _script_json(manifest),
                "description": description,
                "site_url": f"{config.site_url}skills/{skill_id}/",
                "source_url": f"https://github.com/{config.repository}/tree/{source_commit}/{skill_path}",
                "write_capable": bool(write_actions),
            }
        )

    return {
        "core_skill_ids": [entry["id"] for entry in skills if entry.get("tier") == "core"],
        "marketplace": asdict(config),
        "skills": skills,
        "smokes": [dict(smoke) for smoke in SMOKE_TESTS],
        "source_commit": source_commit,
    }


def _head(title: str, asset_prefix: str) -> str:
    return f"""<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light dark">
  <meta http-equiv="Content-Security-Policy" content="{escape(_CSP, quote=True)}">
  <title>{escape(title)}</title>
  <link rel="stylesheet" href="{asset_prefix}assets/styles.css">
  <script src="{asset_prefix}assets/app.js" defer></script>
</head>"""


def _copy_block(command: str, block_id: str, label: str = "Copy command") -> str:
    safe_id = escape(block_id, quote=True)
    return f"""<div class="command-specimen">
  <pre id="{safe_id}"><code>{escape(command)}</code></pre>
  <button type="button" class="copy-button" data-copy-target="{safe_id}">{escape(label)}</button>
</div>"""


def _status_line(skill: Mapping[str, object]) -> str:
    if skill["write_capable"]:
        actions = ", ".join(str(action) for action in skill["write_actions"])
        return f'<span class="permission permission-write">Approval-gated write · {escape(actions)}</span>'
    return '<span class="permission permission-read">Read-only</span>'


def _render_index(model: Mapping[str, object]) -> str:
    marketplace = model["marketplace"]
    skills = model["skills"]
    core_ids = set(model["core_skill_ids"])
    assert isinstance(marketplace, dict) and isinstance(skills, list)
    core = [skill for skill in skills if isinstance(skill, dict) and skill["id"] in core_ids]

    codex_core = "\n".join(
        [
            f"codex plugin marketplace add {marketplace['repository']}",
            *(str(skill["codex_install"]) for skill in core),
        ]
    )
    claude_core = "\n".join(
        [
            f"claude plugin marketplace add {marketplace['repository']} --scope project",
            *(str(skill["claude_install"]) for skill in core),
        ]
    )
    rows = []
    for number, skill in enumerate(skills, start=1):
        assert isinstance(skill, dict)
        tags = " ".join(str(tag) for tag in skill["tags"])
        clients = " ".join(
            str(client) for client, state in skill["adapters"].items() if state != "unsupported"
        )
        write_capable = str(skill["write_capable"]).lower()
        tag_list = "".join(f"<li>{escape(str(tag))}</li>" for tag in skill["tags"])
        rows.append(
            f"""<article class="skill-record" data-skill-card data-tier="{escape(str(skill['tier']), quote=True)}"
  data-tags="{escape(tags, quote=True)}" data-clients="{escape(clients, quote=True)}"
  data-write-capable="{write_capable}">
  <div class="record-register" aria-hidden="true">{number:02d}</div>
  <div class="record-body">
    <div class="record-heading">
      <h2><a href="skills/{escape(str(skill['id']), quote=True)}/">{escape(str(skill['name']))}</a></h2>
      <span class="version">v{escape(str(skill['version']))}</span>
    </div>
    <p>{escape(str(skill['summary']))}</p>
    <ul class="tag-list" aria-label="Skill tags">{tag_list}</ul>
  </div>
  <div class="record-meta">
    <span class="tier">{escape(str(skill['tier']).upper())}</span>
    {_status_line(skill)}
    <a class="record-open" href="skills/{escape(str(skill['id']), quote=True)}/">Open field record</a>
  </div>
</article>"""
        )

    title = str(marketplace["display_name"])
    return f"""<!doctype html>
<html lang="en">
{_head(title, '')}
<body>
{_DIRECTION_CONTRACT}
<a class="skip-link" href="#main-content">Skip to skill directory</a>
<header class="site-header">
  <a class="wordmark" href="./" aria-current="page">STACK / INTERNAL</a>
  <nav aria-label="Catalog reference">
    <a href="#skill-directory">Skill index</a>
    <a href="catalog.json">Catalog JSON</a>
    <a href="https://github.com/{escape(str(marketplace['repository']), quote=True)}">Source repository</a>
  </nav>
</header>
<main id="main-content">
  <section class="opening-field" aria-labelledby="page-title">
    <div class="opening-copy">
      <h1 id="page-title">Install company-grounded workflows as native skills.</h1>
      <p class="lede">Nine public Stack Internal skills, packaged individually for Codex and Claude Code. Browse the source, install through each client’s marketplace, connect MCP separately, and verify behavior locally.</p>
      <dl class="truth-ledger">
        <div><dt>Marketplace</dt><dd>{escape(str(marketplace['name']))}</dd></div>
        <div><dt>Skills</dt><dd>9 public records</dd></div>
        <div><dt>Data path</dt><dd>No backend or tenant data</dd></div>
        <div><dt>Compatibility</dt><dd>Experimental</dd></div>
      </dl>
    </div>
    <section class="core-ledger" aria-labelledby="core-title">
      <div class="ledger-heading">
        <h2 id="core-title">Core install ledger</h2>
        <span>3 independent plugins</span>
      </div>
      <p>Register this public repository as <strong>{escape(str(marketplace['name']))}</strong>, then add the three core skills in your chosen client.</p>
      <div class="client-tabs" data-tabs>
        <div role="tablist" aria-label="Core installation client">
          <button type="button" role="tab" id="core-tab-codex" aria-selected="true" aria-controls="core-panel-codex">Codex</button>
          <button type="button" role="tab" id="core-tab-claude" aria-selected="false" aria-controls="core-panel-claude">Claude Code</button>
        </div>
        <section role="tabpanel" id="core-panel-codex" aria-labelledby="core-tab-codex">
          {_copy_block(codex_core, 'core-codex')}
        </section>
        <section role="tabpanel" id="core-panel-claude" aria-labelledby="core-tab-claude">
          {_copy_block(claude_core, 'core-claude')}
        </section>
      </div>
      <p class="ledger-note">Plugin installation does not configure or authorize Stack Internal MCP.</p>
    </section>
  </section>

  <section class="directory" id="skill-directory" aria-labelledby="directory-title">
    <div class="directory-head">
      <div>
        <h2 id="directory-title">Skill directory</h2>
        <p><span id="visible-count">9</span> of 9 field records visible</p>
      </div>
      <label for="skill-search">Search by skill, outcome, or tag</label>
      <input id="skill-search" type="search" autocomplete="off" placeholder="Try debugging or curation">
    </div>
    <div class="filter-index" aria-label="Filter skill directory">
      <fieldset data-filter-group="tier">
        <legend>Tier</legend>
        <label><input type="checkbox" name="tier" value="core"> Core</label>
        <label><input type="checkbox" name="tier" value="extended"> Extended</label>
      </fieldset>
      <fieldset data-filter-group="client">
        <legend>Client</legend>
        <label><input type="checkbox" name="client" value="codex"> Codex</label>
        <label><input type="checkbox" name="client" value="claude-code"> Claude Code</label>
      </fieldset>
      <fieldset data-filter-group="write">
        <legend>Capability</legend>
        <label><input type="checkbox" name="write" value="false"> Read-only</label>
        <label><input type="checkbox" name="write" value="true"> Approval-gated write</label>
      </fieldset>
      <button type="button" class="clear-filters" id="clear-filters">Clear filters</button>
    </div>
    <div class="record-column">{''.join(rows)}</div>
    <p class="empty-result" id="empty-result" hidden>No field records match. Clear a filter or try a broader term.</p>
  </section>
</main>
<footer>
  <p>Generated from commit <code>{escape(str(model['source_commit']))}</code>. Public artifacts only; no customer content.</p>
</footer>
<div class="copy-status" id="copy-status" aria-live="polite" aria-atomic="true"></div>
</body>
</html>
"""


def _render_smokes(smokes: object, write_capable: bool) -> str:
    assert isinstance(smokes, list)
    items = []
    for index, smoke in enumerate(smokes, start=1):
        assert isinstance(smoke, dict)
        applicability = "" if write_capable or smoke["id"] != "write-approval" else (
            '<p class="smoke-note">Not applicable to this read-only skill; use a write-capable plugin to verify this release contract.</p>'
        )
        items.append(
            f"""<li>
  <span class="smoke-number">{index}</span>
  <div><h3>{escape(str(smoke['name']))}</h3>
  <p><strong>Prompt:</strong> {escape(str(smoke['prompt']))}</p>
  <p><strong>Observe:</strong> {escape(str(smoke['expected']))}</p>{applicability}</div>
</li>"""
        )
    return "".join(items)


def _render_skill(model: Mapping[str, object], skill: Mapping[str, object]) -> str:
    marketplace = model["marketplace"]
    assert isinstance(marketplace, dict)
    skill_id = str(skill["id"])
    manifest = str(skill["codex_project_manifest"])
    tools = "".join(f"<li><code>{escape(str(tool))}</code></li>" for tool in skill["required_tools"])
    if skill["write_capable"]:
        action_items = "".join(f"<li><code>{escape(str(action))}</code></li>" for action in skill["write_actions"])
        safety = f"""<p class="safety-callout">This skill can propose writes. Every changed action or payload requires fresh, explicit approval before the MCP call.</p>
<p>Declared write actions:</p><ul class="tool-list">{action_items}</ul>"""
    else:
        safety = '<p class="safety-callout">Read-only. This skill declares no Stack Internal write actions.</p>'

    codex_mcp = "codex mcp add stack-internal --url https://[tenant-slug].stackenterprise.co/mcp"
    claude_mcp = "claude mcp add --transport http stack-internal https://[tenant-slug].stackenterprise.co/mcp"
    title = f"{skill['name']} · {marketplace['display_name']}"
    return f"""<!doctype html>
<html lang="en">
{_head(title, '../../')}
<body>
{_DIRECTION_CONTRACT}
<a class="skip-link" href="#main-content">Skip to skill record</a>
<header class="site-header detail-header">
  <a class="wordmark" href="../../">STACK / INTERNAL</a>
  <nav aria-label="Skill reference">
    <a href="../../#skill-directory">All skills</a>
    <a href="../../catalog.json">Catalog JSON</a>
    <a href="{escape(str(skill['source_url']), quote=True)}">Canonical source</a>
  </nav>
</header>
<main id="main-content" class="detail-main">
  <article class="field-record-detail">
    <header class="record-title-block">
      <h1>{escape(str(skill['name']))}</h1>
      <p>{escape(str(skill['summary']))}</p>
      <div class="record-classification" aria-label="Skill release metadata">
        <span>{escape(str(skill['tier']).upper())} SKILL</span>
        <span>v{escape(str(skill['version']))}</span>
        <span>COMPATIBILITY: EXPERIMENTAL</span>
        {_status_line(skill)}
      </div>
    </header>

    <div class="record-layout">
      <nav class="record-index" aria-label="On this page">
        <p>FIELD INDEX</p>
        <a href="#purpose">Purpose</a>
        <a href="#requirements">Requirements</a>
        <a href="#safety">Safety</a>
        <a href="#codex">Install in Codex</a>
        <a href="#claude">Install in Claude Code</a>
        <a href="#mcp">Connect MCP</a>
        <a href="#try">Try it</a>
        <a href="#troubleshooting">Troubleshooting</a>
      </nav>
      <div class="record-sections">
        <section id="purpose"><h2>Purpose</h2><p>{escape(str(skill['description']))}</p></section>
        <section id="requirements"><h2>Requirements</h2>
          <p>Install the public plugin in Codex or Claude Code. Separately configure an enabled Stack Internal MCP endpoint and authenticate with an authorized account.</p>
          <h3>Required MCP tools</h3><ul class="tool-list">{tools}</ul>
        </section>
        <section id="safety"><h2>Safety</h2>{safety}<p>The marketplace package contains instructions, not tenant credentials, MCP configuration, hooks, or executables. Review source and permissions before use.</p></section>
        <section id="codex"><h2>Install in Codex</h2>
          <p><strong>Client-managed quick install.</strong> Add the public marketplace, then install this one plugin. Codex chooses command-driven scope.</p>
          {_copy_block(f"codex plugin marketplace add {marketplace['repository']}", f'{skill_id}-codex-marketplace')}
          {_copy_block(str(skill['codex_install']), f'{skill_id}-codex-install')}
          <p>Invoke explicitly with <code>{escape(str(skill['codex_invoke']))}</code>. For a repository-scoped declaration, commit this file as <code>.agents/plugins/marketplace.json</code>:</p>
          <div class="command-specimen manifest-specimen"><pre id="{escape(skill_id)}-manifest"><code>{escape(manifest)}</code></pre><button type="button" class="copy-button" data-copy-target="{escape(skill_id)}-manifest">Copy manifest</button></div>
          <script type="application/json" data-codex-project-manifest>{manifest}</script>
        </section>
        <section id="claude"><h2>Install in Claude Code</h2>
          <p>Add the repository marketplace at project scope, install the plugin interactively, then reload Claude Code if discovery is stale.</p>
          {_copy_block(f"claude plugin marketplace add {marketplace['repository']} --scope project", f'{skill_id}-claude-marketplace')}
          {_copy_block(str(skill['claude_install']), f'{skill_id}-claude-install')}
          <p>Invoke explicitly with <code>{escape(str(skill['claude_invoke']))}</code>.</p>
        </section>
        <section id="mcp"><h2>Connect Stack Internal MCP</h2>
          <p>Plugin installation does not grant Stack Internal access. Ask an administrator to enable MCP, replace the placeholder locally, and complete OAuth in your chosen client.</p>
          <div class="client-tabs" data-tabs>
            <div role="tablist" aria-label="MCP setup client">
              <button type="button" role="tab" id="{escape(skill_id)}-mcp-tab-codex" aria-selected="true" aria-controls="{escape(skill_id)}-mcp-panel-codex">Codex</button>
              <button type="button" role="tab" id="{escape(skill_id)}-mcp-tab-claude" aria-selected="false" aria-controls="{escape(skill_id)}-mcp-panel-claude">Claude Code</button>
            </div>
            <section role="tabpanel" id="{escape(skill_id)}-mcp-panel-codex" aria-labelledby="{escape(skill_id)}-mcp-tab-codex">{_copy_block(codex_mcp, f'{skill_id}-codex-mcp')}</section>
            <section role="tabpanel" id="{escape(skill_id)}-mcp-panel-claude" aria-labelledby="{escape(skill_id)}-mcp-tab-claude">{_copy_block(claude_mcp, f'{skill_id}-claude-mcp')}</section>
          </div>
        </section>
        <section id="try"><h2>Try it</h2><p>Start a new or reloaded client session, invoke the skill explicitly if needed, and observe local tool calls. Do not record raw tenant content.</p><ol class="smoke-ledger">{_render_smokes(model['smokes'], bool(skill['write_capable']))}</ol></section>
        <section id="troubleshooting"><h2>Troubleshooting</h2>
          <dl class="troubleshooting-ledger">
            <div><dt>Plugin commands are missing</dt><dd>Your client version may not expose native marketplace commands. Confirm the exact version and use the documented filesystem fallback without changing the canonical skill.</dd></div>
            <div><dt>Marketplace Git or policy failure</dt><dd>Confirm repository access and ask the managed-policy owner to allow this marketplace. Do not work around organization policy.</dd></div>
            <div><dt>Plugin not found</dt><dd>Refresh the marketplace metadata, confirm the plugin ID <code>{escape(skill_id)}</code>, and retry the native install.</dd></div>
            <div><dt>Installed but undiscovered</dt><dd>List installed plugins, reload the client, then invoke the namespaced skill explicitly.</dd></div>
            <div><dt>MCP or OAuth failure</dt><dd>The plugin remains installed. Recheck the separate endpoint, authorization, and tenant permission; report failure honestly rather than claiming an internal search.</dd></div>
          </dl>
        </section>
        <section id="compatibility"><h2>Compatibility</h2><p>Codex and Claude Code compatibility is experimental until exact-version, tenant-backed release evidence passes all four smokes. Automated catalog tests are not live compatibility proof.</p></section>
        <section id="source"><h2>Source</h2><p>Canonical skill content at commit <code>{escape(str(model['source_commit']))}</code>.</p><p><a href="{escape(str(skill['source_url']), quote=True)}">Inspect the canonical source for {escape(skill_id)}</a></p></section>
      </div>
    </div>
  </article>
</main>
<footer><p><a href="../../">Return to the public directory</a> · No backend, tenant form, or MCP proxy.</p></footer>
<div class="copy-status" id="copy-status" aria-live="polite" aria-atomic="true"></div>
</body>
</html>
"""


def _safe_output_root(root: Path, output_root: Path) -> Path:
    """Return an absolute output path after refusing dangerous redirects."""
    root = root.resolve()
    output_root = Path(os.path.abspath(output_root))
    if output_root == output_root.parent:
        raise ValueError("site output directory must not be a filesystem root")
    if any(path.is_symlink() for path in (output_root, *output_root.parents)):
        raise ValueError("site output path must not contain a symlink")
    if output_root.exists() and not output_root.is_dir():
        raise ValueError("site output target must be a directory")
    try:
        output_root.parent.mkdir(parents=True, exist_ok=True)
    except (FileExistsError, NotADirectoryError) as error:
        raise ValueError("site output parent must be a directory") from error
    if not output_root.parent.is_dir():
        raise ValueError("site output parent must be a directory")
    resolved_output = output_root.resolve(strict=False)
    if resolved_output == root or root.is_relative_to(resolved_output):
        raise ValueError("site output directory must not contain the source repository")
    return output_root


def _write_site_tree(root: Path, output_root: Path, model: dict[str, object]) -> None:
    """Write a complete site into an empty staging directory."""
    assets = output_root / "assets"
    assets.mkdir(parents=True, exist_ok=True)

    (output_root / "catalog.json").write_text(_json_text(model), encoding="utf-8")
    (output_root / "index.html").write_text(_render_index(model), encoding="utf-8")
    shutil.copyfile(root / "marketplace_web" / "styles.css", assets / "styles.css")
    shutil.copyfile(root / "marketplace_web" / "app.js", assets / "app.js")

    skills = model["skills"]
    assert isinstance(skills, list)
    for skill in skills:
        assert isinstance(skill, dict)
        destination = output_root / "skills" / str(skill["id"])
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "index.html").write_text(_render_skill(model, skill), encoding="utf-8")


def write_site(root: Path, output_root: Path, source_commit: str) -> None:
    """Atomically replace *output_root* with the exact deterministic site tree."""
    root = Path(root).resolve()
    output_root = _safe_output_root(root, output_root)
    model = build_site_model(root, source_commit)
    staging = Path(tempfile.mkdtemp(prefix=f".{output_root.name}.build-", dir=output_root.parent))
    backup: Path | None = None
    try:
        _write_site_tree(root, staging, model)
        if output_root.exists():
            backup = Path(tempfile.mkdtemp(prefix=f".{output_root.name}.previous-", dir=output_root.parent))
            backup.rmdir()
            output_root.replace(backup)
        try:
            staging.replace(output_root)
        except OSError:
            if backup is not None and backup.exists() and not output_root.exists():
                backup.replace(output_root)
            raise
        if backup is not None:
            shutil.rmtree(backup)
            backup = None
    finally:
        if staging.exists():
            shutil.rmtree(staging)
        if backup is not None and backup.exists() and not output_root.exists():
            backup.replace(output_root)
