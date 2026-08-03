from __future__ import annotations

import json
from pathlib import Path

from stack_skill_catalog.validation import validate_repository


def test_established_company_debugging_eval_requires_matching_runtime_evidence_and_label():
    """Prevent the established-practice eval from accepting an unsupported label."""
    eval_path = Path(__file__).parents[2] / "skills/core/company-debugging/evals/evals.json"
    cases = json.loads(eval_path.read_text(encoding="utf-8"))["cases"]
    case = next(item for item in cases if item["id"] == "accepted-internal-service-timeout-practice")

    assert case.get("runtime_evidence") == {
        "code": "The retry wrapper encloses the Ledger commit.",
        "traces": "Production traces show each Ledger commit retried inside that wrapper.",
    }
    assert "Label the diagnosis `established-company-practice`." in case["expected"]


def test_write_skill_requires_approval_gate(repo_fixture):
    repo_fixture.add_skill(write_actions="create_QA", body="# Skill\n\n## Workflow\nDraft content.")

    assert "write-capable skill must contain ## Approval gate" in validate_repository(repo_fixture.root)


def test_valid_skill_fixture_passes(repo_fixture):
    repo_fixture.add_skill()

    assert validate_repository(repo_fixture.root) == []


def test_optional_resource_directory_must_be_populated_and_linked(repo_fixture):
    repo_fixture.add_skill()
    (repo_fixture.root / "skills/core/example-skill/references").mkdir()

    assert "optional directory must be non-empty: references" in validate_repository(repo_fixture.root)


def test_allowed_tools_is_forbidden(repo_fixture):
    repo_fixture.add_skill()
    skill_file = repo_fixture.root / "skills/core/example-skill/SKILL.md"
    skill_file.write_text(
        skill_file.read_text(encoding="utf-8").replace("license: Apache-2.0", "allowed-tools: search\nlicense: Apache-2.0"),
        encoding="utf-8",
    )

    assert "allowed-tools field is not permitted" in validate_repository(repo_fixture.root)


def test_required_sections_must_use_exact_headings(repo_fixture):
    repo_fixture.add_skill()
    skill_file = repo_fixture.root / "skills/core/example-skill/SKILL.md"
    skill_file.write_text(
        skill_file.read_text(encoding="utf-8").replace("## Workflow", "## Workflow notes"),
        encoding="utf-8",
    )

    assert "SKILL.md must contain ## Workflow" in validate_repository(repo_fixture.root)


def test_approval_gate_must_use_exact_heading(repo_fixture):
    repo_fixture.add_skill(
        write_actions="create_QA",
        body="# Skill\n\n## Workflow\nDraft content.\n\n## Failure handling\nReport failures.\n\n## Approval gatekeeping\nAsk first.",
    )

    assert "write-capable skill must contain ## Approval gate" in validate_repository(repo_fixture.root)


def test_license_must_be_apache_2(repo_fixture):
    repo_fixture.add_skill()
    skill_file = repo_fixture.root / "skills/core/example-skill/SKILL.md"
    skill_file.write_text(
        skill_file.read_text(encoding="utf-8").replace("license: Apache-2.0", "license: MIT"),
        encoding="utf-8",
    )

    assert "license must be Apache-2.0" in validate_repository(repo_fixture.root)


def test_metadata_keys_must_use_the_project_namespace(repo_fixture):
    repo_fixture.add_skill()
    skill_file = repo_fixture.root / "skills/core/example-skill/SKILL.md"
    skill_file.write_text(
        skill_file.read_text(encoding="utf-8").replace("metadata:\n", "metadata:\n  unscoped: value\n"),
        encoding="utf-8",
    )

    assert "metadata keys must start with stack-internal-: unscoped" in validate_repository(repo_fixture.root)


def test_metadata_values_must_be_strings(repo_fixture):
    repo_fixture.add_skill()
    skill_file = repo_fixture.root / "skills/core/example-skill/SKILL.md"
    skill_file.write_text(
        skill_file.read_text(encoding="utf-8").replace('stack-internal-version: "0.1.0"', "stack-internal-version: 1"),
        encoding="utf-8",
    )

    assert "metadata values must be strings: stack-internal-version" in validate_repository(repo_fixture.root)


def test_markdown_image_link_counts_as_an_asset_reference(repo_fixture):
    repo_fixture.add_skill()
    skill_dir = repo_fixture.root / "skills/core/example-skill"
    assets_dir = skill_dir / "assets"
    assets_dir.mkdir()
    (assets_dir / "diagram.png").write_bytes(b"PNG")
    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text(
        f"{skill_file.read_text(encoding='utf-8')}\n![Workflow diagram](assets/diagram.png)\n",
        encoding="utf-8",
    )

    assert validate_repository(repo_fixture.root) == []


def test_read_only_skill_evals_must_forbid_every_catalog_write_action(repo_fixture):
    repo_fixture.add_skill()
    eval_path = repo_fixture.root / "skills/core/example-skill/evals/evals.json"
    evals = json.loads(eval_path.read_text(encoding="utf-8"))
    evals["cases"][0]["forbidden_actions"] = ["create_question"]
    eval_path.write_text(json.dumps(evals), encoding="utf-8")

    assert (
        "read-only eval case must forbid all catalog write actions: case-one "
        "(missing: create_QA, create_article, draft_question, submit_user_answer, "
        "update_answer, update_question, vote)"
    ) in validate_repository(repo_fixture.root)
