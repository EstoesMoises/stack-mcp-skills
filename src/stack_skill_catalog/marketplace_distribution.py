"""Generate deterministic native marketplace distributions."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory

from .catalog import load_catalog
from .marketplace_config import MarketplaceConfig, load_marketplace_config
from .plugin_package import build_plugin_package


GENERATED_MARKER = "generated; edit catalog/skills.json or skills/ instead\n"
SURFACES = (
    Path("plugins"),
    Path(".agents/plugins/marketplace.json"),
    Path(".claude-plugin/marketplace.json"),
)


def _write_json(path: Path, value: object) -> None:
    """Write stable, human-readable JSON with a trailing newline."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _preflight_destinations(root: Path) -> None:
    """Reject destination nodes that cannot be safely replaced in place."""
    if root.is_symlink():
        raise ValueError("refusing to use a symlinked marketplace destination")
    if root.exists() and not root.is_dir():
        raise ValueError("refusing to use an incompatible marketplace destination")

    for surface in SURFACES:
        candidate = root
        for index, part in enumerate(surface.parts):
            candidate /= part
            if candidate.is_symlink():
                raise ValueError("refusing to use a symlinked marketplace destination")
            if not candidate.exists():
                continue
            expects_directory = index < len(surface.parts) - 1 or surface == Path("plugins")
            if expects_directory and not candidate.is_dir():
                raise ValueError("refusing to use an incompatible marketplace destination")
            if not expects_directory and not candidate.is_file():
                raise ValueError("refusing to use an incompatible marketplace destination")


def _validate_entries(entries: list[dict[str, object]]) -> None:
    """Reject catalogs that cannot represent the fixed nine-plugin distribution."""
    ids = [entry.get("id") for entry in entries]
    duplicates = sorted(
        {identifier for identifier in ids if isinstance(identifier, str) and ids.count(identifier) > 1}
    )
    if duplicates:
        raise ValueError(f"catalog contains duplicate skill IDs: {', '.join(duplicates)}")

    for entry in entries:
        identifier = entry.get("id")
        path = entry.get("path")
        if not isinstance(identifier, str) or not isinstance(path, str) or Path(path).name != identifier:
            raise ValueError(f"catalog skill ID must match path: {identifier}")

    counts = Counter(entry.get("tier") for entry in entries)
    if counts != Counter({"core": 3, "extended": 6}):
        raise ValueError("catalog must contain exactly three core and six extended skills")


def build_codex_marketplace(
    entries: list[dict[str, object]], config: MarketplaceConfig
) -> dict[str, object]:
    """Build the ordered Codex marketplace manifest."""
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


def build_claude_marketplace(
    entries: list[dict[str, object]], config: MarketplaceConfig
) -> dict[str, object]:
    """Build the ordered Claude Code marketplace manifest."""
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


def generate_distribution(root: Path, output_root: Path) -> None:
    """Generate all marketplace artifacts inside *output_root* only."""
    catalog = load_catalog(root / "catalog/skills.json")
    entries = catalog.get("skills")
    if not isinstance(entries, list) or not all(isinstance(entry, dict) for entry in entries):
        raise ValueError("catalog skills must be a list of objects")
    _validate_entries(entries)
    config = load_marketplace_config(root / "catalog/marketplace.json")
    _preflight_destinations(output_root)

    plugins_root = output_root / "plugins"
    plugins_root.mkdir(parents=True, exist_ok=True)
    (plugins_root / ".generated-marketplace").write_text(GENERATED_MARKER, encoding="utf-8")
    for entry in entries:
        build_plugin_package(root, entry, config, plugins_root)

    _write_json(
        output_root / ".agents/plugins/marketplace.json",
        build_codex_marketplace(entries, config),
    )
    _write_json(
        output_root / ".claude-plugin/marketplace.json",
        build_claude_marketplace(entries, config),
    )


def _tree_files(path: Path) -> dict[str, Path]:
    """Return every file-like tree entry keyed by a portable relative path."""
    return {
        item.relative_to(path).as_posix(): item
        for item in sorted(path.rglob("*"))
        if item.is_file() or item.is_symlink()
    }


def distribution_diff(root: Path) -> list[str]:
    """Return byte-level drift for the three committed marketplace surfaces."""
    root = root.resolve()
    with TemporaryDirectory(prefix="stack-marketplace-check-") as temporary:
        expected_root = Path(temporary)
        generate_distribution(root, expected_root)
        differences: list[str] = []
        for surface in SURFACES:
            expected = expected_root / surface
            actual = root / surface
            label = surface.as_posix()
            if not actual.exists() and not actual.is_symlink():
                differences.append(f"missing: {label}")
                continue
            if expected.is_file():
                if actual.is_symlink() or not actual.is_file() or actual.read_bytes() != expected.read_bytes():
                    differences.append(f"changed: {label}")
                continue
            if actual.is_symlink() or not actual.is_dir():
                differences.append(f"changed: {label}")
                continue

            expected_files = _tree_files(expected)
            actual_files = _tree_files(actual)
            for relative in sorted(expected_files.keys() - actual_files.keys()):
                differences.append(f"missing: {label}/{relative}")
            for relative in sorted(actual_files.keys() - expected_files.keys()):
                differences.append(f"unexpected: {label}/{relative}")
            for relative in sorted(expected_files.keys() & actual_files.keys()):
                expected_file = expected_files[relative]
                actual_file = actual_files[relative]
                if (
                    actual_file.is_symlink()
                    or not actual_file.is_file()
                    or actual_file.read_bytes() != expected_file.read_bytes()
                ):
                    differences.append(f"changed: {label}/{relative}")
        return sorted(differences)


def write_distribution(root: Path) -> None:
    """Safely replace only generated marketplace surfaces under *root*."""
    root = root.resolve()
    _preflight_destinations(root)
    plugins = root / "plugins"
    marker = plugins / ".generated-marketplace"
    if plugins.exists() or plugins.is_symlink():
        marker_is_exact = (
            plugins.is_dir()
            and not plugins.is_symlink()
            and marker.is_file()
            and not marker.is_symlink()
            and marker.read_bytes() == GENERATED_MARKER.encode("utf-8")
        )
        if not marker_is_exact:
            raise ValueError("refusing to replace plugins without the exact generated marker")

    with TemporaryDirectory(prefix=f".{root.name}-marketplace-", dir=root.parent) as temporary:
        generated = Path(temporary)
        generate_distribution(root, generated)

        if plugins.exists():
            shutil.rmtree(plugins)
        shutil.move(str(generated / "plugins"), plugins)
        for surface in SURFACES[1:]:
            destination = root / surface
            destination.parent.mkdir(parents=True, exist_ok=True)
            (generated / surface).replace(destination)
