import json
from pathlib import Path

import pytest


ADAPTERS = {
    "codex": [".agents/skills", "codex mcp add stack-internal"],
    "claude-code": [".claude/skills", "claude mcp add"],
    "cursor": [".cursor/skills", "stackenterprise.co/mcp"],
    "github-copilot": [".github/skills", "stackenterprise.co/mcp"],
}

DOCUMENTATION_URLS = {
    "Codex": "https://learn.chatgpt.com/docs/build-skills",
    "Claude Code": "https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview",
    "Cursor": "https://cursor.com/docs/skills",
    "GitHub Copilot": "https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills",
}

SMOKE_TESTS = (
    "### Smoke test 1 — Conditional search",
    "### Smoke test 2 — Negative trigger",
    "### Smoke test 3 — Write approval",
    "### Smoke test 4 — MCP failure",
)


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).parents[2]


def test_adapter_guides_install_all_catalogued_skills_and_keep_the_smoke_contract(repo_root):
    """Catch a guide that loses an install scope, smoke check, or canonical skill set."""
    catalog = json.loads((repo_root / "catalog" / "skills.json").read_text(encoding="utf-8"))
    skill_paths = [entry["path"] for entry in catalog["skills"]]

    assert len(skill_paths) == 9
    for path in skill_paths:
        assert (repo_root / path / "SKILL.md").is_file()

    for adapter, required_text in ADAPTERS.items():
        guide_path = repo_root / "adapters" / adapter / "README.md"
        body = guide_path.read_text(encoding="utf-8")

        assert all(text in body for text in required_text)
        assert body.count("### Smoke test") == 4
        assert all(scenario in body for scenario in SMOKE_TESTS)
        assert "copy each complete, self-contained skill directory" in body.lower()
        assert "experimental" in body.lower()
        assert "adapter compatibility: supported" not in body.lower()


def test_adapter_matrix_links_primary_docs_and_warns_paths_can_change(repo_root):
    """Catch a release guide that omits a client source of truth or freshness warning."""
    body = (repo_root / "adapters" / "README.md").read_text(encoding="utf-8")

    assert all(url in body for url in DOCUMENTATION_URLS.values())
    assert "project" in body.lower()
    assert "user" in body.lower()
    assert "re-check" in body.lower()
    assert "preview" in body.lower()
    assert "experimental" in body.lower()
    assert "adapter compatibility: supported" not in body.lower()
    assert all(
        state == "experimental"
        for entry in json.loads((repo_root / "catalog" / "skills.json").read_text(encoding="utf-8"))["skills"]
        for state in entry["adapters"].values()
    )
