"""Repository-level validation orchestration."""

from __future__ import annotations

from pathlib import Path

from .catalog import load_catalog, validate_catalog
from .skill import discover_skill_dirs, validate_skill


def validate_repository(root: Path) -> list[str]:
    """Validate a catalog repository and return stable human-readable errors."""
    root = Path(root)
    catalog_path = root / "catalog" / "skills.json"
    try:
        catalog = load_catalog(catalog_path)
    except (OSError, ValueError) as error:
        return [f"catalog could not be loaded: {error}"]

    errors = validate_catalog(root, catalog)
    skills = catalog.get("skills")
    if not isinstance(skills, list):
        return sorted(errors)
    entries = [entry for entry in skills if isinstance(entry, dict)]
    by_path = {
        entry["path"]: entry
        for entry in entries
        if isinstance(entry.get("path"), str)
    }
    discovered = discover_skill_dirs(root)
    discovered_paths = {path.relative_to(root).as_posix(): path for path in discovered}

    for path in sorted(discovered_paths):
        if path not in by_path:
            errors.append(f"skill directory is missing a catalog entry: {path}")
    for path, entry in sorted(by_path.items()):
        skill_dir = root / path
        if skill_dir.is_dir():
            errors.extend(validate_skill(root, skill_dir, entry))

    return sorted(set(errors))
