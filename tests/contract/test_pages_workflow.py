import re
from copy import deepcopy
from pathlib import Path

import yaml


ROOT = Path(__file__).parents[2]


class GitHubActionsLoader(yaml.SafeLoader):
    """Parse workflow YAML with GitHub Actions' `on` key semantics."""


GitHubActionsLoader.yaml_implicit_resolvers = deepcopy(yaml.SafeLoader.yaml_implicit_resolvers)
for first_character, resolvers in GitHubActionsLoader.yaml_implicit_resolvers.items():
    GitHubActionsLoader.yaml_implicit_resolvers[first_character] = [
        resolver for resolver in resolvers if resolver[0] != "tag:yaml.org,2002:bool"
    ]
GitHubActionsLoader.add_implicit_resolver(
    "tag:yaml.org,2002:bool",
    re.compile(r"^(?:true|True|TRUE|false|False|FALSE)$"),
    list("tTfF"),
)


def _load_pages_workflow() -> dict[str, object]:
    return yaml.load(
        (ROOT / ".github/workflows/pages.yml").read_text(encoding="utf-8"),
        Loader=GitHubActionsLoader,
    )


def test_pages_workflow_uses_pinned_actions_and_job_scoped_permissions():
    """Build has read-only access while deployment owns the Pages credentials."""
    workflow = _load_pages_workflow()
    uses = [
        step["uses"]
        for job in workflow["jobs"].values()
        for step in job.get("steps", [])
        if "uses" in step
    ]

    assert "actions/upload-pages-artifact@7b1f4a764d45c48632c6b24a0339c27f5614fb0b" in uses
    assert "actions/deploy-pages@d6db90164ac5ed86f2b6aed7e0febac5b3c0c03e" in uses
    assert all(not action.startswith("actions/configure-pages@") for action in uses)
    assert all(re.search(r"@[0-9a-f]{40}$", action) for action in uses)
    assert "permissions" not in workflow
    assert workflow["jobs"]["build"]["permissions"] == {"contents": "read"}
    assert workflow["jobs"]["deploy"]["permissions"] == {
        "pages": "write",
        "id-token": "write",
    }


def test_pages_workflow_only_builds_and_deploys_main_ref():
    """Manual dispatches must not publish an arbitrary branch or tag."""
    workflow = _load_pages_workflow()

    assert workflow["on"] == {
        "push": {"branches": ["main"]},
        "workflow_dispatch": None,
    }
    expected_guard = "github.ref == 'refs/heads/main'"
    assert workflow["jobs"]["build"]["if"] == expected_guard
    assert workflow["jobs"]["deploy"]["if"] == expected_guard


def test_validation_checks_packages_and_repeatable_site_builds():
    """CI must reject package drift and non-deterministic Pages artifacts."""
    text = (ROOT / ".github/workflows/validate.yml").read_text(encoding="utf-8")

    assert "packages --mode check --root ." in text
    assert text.count("scripts/build_marketplace.py site") == 2
    assert "diff -ru dist-a dist-b" in text
