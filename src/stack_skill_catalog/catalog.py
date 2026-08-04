"""Catalog loading and schema validation."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


_SMOKE_CHECKS = {
    1: "conditional-search-and-full-retrieval",
    2: "negative-trigger-no-mcp-call",
    3: "write-change-reapproval-and-exact-args",
    4: "honest-mcp-failure-reporting",
}


def _git_text(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def _git_bytes(root: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=False,
        check=False,
    )


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
    eligible_evidence_records: list[dict[str, Any]] = []
    evidence: object = {}
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
    release_commit = evidence.get("release_candidate_commit") if isinstance(evidence, dict) else None
    git_commit_valid = False
    if evidence_records:
        if not isinstance(release_commit, str):
            errors.append("compatibility evidence records require a release-candidate commit")
        else:
            commit_check = _git_text(root, "cat-file", "-e", f"{release_commit}^{{commit}}")
            ancestor_check = _git_text(root, "merge-base", "--is-ancestor", release_commit, "HEAD")
            git_commit_valid = commit_check.returncode == 0 and ancestor_check.returncode == 0
            if not git_commit_valid:
                errors.append(
                    "compatibility release-candidate commit must be a real ancestor commit in this Git repository"
                )

    smoke_schema_path = root / "standards" / "smoke-evidence-schema.json"
    try:
        smoke_schema = json.loads(smoke_schema_path.read_text(encoding="utf-8"))
        smoke_validator = Draft202012Validator(smoke_schema)
    except (OSError, json.JSONDecodeError) as error:
        smoke_validator = None
        errors.append(f"smoke evidence schema could not be loaded: {error}")

    designated_dir = (root / "compatibility" / "smoke-evidence").resolve()
    for record_index, record in enumerate(evidence_records):
        record_valid = git_commit_valid
        if record.get("catalog_commit") != release_commit:
            errors.append(
                f"compatibility evidence record {record_index} catalog commit does not match release candidate"
            )
            record_valid = False
        smoke_tests = record.get("smoke_tests")
        if not isinstance(smoke_tests, list):
            record_valid = False
            continue
        for smoke in smoke_tests:
            if not isinstance(smoke, dict):
                record_valid = False
                continue
            number = smoke.get("number")
            reference = smoke.get("evidence_ref")
            if not isinstance(number, int) or not isinstance(reference, str):
                record_valid = False
                continue
            relative = Path(reference)
            artifact_path = (root / relative).resolve()
            safe_path = (
                not relative.is_absolute()
                and ".." not in relative.parts
                and artifact_path.is_relative_to(designated_dir)
            )
            if not safe_path:
                errors.append(f"smoke evidence reference is outside the designated directory: {reference}")
                record_valid = False
                continue
            try:
                artifact_bytes = artifact_path.read_bytes()
                if not artifact_bytes:
                    raise ValueError("artifact is empty")
                artifact = json.loads(artifact_bytes)
            except (OSError, ValueError, json.JSONDecodeError) as error:
                errors.append(f"smoke evidence artifact could not be loaded: {reference}: {error}")
                record_valid = False
                continue
            committed = (
                _git_bytes(root, "show", f"{release_commit}:{relative.as_posix()}")
                if git_commit_valid
                else None
            )
            if committed is None or committed.returncode != 0 or committed.stdout != artifact_bytes:
                errors.append(f"smoke evidence artifact is not exact release-candidate content: {reference}")
                record_valid = False
            if smoke_validator is None:
                record_valid = False
            else:
                artifact_errors = list(smoke_validator.iter_errors(artifact))
                if artifact_errors:
                    errors.append(f"smoke evidence artifact schema violation: {reference}")
                    record_valid = False
            if not isinstance(artifact, dict) or (
                artifact.get("adapter") != record.get("adapter")
                or artifact.get("smoke_test") != number
                or artifact.get("check_id") != _SMOKE_CHECKS.get(number)
            ):
                errors.append(f"smoke evidence artifact does not match adapter/test number: {reference}")
                record_valid = False
        if record_valid:
            eligible_evidence_records.append(record)

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
                        for record in eligible_evidence_records
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
