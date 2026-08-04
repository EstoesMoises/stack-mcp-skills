import json
from pathlib import Path
import shutil

import pytest

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
    """Packaging must preserve every canonical skill file and version."""
    entry = load_catalog(ROOT / "catalog/skills.json")["skills"][0]
    config = load_marketplace_config(ROOT / "catalog/marketplace.json")

    plugin = build_plugin_package(ROOT, entry, config, tmp_path)

    canonical = ROOT / entry["path"]
    packaged = plugin / "skills" / entry["id"]
    assert _files(packaged) == _files(canonical)
    codex = json.loads((plugin / ".codex-plugin/plugin.json").read_text())
    claude = json.loads((plugin / ".claude-plugin/plugin.json").read_text())
    assert codex["version"] == entry["version"]
    assert claude == {
        "name": entry["id"],
        "version": entry["version"],
        "description": entry["summary"],
        "author": {"name": config.publisher_name},
        "homepage": f"{config.site_url}skills/{entry['id']}/",
        "repository": f"https://github.com/{config.repository}",
        "license": "Apache-2.0",
        "keywords": entry["tags"],
    }
    assert (plugin / "LICENSE").read_bytes() == (ROOT / "LICENSE").read_bytes()
    readme = (plugin / "README.md").read_text(encoding="utf-8")
    for expected in (
        f"Plugin ID: `{entry['id']}`",
        f"Skill ID: `{entry['id']}`",
        f"Version: `{entry['version']}`",
        f"Canonical source: {config.site_url}skills/{entry['id']}/",
        f"Required MCP tools: {', '.join(entry['required_tools'])}",
        f"Declared write actions: {', '.join(entry['write_actions']) or 'None'}",
        "separate Stack Internal MCP connection and OAuth authentication",
        f"Codex: `${entry['id']}:{entry['id']}`",
        f"Claude Code: `/{entry['id']}:{entry['id']}`",
        "Compatibility: experimental for Codex and Claude Code.",
    ):
        assert expected in readme


def test_plugin_contains_no_executable_or_mcp_surface(tmp_path):
    """A package must not expose hooks, MCP, or app configuration surfaces."""
    entry = load_catalog(ROOT / "catalog/skills.json")["skills"][0]
    config = load_marketplace_config(ROOT / "catalog/marketplace.json")

    plugin = build_plugin_package(ROOT, entry, config, tmp_path)

    relative = {path.relative_to(plugin).as_posix() for path in plugin.rglob("*")}
    assert not {"hooks", ".mcp.json", ".app.json"} & relative
    codex = json.loads((plugin / ".codex-plugin/plugin.json").read_text())
    assert not {"hooks", "mcpServers", "apps"} & codex.keys()


def test_codex_manifest_includes_required_interface_content(tmp_path):
    """The generated Codex manifest must meet the plugin ingestion contract."""
    entry = load_catalog(ROOT / "catalog/skills.json")["skills"][0]
    config = load_marketplace_config(ROOT / "catalog/marketplace.json")

    plugin = build_plugin_package(ROOT, entry, config, tmp_path)
    interface = json.loads((plugin / ".codex-plugin/plugin.json").read_text())["interface"]

    assert interface["longDescription"] == entry["summary"]
    assert interface["defaultPrompt"] == [
        f"Use {entry['name']} to help with a Stack Internal task."
    ]


def test_plugin_rejects_canonical_skill_symlinks(tmp_path):
    """A linked file could make an archive include content outside the canonical skill."""
    entry = load_catalog(ROOT / "catalog/skills.json")["skills"][0]
    config = load_marketplace_config(ROOT / "catalog/marketplace.json")
    skill_root = tmp_path / entry["path"]
    shutil.copytree(ROOT / entry["path"], skill_root)
    (skill_root / "linked.md").symlink_to(ROOT / "LICENSE")
    shutil.copyfile(ROOT / "LICENSE", tmp_path / "LICENSE")

    with pytest.raises(ValueError, match="may not contain symlinks"):
        build_plugin_package(tmp_path, entry, config, tmp_path / "packages")


def test_plugin_rejects_catalog_version_that_differs_from_canonical_skill(tmp_path):
    """A stale catalog version must not produce any package files."""
    entry = load_catalog(ROOT / "catalog/skills.json")["skills"][0].copy()
    config = load_marketplace_config(ROOT / "catalog/marketplace.json")
    skill_root = tmp_path / entry["path"]
    shutil.copytree(ROOT / entry["path"], skill_root)
    shutil.copyfile(ROOT / "LICENSE", tmp_path / "LICENSE")
    entry["version"] = "9.9.9"
    destination = tmp_path / "packages"

    with pytest.raises(ValueError, match="catalog and skill versions differ"):
        build_plugin_package(tmp_path, entry, config, destination)

    assert not destination.exists()


