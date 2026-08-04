import re
from pathlib import Path

import yaml


ROOT = Path(__file__).parents[2]


def test_pages_workflow_uses_pinned_actions_and_minimal_permissions():
    """A Pages deployment must retain its reviewed action revisions and scope."""
    text = (ROOT / ".github/workflows/pages.yml").read_text(encoding="utf-8")
    workflow = yaml.safe_load(text)
    uses = [
        step["uses"]
        for job in workflow["jobs"].values()
        for step in job.get("steps", [])
        if "uses" in step
    ]

    assert "actions/configure-pages@983d7736d9b0ae728b81ab479565c72886d7745b" in uses
    assert "actions/upload-pages-artifact@7b1f4a764d45c48632c6b24a0339c27f5614fb0b" in uses
    assert "actions/deploy-pages@d6db90164ac5ed86f2b6aed7e0febac5b3c0c03e" in uses
    assert all(re.search(r"@[0-9a-f]{40}$", action) for action in uses)
    assert workflow["permissions"] == {
        "contents": "read",
        "pages": "write",
        "id-token": "write",
    }


def test_validation_checks_packages_and_repeatable_site_builds():
    """CI must reject package drift and non-deterministic Pages artifacts."""
    text = (ROOT / ".github/workflows/validate.yml").read_text(encoding="utf-8")

    assert "packages --mode check --root ." in text
    assert text.count("scripts/build_marketplace.py site") == 2
    assert "diff -ru dist-a dist-b" in text
