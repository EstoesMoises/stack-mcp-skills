"""Catalog loading and schema validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


def load_catalog(path: Path) -> dict[str, object]:
    """Load a catalog JSON object from *path*."""
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("catalog must be a JSON object")
    return value


def validate_catalog(root: Path, catalog: dict[str, object]) -> list[str]:
    """Return deterministic structural and repository errors for *catalog*."""
    errors: list[str] = []
    schema_path = root / "standards" / "catalog-schema.json"
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return [f"catalog schema could not be loaded: {error}"]

    validator = Draft202012Validator(schema)
    for error in sorted(validator.iter_errors(catalog), key=lambda item: (list(item.absolute_path), item.message)):
        location = ".".join(str(part) for part in error.absolute_path) or "root"
        errors.append(f"catalog schema violation at {location}: {error.message}")

    skills = catalog.get("skills")
    if not isinstance(skills, list):
        return sorted(errors)

    entries = [entry for entry in skills if isinstance(entry, dict)]
    evidence_records: list[dict[str, Any]] = []
    evidence_path = root / "compatibility" / "evidence.json"
    evidence_schema_path = root / "standards" / "adapter-evidence-schema.json"
    try:
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        evidence_schema = json.loads(evidence_schema_path.read_text(encoding="utf-8"))
        evidence_validator = Draft202012Validator(evidence_schema)
        for error in sorted(
            evidence_validator.iter_errors(evidence),
            key=lambda item: (list(item.absolute_path), item.message),
        ):
            location = ".".join(str(part) for part in error.absolute_path) or "root"
            errors.append(f"compatibility evidence schema violation at {location}: {error.message}")
        if isinstance(evidence, dict) and isinstance(evidence.get("records"), list):
            evidence_records = [record for record in evidence["records"] if isinstance(record, dict)]
    except (OSError, json.JSONDecodeError) as error:
        errors.append(f"compatibility evidence could not be loaded: {error}")
    for field in ("id", "path"):
        values = [entry.get(field) for entry in entries]
        duplicates = sorted({value for value in values if values.count(value) > 1 and isinstance(value, str)})
        errors.extend(f"catalog contains duplicate {field}: {value}" for value in duplicates)

    for entry in entries:
        path = entry.get("path")
        if isinstance(path, str) and not (root / path).is_dir():
            errors.append(f"catalog skill path does not exist: {path}")
        if isinstance(path, str):
            parts = Path(path).parts
            path_tier = parts[1] if len(parts) >= 3 and parts[0] == "skills" else None
            if path_tier in {"core", "extended"} and entry.get("tier") != path_tier:
                errors.append(
                    "catalog tier does not match skill path: "
                    f"{entry.get('id')} ({entry.get('tier')} != {path_tier})"
                )
        required_tools = entry.get("required_tools")
        write_actions = entry.get("write_actions")
        if isinstance(required_tools, list) and isinstance(write_actions, list):
            missing_actions = sorted(
                {
                    action
                    for action in write_actions
                    if isinstance(action, str) and action not in required_tools
                }
            )
            if missing_actions:
                errors.append(
                    "catalog write actions must be included in required_tools: "
                    f"{entry.get('id')} (missing: {', '.join(missing_actions)})"
                )
        adapters = entry.get("adapters")
        if isinstance(adapters, dict):
            for adapter, state in adapters.items():
                if state == "supported":
                    matching = [
                        record
                        for record in evidence_records
                        if record.get("adapter") == adapter
                        and record.get("skill_id") == entry.get("id")
                        and record.get("skill_version") == entry.get("version")
                        and record.get("tenant_purpose") == "non-production skill validation"
                        and [test.get("number") for test in record.get("smoke_tests", []) if isinstance(test, dict)]
                        == [1, 2, 3, 4]
                        and all(
                            test.get("passed") is True
                            for test in record.get("smoke_tests", [])
                            if isinstance(test, dict)
                        )
                    ]
                    if not matching:
                        errors.append(f"adapter support requires tenant-backed smoke-test evidence: {adapter}")

    return sorted(errors)
