import json
import re
from pathlib import Path

import pytest


ADAPTERS = {
    "codex": {
        "paths": (".agents/skills/<skill-name>/", "~/.agents/skills/<skill-name>/"),
        "commands": (
            "codex mcp add stack-internal --url https://[slug].stackenterprise.co/mcp",
            "codex mcp login stack-internal",
        ),
        "invocation": ("automatically when the request matches its description", "$skill-name", "/skills"),
        "notes": ("may register the server without opening the browser", "restart Codex"),
    },
    "claude-code": {
        "paths": (".claude/skills/<skill-name>/", "~/.claude/skills/<skill-name>/"),
        "commands": (
            "claude mcp add --transport http stack-internal https://[slug].stackenterprise.co/mcp",
            "claude mcp login stack-internal",
        ),
        "invocation": ("automatically when a request matches their descriptions", "/skill-name"),
        "notes": ("may register the server without opening the browser",),
    },
    "cursor": {
        "paths": (".cursor/skills/<skill-name>/", "~/.cursor/skills/<skill-name>/"),
        "commands": (),
        "invocation": ("automatically when a request matches their descriptions", "slash-command"),
        "notes": (),
    },
    "github-copilot": {
        "paths": (
            ".github/skills/<skill-name>/",
            "~/.copilot/skills/<skill-name>/",
            ".agents/skills/<skill-name>/",
            "~/.agents/skills/<skill-name>/",
        ),
        "commands": (),
        "invocation": ("automatic selection", "/SKILL-NAME", "Copilot CLI"),
        "notes": (),
    },
}

DOCUMENTATION_URLS = {
    "Codex": "https://learn.chatgpt.com/docs/build-skills",
    "Claude Code": "https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview",
    "Cursor": "https://cursor.com/docs/skills",
    "GitHub Copilot": "https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills",
}

SMOKE_TESTS = (
    (
        "### Smoke test 1 — Conditional search",
        "How should I structure logging in this service?",
        "`search`, then full-content retrieval for a promising result, with title and ID.",
    ),
    (
        "### Smoke test 2 — Negative trigger",
        "Write a Python function that reverses a string.",
        "no Stack Internal MCP call.",
    ),
    (
        "### Smoke test 3 — Write approval",
        "We fixed the timeout; publish a Q&A.",
        "duplicate search, valid tags, an exact local draft, and a pause before any write.",
    ),
    (
        "### Smoke test 4 — MCP failure",
        "Disconnect or deny access, then ask an internal-policy question.",
        "honest access failure and an offer to continue with clearly labeled general knowledge.",
    ),
)


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).parents[2]


def test_adapter_guides_preserve_native_install_auth_and_smoke_contracts(repo_root):
    """Catch a guide losing a scoped install, auth action, invocation, or observable smoke result."""
    catalog = json.loads((repo_root / "catalog" / "skills.json").read_text(encoding="utf-8"))
    skill_paths = [entry["path"] for entry in catalog["skills"]]

    assert len(skill_paths) == 9
    for path in skill_paths:
        assert (repo_root / path / "SKILL.md").is_file()

    for adapter, requirements in ADAPTERS.items():
        guide_path = repo_root / "adapters" / adapter / "README.md"
        body = guide_path.read_text(encoding="utf-8")

        assert all(path in body for path in requirements["paths"])
        assert all(command in body for command in requirements["commands"])
        assert all(marker in body for marker in requirements["invocation"])
        assert all(note in body for note in requirements["notes"])
        assert body.count("### Smoke test") == 4
        assert all(text in body for scenario in SMOKE_TESTS for text in scenario)
        assert "copy each complete, self-contained skill directory" in body.lower()
        assert "[slug].stackenterprise.co/mcp" in body
        assert "oauth" in body.lower()
        assert "```json" not in body.lower()
        assert "experimental" in body.lower()
        assert "adapter compatibility: supported" not in body.lower()

    assert "Claude API skill-upload" in (repo_root / "adapters" / "claude-code" / "README.md").read_text(encoding="utf-8")
    for adapter in ("cursor", "github-copilot"):
        body = (repo_root / "adapters" / adapter / "README.md").read_text(encoding="utf-8").lower()
        assert "unverified" in body
        assert "json" in body


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


def test_adapter_matrix_lists_exactly_the_catalogued_skill_directories(repo_root):
    """Catch a matrix that advertises a missing, stale, or incomplete canonical skill list."""
    catalog = json.loads((repo_root / "catalog" / "skills.json").read_text(encoding="utf-8"))
    body = (repo_root / "adapters" / "README.md").read_text(encoding="utf-8")
    documented_paths = re.findall(r"^- `(skills/(?:core|extended)/[^`/]+)/`$", body, flags=re.MULTILINE)

    assert set(documented_paths) == {entry["path"] for entry in catalog["skills"]}
    assert len(documented_paths) == len(catalog["skills"])
