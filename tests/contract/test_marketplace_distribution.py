import json
from pathlib import Path
import shutil

import pytest

from stack_skill_catalog.catalog import load_catalog
from stack_skill_catalog.marketplace_config import load_marketplace_config
from stack_skill_catalog.marketplace_distribution import (
    GENERATED_MARKER,
    build_claude_marketplace,
    build_codex_marketplace,
    build_copilot_marketplace,
    generate_distribution,
)


ROOT = Path(__file__).parents[2]


def test_distribution_contains_all_catalog_plugins_in_catalog_order(tmp_path):
    """Dropping or reordering a catalog entry must change the generated distribution."""
    generate_distribution(ROOT, tmp_path)
    ids = [entry["id"] for entry in load_catalog(ROOT / "catalog/skills.json")["skills"]]

    assert {path.name for path in (tmp_path / "plugins").iterdir() if path.is_dir()} == set(ids)
    codex = json.loads((tmp_path / ".agents/plugins/marketplace.json").read_text())
    claude = json.loads((tmp_path / ".claude-plugin/marketplace.json").read_text())
    copilot = json.loads((tmp_path / ".github/plugin/marketplace.json").read_text())
    assert [entry["name"] for entry in codex["plugins"]] == ids
    assert [entry["name"] for entry in claude["plugins"]] == ids
    assert [entry["name"] for entry in copilot["plugins"]] == ids


def test_core_is_a_selection_not_a_generated_plugin(tmp_path):
    """Generation must not invent a tenth bundle plugin for the core selection."""
    generate_distribution(ROOT, tmp_path)

    assert not (tmp_path / "plugins/core").exists()
    assert not (tmp_path / "plugins/stack-internal-core").exists()


def test_marketplace_manifests_include_native_client_metadata_in_catalog_order():
    """Removing native metadata or changing entry order must fail the manifest contract."""
    entries = load_catalog(ROOT / "catalog/skills.json")["skills"]
    config = load_marketplace_config(ROOT / "catalog/marketplace.json")

    codex = build_codex_marketplace(entries, config)
    claude = build_claude_marketplace(entries, config)
    copilot = build_copilot_marketplace(entries, config)

    first = entries[0]
    assert codex["name"] == "stack-internal"
    assert codex["interface"] == {"displayName": "Stack Internal Skills"}
    assert codex["plugins"][0] == {
        "name": first["id"],
        "source": {"source": "local", "path": f"./plugins/{first['id']}"},
        "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
        "category": "Productivity",
    }
    assert claude["description"] == (
        "Public Stack Internal Agent Skills for company-grounded coding workflows."
    )
    assert claude["owner"] == {"name": "Stack Internal Skills"}
    assert claude["plugins"][0] == {
        "name": first["id"],
        "source": f"./plugins/{first['id']}",
        "description": first["summary"],
        "version": first["version"],
        "author": {"name": "Stack Internal Skills"},
    }
    assert copilot["owner"] == {"name": "Stack Internal Skills"}
    assert copilot["metadata"] == {
        "description": "Public Stack Internal Agent Skills for company-grounded coding workflows.",
        "version": "0.3.0",
    }
    assert copilot["plugins"][0] == {
        **claude["plugins"][0],
        "homepage": f"{config.site_url}skills/{first['id']}/",
        "repository": f"https://github.com/{config.repository}",
        "license": "Apache-2.0",
        "keywords": first["tags"],
        "category": config.category,
    }


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda entries: entries.append(entries[0].copy()), "duplicate skill IDs"),
        (
            lambda entries: entries[0].__setitem__("path", "skills/core/different-id"),
            "skill ID must match path",
        ),
        (lambda entries: entries[0].__setitem__("tier", "invalid"), "skill tier is invalid"),
    ],
)
def test_distribution_rejects_invalid_catalog_shape(tmp_path, mutation, message):
    """Invalid IDs, paths, or tiers must fail before an output tree is created."""
    catalog = load_catalog(ROOT / "catalog/skills.json")
    mutation(catalog["skills"])
    root = tmp_path / "root"
    (root / "catalog").mkdir(parents=True)
    (root / "catalog/skills.json").write_text(json.dumps(catalog), encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        generate_distribution(root, tmp_path / "output")

    assert not (tmp_path / "output").exists()


def test_generated_marker_has_the_exact_protection_content(tmp_path):
    """Changing the marker bytes must prevent safe replacement on later writes."""
    generate_distribution(ROOT, tmp_path)

    assert (tmp_path / "plugins/.generated-marketplace").read_text() == GENERATED_MARKER


def test_generation_is_isolated_to_the_supplied_output_root(tmp_path):
    """A distribution build must never write generated surfaces into its source root."""
    source = tmp_path / "source"
    for directory in ("catalog", "standards", "skills"):
        shutil.copytree(ROOT / directory, source / directory)
    shutil.copyfile(ROOT / "LICENSE", source / "LICENSE")
    before = {
        path.relative_to(source).as_posix(): path.read_bytes()
        for path in source.rglob("*")
        if path.is_file()
    }

    generate_distribution(source, tmp_path / "output")

    after = {
        path.relative_to(source).as_posix(): path.read_bytes()
        for path in source.rglob("*")
        if path.is_file()
    }
    assert after == before
    assert not (source / "plugins").exists()
    assert not (source / ".agents").exists()
    assert not (source / ".claude-plugin").exists()
    assert not (source / ".github").exists()


@pytest.mark.parametrize(
    "symlinked_parent",
    ["plugins", ".agents", ".agents/plugins", ".claude-plugin", ".github", ".github/plugin"],
)
def test_generation_rejects_symlinked_destination_parents(tmp_path, symlinked_parent):
    """A pre-existing output symlink must not redirect generated bytes outside output_root."""
    output = tmp_path / "output"
    output.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    symlink = output / symlinked_parent
    symlink.parent.mkdir(parents=True, exist_ok=True)
    symlink.symlink_to(outside, target_is_directory=True)

    with pytest.raises(ValueError, match="symlinked marketplace destination"):
        generate_distribution(ROOT, output)

    assert list(outside.iterdir()) == []
