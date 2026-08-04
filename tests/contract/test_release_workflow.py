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
    "uv run python scripts/build_marketplace.py packages --mode check --root .",
    "scripts/build_marketplace.py site --root . --output dist-a",
    "scripts/build_marketplace.py site --root . --output dist-b",
)
PINNED_ACTIONS = (
    "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1",
    "astral-sh/setup-uv@08807647e7069bb48b6ef5acd8ec9567f424441b",
)
PINNED_ACTION_LINES = (
    "- uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1",
    "- uses: astral-sh/setup-uv@08807647e7069bb48b6ef5acd8ec9567f424441b # v8.1.0",
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


def test_readme_describes_experimental_adapter_packaging_without_portability_claim():
    """The landing page must not imply compatibility before tenant-backed evidence exists."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    introduction = readme.split("## Catalog", 1)[0].lower()

    assert "packaged for the documented experimental adapters" in introduction
    assert "tenant-backed" in introduction
    assert "portable across the documented clients" not in introduction


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
    workflow_text = workflow_path.read_text(encoding="utf-8")
    workflow = yaml.safe_load(workflow_text)
    steps = workflow["jobs"]["validate"]["steps"]
    used_actions = [step["uses"] for step in steps if "uses" in step]
    run_steps = [step["run"] for step in steps if "run" in step]
    release_checklist = (ROOT / "docs/release-checklist.md").read_text(encoding="utf-8")

    assert used_actions == list(PINNED_ACTIONS)
    assert all(line in workflow_text for line in PINNED_ACTION_LINES)
    assert all(
        any(command in step for step in run_steps) for command in REQUIRED_AUTOMATED_COMMANDS
    )
    assert all(command in release_checklist for command in REQUIRED_AUTOMATED_COMMANDS)
    assert any(
        "skills/core/* skills/extended/*" in command
        and 'uv run skills-ref validate "$skill"' in command
        for command in run_steps
    )
    assert 'uv run skills-ref validate "$skill"' in release_checklist


def test_release_checklist_covers_native_marketplace_publication_review():
    """A release review must inspect the deployed catalog and both native clients."""
    body = (ROOT / "docs/release-checklist.md").read_text(encoding="utf-8")

    assert "GitHub Pages catalog" in body
    assert "exact current commit" in body
    assert "plugin list" in body
    assert "Codex and Claude Code" in body


def test_ci_triggers_on_pull_requests_and_main_pushes():
    """Validation must run for proposed changes and every update to the release branch."""
    workflow_text = (ROOT / ".github/workflows/validate.yml").read_text(encoding="utf-8")

    assert re.search(
        r"^on:\n  pull_request:\n  push:\n    branches: \[main\]$",
        workflow_text,
        flags=re.MULTILINE,
    )


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
