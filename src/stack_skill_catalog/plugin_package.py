"""Build safe, dual-client plugin packages from canonical skills."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from .generation_safety import safe_join, validate_skill_entry
from .marketplace_config import MarketplaceConfig
from .skill import load_frontmatter


_FORBIDDEN_CONTENT_NAMES = {".app.json", ".mcp.json", "hooks"}


def _write_json(path: Path, value: object) -> None:
    """Write stable, human-readable JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_codex_plugin_manifest(entry: dict[str, object], config: MarketplaceConfig) -> dict[str, object]:
    """Build the Codex manifest for one canonical skill."""
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
            "longDescription": entry["summary"],
            "developerName": config.publisher_name,
            "category": config.category,
            "capabilities": ["Read"] if not write_actions else ["Read", "Approval-gated writes"],
            "websiteURL": f"{config.site_url}skills/{entry['id']}/",
            "defaultPrompt": [f"Use {entry['name']} to help with a Stack Internal task."],
        },
    }


def build_claude_plugin_manifest(entry: dict[str, object], config: MarketplaceConfig) -> dict[str, object]:
    """Build the Claude Code manifest for one canonical skill."""
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


def plugin_readme(entry: dict[str, object], config: MarketplaceConfig) -> str:
    """Describe the package, its prerequisites, and client invocations."""
    return f"""# {entry['name']}

- Plugin ID: `{entry['id']}`
- Skill ID: `{entry['id']}`
- Version: `{entry['version']}`

Canonical source: {config.site_url}skills/{entry['id']}/

Required MCP tools: {', '.join(entry['required_tools'])}

Declared write actions: {', '.join(entry['write_actions']) or 'None'}

Prerequisite: configure a separate Stack Internal MCP connection and OAuth authentication before use.

Codex: `${entry['id']}:{entry['id']}`

Claude Code: `/{entry['id']}:{entry['id']}`

Compatibility: experimental for Codex and Claude Code.
"""


def build_plugin_package(
    root: Path,
    entry: dict[str, object],
    config: MarketplaceConfig,
    destination: Path,
) -> Path:
    """Create one self-contained plugin without executable or MCP configuration."""
    identifier, source = validate_skill_entry(root, entry)
    destination = Path(destination)
    if destination.is_symlink():
        raise ValueError("package destination may not be a symlink")
    plugin_root = safe_join(destination, identifier)
    if plugin_root.exists() or plugin_root.is_symlink():
        raise ValueError(f"package root already exists: {plugin_root}")
    if source.is_symlink():
        raise ValueError(f"canonical skills may not contain symlinks: {source.relative_to(root)}")
    for path in source.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"canonical skills may not contain symlinks: {path.relative_to(root)}")
        if path.name in _FORBIDDEN_CONTENT_NAMES or (path.is_file() and path.stat().st_mode & 0o111):
            raise ValueError(f"canonical skills may not contain forbidden plugin content: {path.relative_to(root)}")
    metadata, _ = load_frontmatter(source)
    if metadata.get("metadata", {}).get("stack-internal-version") != entry["version"]:
        raise ValueError("catalog and skill versions differ")
    shutil.copytree(source, safe_join(plugin_root, "skills", identifier), copy_function=shutil.copyfile)
    shutil.copyfile(root / "LICENSE", safe_join(plugin_root, "LICENSE"))
    _write_json(
        safe_join(plugin_root, ".codex-plugin", "plugin.json"),
        build_codex_plugin_manifest(entry, config),
    )
    _write_json(
        safe_join(plugin_root, ".claude-plugin", "plugin.json"),
        build_claude_plugin_manifest(entry, config),
    )
    safe_join(plugin_root, "README.md").write_text(plugin_readme(entry, config), encoding="utf-8")
    return plugin_root
