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
    assert json.loads((plugin / ".codex-plugin/plugin.json").read_text())["version"] == entry["version"]
    assert json.loads((plugin / ".claude-plugin/plugin.json").read_text())["version"] == entry["version"]
    assert (plugin / "LICENSE").read_bytes() == (ROOT / "LICENSE").read_bytes()


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
