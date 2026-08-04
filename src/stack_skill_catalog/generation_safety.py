"""Validate untrusted catalog paths before generators read or write files."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

from .catalog import load_catalog


_SKILL_ID_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


def safe_join(base: Path, *components: str | Path) -> Path:
    """Join relative components while proving the result remains below *base*."""
    base = Path(base)
    candidate = base
    for component in components:
        relative = Path(component)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("generated destination must stay inside its staging root")
        candidate /= relative

    resolved_base = base.resolve(strict=False)
    resolved_candidate = candidate.resolve(strict=False)
    if not resolved_candidate.is_relative_to(resolved_base):
        raise ValueError("generated destination must stay inside its staging root")
    return candidate


def validate_skill_entry(root: Path, entry: dict[str, object]) -> tuple[str, Path]:
    """Return a strict skill ID and canonical in-repository source directory."""
    identifier = entry.get("id")
    tier = entry.get("tier")
    raw_path = entry.get("path")
    if not isinstance(identifier, str) or _SKILL_ID_PATTERN.fullmatch(identifier) is None:
        raise ValueError("catalog skill ID must be a portable lowercase identifier")
    if tier not in {"core", "extended"}:
        raise ValueError(f"catalog skill tier is invalid: {identifier}")
    if not isinstance(raw_path, str):
        raise ValueError(f"catalog skill path must be a string: {identifier}")

    relative = Path(raw_path)
    expected = Path("skills") / tier / identifier
    if (
        relative.is_absolute()
        or ".." in relative.parts
        or raw_path != expected.as_posix()
    ):
        raise ValueError(f"catalog skill ID must match path: {identifier}")

    root = Path(root).resolve()
    candidate = root / relative
    cursor = root
    for part in relative.parts:
        cursor /= part
        if cursor.is_symlink():
            raise ValueError(f"catalog skill paths may not contain symlinks or escapes: {identifier}")

    try:
        source = candidate.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise ValueError(f"catalog skill source could not be resolved: {identifier}") from error
    canonical_root = (root / "skills").resolve(strict=False)
    if (
        not source.is_relative_to(root)
        or not source.is_relative_to(canonical_root)
        or not source.is_dir()
    ):
        raise ValueError(f"catalog skill source must stay inside the repository: {identifier}")
    if any(path.is_symlink() for path in source.rglob("*")):
        raise ValueError(f"canonical skills may not contain symlinks: {identifier}")
    return identifier, source


def load_catalog_entries(root: Path) -> list[dict[str, object]]:
    """Load catalog entries as objects without consuming any path-bearing field."""
    root = Path(root).resolve()
    catalog = load_catalog(root / "catalog" / "skills.json")
    raw_entries = catalog.get("skills")
    if not isinstance(raw_entries, list) or not all(isinstance(entry, dict) for entry in raw_entries):
        raise ValueError("catalog skills must be a list of objects")
    return list(raw_entries)


def load_validated_catalog_entries(root: Path) -> list[dict[str, object]]:
    """Load catalog entries and validate every path-bearing field before use."""
    entries = load_catalog_entries(root)
    for entry in entries:
        validate_skill_entry(root, entry)
    return entries


def validate_unique_skill_ids(entries: Iterable[dict[str, object]]) -> None:
    """Reject duplicate IDs at the shared catalog boundary."""
    identifiers = [entry.get("id") for entry in entries]
    duplicates = sorted(
        {
            identifier
            for identifier in identifiers
            if isinstance(identifier, str) and identifiers.count(identifier) > 1
        }
    )
    if duplicates:
        raise ValueError(f"catalog contains duplicate skill IDs: {', '.join(duplicates)}")
