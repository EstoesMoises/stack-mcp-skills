"""Skill discovery and validation."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import yaml
from skills_ref import validate as validate_agent_skill


_OPTIONAL_DIRECTORIES = ("references", "scripts", "assets")
_REQUIRED_SECTIONS = ("## Workflow", "## Failure handling")
_LINK_PATTERN = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")
_PLACEHOLDER_PATTERN = re.compile(r"\b(?:TODO|TBD)\b|\{\{|\}\}|<placeholder>|\[insert[^\]]*\]|lorem ipsum", re.IGNORECASE)


def discover_skill_dirs(root: Path) -> list[Path]:
    """Return sorted skill directories that contain a canonical SKILL.md."""
    skills_root = root / "skills"
    if not skills_root.is_dir():
        return []
    return sorted(
        (path.parent for path in skills_root.rglob("SKILL.md") if path.is_file()),
        key=lambda path: path.relative_to(root).as_posix(),
    )


def load_frontmatter(skill_dir: Path) -> tuple[dict[str, object], str]:
    """Load YAML frontmatter and the Markdown body from a skill."""
    skill_path = skill_dir / "SKILL.md"
    content = skill_path.read_text(encoding="utf-8")
    if not content.startswith("---"):
        raise ValueError("SKILL.md must start with YAML frontmatter")
    parts = content.split("---", 2)
    if len(parts) < 3:
        raise ValueError("SKILL.md frontmatter is not closed")
    metadata = yaml.safe_load(parts[1])
    if not isinstance(metadata, dict):
        raise ValueError("SKILL.md frontmatter must be an object")
    return metadata, parts[2].strip()


def _as_actions(value: object) -> list[str] | None:
    if not isinstance(value, str):
        return None
    if value.strip() == "none":
        return []
    return [action.strip() for action in value.split(",") if action.strip()]


def _json_object(path: Path, description: str, errors: list[str]) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        errors.append(f"{description} is invalid JSON: {error}")
        return None
    if not isinstance(value, dict):
        errors.append(f"{description} must be a JSON object")
        return None
    return value


def _local_links(body: str) -> list[str]:
    links: list[str] = []
    for target in _LINK_PATTERN.findall(body):
        target = target.strip().split("#", 1)[0]
        if not target or "://" in target or target.startswith("mailto:"):
            continue
        links.append(target)
    return links


def _validate_resources(skill_dir: Path, body: str, errors: list[str]) -> None:
    links = _local_links(body)
    for link in links:
        link_path = Path(link)
        if link_path.is_absolute() or ".." in link_path.parts:
            errors.append(f"local resource link must stay within skill root: {link}")
            continue
        if len(link_path.parts) != 2 or link_path.parts[0] not in _OPTIONAL_DIRECTORIES:
            errors.append(f"local resource link must be one hop deep: {link}")
            continue
        if not (skill_dir / link_path).is_file():
            errors.append(f"local resource link does not exist: {link}")

    for directory_name in _OPTIONAL_DIRECTORIES:
        directory = skill_dir / directory_name
        if not directory.exists():
            continue
        files = sorted(path for path in directory.rglob("*") if path.is_file())
        if not files:
            errors.append(f"optional directory must be non-empty: {directory_name}")
            continue
        for resource in files:
            relative = resource.relative_to(skill_dir).as_posix()
            if len(Path(relative).parts) != 2:
                errors.append(f"local resource must be one hop deep: {relative}")
            elif relative not in links:
                errors.append(f"local resource must be linked from SKILL.md: {relative}")


def _validate_evals(skill_dir: Path, tier: object, errors: list[str]) -> None:
    evals_dir = skill_dir / "evals"
    eval_cases = _json_object(evals_dir / "evals.json", "evals/evals.json", errors)
    if eval_cases is not None:
        cases = eval_cases.get("cases")
        if not isinstance(cases, list) or len(cases) < 2:
            errors.append("evals/evals.json must contain at least two cases")
        elif any(
            not isinstance(case, dict)
            or not all(isinstance(case.get(field), str) and case[field] for field in ("id", "prompt", "expected"))
            for case in cases
        ):
            errors.append("each eval case must include non-empty id, prompt, and expected strings")

    trigger_cases = _json_object(evals_dir / "trigger-evals.json", "evals/trigger-evals.json", errors)
    if trigger_cases is not None:
        minimum = 8 if tier == "core" else 4
        for key in ("positive", "negative"):
            cases = trigger_cases.get(key)
            if not isinstance(cases, list) or len(cases) < minimum or not all(
                isinstance(case, str) and case.strip() for case in cases
            ):
                errors.append(f"evals/trigger-evals.json must contain at least {minimum} {key} cases")


def validate_skill(root: Path, skill_dir: Path, catalog_entry: dict[str, object]) -> list[str]:
    """Return deterministic contract errors for one catalogued skill."""
    errors: list[str] = []
    try:
        metadata, body = load_frontmatter(skill_dir)
    except (OSError, ValueError, yaml.YAMLError) as error:
        return [f"could not read SKILL.md: {error}"]

    errors.extend(f"skills-ref: {error}" for error in validate_agent_skill(skill_dir))
    name = metadata.get("name")
    if name != skill_dir.name:
        errors.append(f"name must match parent directory: {skill_dir.name}")
    if name != catalog_entry.get("id"):
        errors.append(f"name must match catalog id: {catalog_entry.get('id')}")

    content = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    if len(content.splitlines()) > 500:
        errors.append("SKILL.md must not exceed 500 lines")
    if len(content) > 20_000:
        errors.append("SKILL.md must not exceed 20000 characters")
    errors.extend(f"SKILL.md must contain {section}" for section in _REQUIRED_SECTIONS if section not in body)

    if "allowed-tools" in metadata:
        errors.append("allowed-tools field is not permitted")
    if _PLACEHOLDER_PATTERN.search(content):
        errors.append("SKILL.md must not contain placeholder markers")

    skill_metadata = metadata.get("metadata")
    if not isinstance(skill_metadata, dict):
        errors.append("metadata must be an object")
        skill_metadata = {}
    required_metadata = {
        "stack-internal-tier": catalog_entry.get("tier"),
        "stack-internal-version": catalog_entry.get("version"),
    }
    for key, expected in required_metadata.items():
        if skill_metadata.get(key) != expected:
            errors.append(f"metadata {key} must match catalog")

    expected_actions = catalog_entry.get("write_actions")
    actual_actions = _as_actions(skill_metadata.get("stack-internal-write-actions"))
    if not isinstance(expected_actions, list) or actual_actions is None or sorted(actual_actions) != sorted(expected_actions):
        errors.append("metadata stack-internal-write-actions must match catalog")
    elif expected_actions and "## Approval gate" not in body:
        errors.append("write-capable skill must contain ## Approval gate")

    expected_adapters = catalog_entry.get("adapters")
    actual_adapters = skill_metadata.get("stack-internal-adapters")
    if not isinstance(expected_adapters, dict) or not isinstance(actual_adapters, str) or {
        adapter.strip() for adapter in actual_adapters.split(",") if adapter.strip()
    } != set(expected_adapters):
        errors.append("metadata stack-internal-adapters must match catalog")

    _validate_resources(skill_dir, body, errors)
    _validate_evals(skill_dir, catalog_entry.get("tier"), errors)
    return sorted(set(errors))