def test_plugin_refuses_an_existing_package_root(tmp_path):
    """Pre-existing package contents must never survive in a returned package."""
    entry = load_catalog(ROOT / "catalog/skills.json")["skills"][0]
    config = load_marketplace_config(ROOT / "catalog/marketplace.json")
    plugin_root = tmp_path / entry["id"]
    plugin_root.mkdir()
    (plugin_root / ".mcp.json").write_text('{"untrusted": true}\n', encoding="utf-8")

    with pytest.raises(ValueError, match="package root already exists"):
        build_plugin_package(ROOT, entry, config, tmp_path)

    assert (plugin_root / ".mcp.json").is_file()


def test_plugin_rejects_a_symlinked_canonical_skill_directory(tmp_path):
    """A catalog path must not dereference a directory outside its canonical tree."""
    entry = load_catalog(ROOT / "catalog/skills.json")["skills"][0]
    config = load_marketplace_config(ROOT / "catalog/marketplace.json")
    root = tmp_path / "root"
    external_skill = tmp_path / "external-skill"
    shutil.copytree(ROOT / entry["path"], external_skill)
    (root / "skills" / "core").mkdir(parents=True)
    (root / entry["path"]).symlink_to(external_skill, target_is_directory=True)
    shutil.copyfile(ROOT / "LICENSE", root / "LICENSE")

    with pytest.raises(ValueError, match="may not contain symlinks"):
        build_plugin_package(root, entry, config, root / "packages")

    assert not (root / "packages").exists()


@pytest.mark.parametrize(
    ("hostile_id", "hostile_path"),
    [
        ("../escaped", "skills/core/efficient-search"),
        ("absolute", "../external/efficient-search"),
    ],
)
def test_plugin_rejects_nonportable_catalog_fields_before_writing(
    tmp_path, hostile_id, hostile_path
):
    """Direct package callers cannot use catalog IDs or paths to escape source/destination roots."""
    entry = load_catalog(ROOT / "catalog/skills.json")["skills"][0].copy()
    config = load_marketplace_config(ROOT / "catalog/marketplace.json")
    root = tmp_path / "root"
    shutil.copytree(ROOT / "skills", root / "skills")
    shutil.copyfile(ROOT / "LICENSE", root / "LICENSE")
    destination = tmp_path / "packages"
    if hostile_id == "absolute":
        external = tmp_path / "external" / "efficient-search"
        shutil.copytree(ROOT / entry["path"], external)
        entry["id"] = str(tmp_path / "absolute-package")
        entry["path"] = str(external)
    else:
        entry["id"] = hostile_id
        entry["path"] = hostile_path

    with pytest.raises(ValueError, match="catalog skill"):
        build_plugin_package(root, entry, config, destination)

    assert not destination.exists()
    assert not (tmp_path / "absolute-package").exists()


@pytest.mark.parametrize("kind", ["mcp", "app", "hooks", "executable"])
def test_plugin_rejects_forbidden_canonical_content_before_writing(kind, tmp_path):
    """A canonical skill cannot smuggle plugin surfaces or executable content into a package."""
    entry = load_catalog(ROOT / "catalog/skills.json")["skills"][0]
    config = load_marketplace_config(ROOT / "catalog/marketplace.json")
    skill_root = tmp_path / entry["path"]
    shutil.copytree(ROOT / entry["path"], skill_root)
    shutil.copyfile(ROOT / "LICENSE", tmp_path / "LICENSE")
    nested = skill_root / "nested"
    nested.mkdir()
    if kind == "mcp":
        (nested / ".mcp.json").write_text("{}\n", encoding="utf-8")
    elif kind == "app":
        (nested / ".app.json").write_text("{}\n", encoding="utf-8")
    elif kind == "hooks":
        (nested / "hooks").mkdir()
    else:
        executable = nested / "server"
        executable.write_text("#!/bin/sh\n", encoding="utf-8")
        executable.chmod(0o755)
    destination = tmp_path / "packages"

    with pytest.raises(ValueError, match="forbidden plugin content"):
        build_plugin_package(tmp_path, entry, config, destination)

    assert not destination.exists()
