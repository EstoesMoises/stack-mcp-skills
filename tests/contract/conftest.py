from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pytest


@dataclass
class RepoFixture:
    root: Path

    def add_skill(
        self,
        *,
        path: str = "skills/core/example-skill",
        name: str = "example-skill",
        tier: str = "core",
        write_actions: str = "none",
        body: str | None = None,
    ) -> None:
        skill_dir = self.root / path
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            "\n".join(
                [
                    "---",
                    f"name: {name}",
                    "description: Find company-specific guidance when an internal answer may help.",
                    "license: Apache-2.0",
                    "metadata:",
                    f"  stack-internal-tier: {tier}",
                    '  stack-internal-version: "0.1.0"',
                    f"  stack-internal-write-actions: {write_actions}",
                    "  stack-internal-adapters: codex,claude-code,cursor,github-copilot",
                    "---",
                    body
                    or "# Skill\n\n## Workflow\nUse the documented workflow.\n\n## Failure handling\nReport unavailable tools honestly.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        evals_dir = skill_dir / "evals"
        evals_dir.mkdir()
        catalog_write_actions = json.loads(
            (self.root / "standards" / "catalog-schema.json").read_text(encoding="utf-8")
        )["$defs"]["write_action"]["enum"]
        (evals_dir / "evals.json").write_text(
            json.dumps(
                {
                    "cases": [
                        {
                            "id": "case-one",
                            "prompt": "Find an internal policy.",
                            "expected": "Search.",
                            "forbidden_actions": catalog_write_actions,
                        },
                        {
                            "id": "case-two",
                            "prompt": "Find an incident.",
                            "expected": "Retrieve content.",
                            "forbidden_actions": catalog_write_actions,
                        },
                    ]
                }
            ),
            encoding="utf-8",
        )
        minimum = 8 if tier == "core" else 4
        (evals_dir / "trigger-evals.json").write_text(
            json.dumps(
                {
                    "positive": [f"positive {index}" for index in range(minimum)],
                    "negative": [f"negative {index}" for index in range(minimum)],
                }
            ),
            encoding="utf-8",
        )
        catalog = json.loads((self.root / "catalog" / "skills.json").read_text(encoding="utf-8"))
        catalog["skills"].append(
            {
                "id": name,
                "name": "Example Skill",
                "version": "0.1.0",
                "tier": tier,
                "summary": "Find company-specific guidance.",
                "path": path,
                "tags": ["example"],
                "required_tools": ["search"],
                "write_actions": [] if write_actions == "none" else write_actions.split(","),
                "adapters": {
                    "codex": "experimental",
                    "claude-code": "experimental",
                    "cursor": "experimental",
                    "github-copilot": "experimental",
                },
            }
        )
        (self.root / "catalog" / "skills.json").write_text(
            json.dumps(catalog), encoding="utf-8"
        )


@pytest.fixture
def repo_fixture(tmp_path: Path) -> RepoFixture:
    root = tmp_path / "repo"
    (root / "catalog").mkdir(parents=True)
    (root / "standards").mkdir()
    (root / "compatibility").mkdir()
    (root / "catalog" / "skills.json").write_text(
        json.dumps({"catalog_version": "1.0.0", "skills": []}), encoding="utf-8"
    )
    (root / "standards" / "catalog-schema.json").write_text(
        (Path(__file__).parents[2] / "standards" / "catalog-schema.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (root / "standards" / "adapter-evidence-schema.json").write_text(
        (Path(__file__).parents[2] / "standards" / "adapter-evidence-schema.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (root / "compatibility" / "evidence.json").write_text(
        json.dumps({"schema_version": "1.0.0", "records": []}), encoding="utf-8"
    )
    return RepoFixture(root)
