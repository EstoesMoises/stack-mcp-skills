from __future__ import annotations

import json
import re
from pathlib import Path

import yaml


ROOT = Path(__file__).parents[2]
REQUIRED_AUTOMATED_COMMANDS = (
    "uv sync --locked --dev",
    "uv run pytest -q",
    "uv run python scripts/validate_catalog.py .",
)


def _markdown_links(path: Path) -> list[str]:
    return re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", path.read_text(encoding="utf-8"))


def test_readme_catalog_table_matches_catalog():
    """A catalog addition, rename, or tier change must reach the public inventory."""
    catalog = json.loads((ROOT / "catalog" / "skills.json").read_text(encoding="utf-8"))
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    rows = re.findall(
        r"^\| (Core|Extended) \| \[([^\]]+)\]\((skills/(?:core|extended)/[^)]+/)\) \| ([^|]+?) \|$",
        readme,
        flags=re.MULTILINE,
    )
    documented = {
        path.removesuffix("/"): {
            "tier": tier.lower(),
            "name": name,
            "summary": summary,
        }
        for tier, name, path, summary in rows
    }
    expected = {
        entry["path"]: {
            "tier": entry["tier"],
            "name": entry["name"],
            "summary": entry["summary"],
        }
        for entry in catalog["skills"]
    }

    assert documented == expected


def test_public_document_relative_links_resolve():
    """Public navigation may not point to missing repository artifacts."""
    documents = (
        ROOT / "README.md",
        ROOT / "CONTRIBUTING.md",
        ROOT / "docs/release-checklist.md",
    )

    for document in documents:
        for target in _markdown_links(document):
            path_part = target.split("#", 1)[0]
            if not path_part or "://" in path_part or path_part.startswith("mailto:"):
                continue
            assert (document.parent / path_part).exists(), f"broken link in {document}: {target}"


def test_ci_runs_every_automated_release_gate():
    """A green CI run must exercise every locally documented automated gate."""
    workflow_path = ROOT / ".github/workflows/validate.yml"
    workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
    steps = workflow["jobs"]["validate"]["steps"]
    used_actions = [step["uses"] for step in steps if "uses" in step]
    run_steps = [step["run"] for step in steps if "run" in step]
    release_checklist = (ROOT / "docs/release-checklist.md").read_text(encoding="utf-8")

    assert used_actions == ["actions/checkout@v4", "astral-sh/setup-uv@v6"]
    assert all(command in run_steps for command in REQUIRED_AUTOMATED_COMMANDS)
    assert all(command in release_checklist for command in REQUIRED_AUTOMATED_COMMANDS)
    assert any(
        "skills/core/* skills/extended/*" in command
        and 'uv run skills-ref validate "$skill"' in command
        for command in run_steps
    )
    assert 'uv run skills-ref validate "$skill"' in release_checklist


def test_contribution_contract_states_eval_and_resource_requirements():
    """Contributors must receive the tier-sensitive eval and portability contract."""
    body = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")

    assert "one coherent user goal" in body.lower()
    assert "extended tier by default" in body.lower()
    assert "two or three output evals" in body.lower()
    assert re.search(r"core.*at least eight positive.*eight negative", body, flags=re.IGNORECASE | re.DOTALL)
    assert re.search(r"extended.*at least four positive.*four negative", body, flags=re.IGNORECASE | re.DOTALL)
    assert "one reference hop" in body.lower()
    assert "no empty optional directories" in body.lower()
    assert "current live input schema" in body.lower()
    assert "changed payload requires new approval" in body.lower()


def test_release_gates_separate_local_review_from_tenant_evidence():
    """No adapter can be promoted from simulated or manual-only evidence."""
    body = (ROOT / "docs/release-checklist.md").read_text(encoding="utf-8")

    headings = re.findall(r"^## (.+)$", body, flags=re.MULTILINE)
    assert "Automated gates" in headings
    assert "Manual no-tenant review" in headings
    assert "Tenant-backed release gate" in headings
    for field in ("Date", "Client version", "Skill version", "Pass/fail", "Notes"):
        assert field in body
    assert "all four adapter smoke tests" in body.lower()
    assert "authorized test tenant" in body.lower()
    assert re.search(
        r"must not be (?:marked|promoted).*`supported`.*until.*tenant-backed release gate passes",
        body,
        flags=re.IGNORECASE | re.DOTALL,
    )
