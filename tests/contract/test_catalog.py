from __future__ import annotations

import json
from pathlib import Path

from stack_skill_catalog.catalog import load_catalog
from stack_skill_catalog.validation import validate_repository


def test_valid_empty_catalog_passes(repo_fixture):
    assert validate_repository(repo_fixture.root) == []


def test_name_must_match_parent(repo_fixture):
    repo_fixture.add_skill(path="skills/core/right-name", name="wrong-name")

    assert "name must match parent directory: right-name" in validate_repository(repo_fixture.root)


def test_catalog_loader_returns_catalog_object(repo_fixture):
    catalog = load_catalog(repo_fixture.root / "catalog" / "skills.json")

    assert catalog == {"catalog_version": "1.0.0", "skills": []}


def test_catalog_rejects_unknown_tools(repo_fixture):
    catalog_path = repo_fixture.root / "catalog" / "skills.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    catalog["skills"].append(
        {
            "id": "example-skill",
            "name": "Example Skill",
            "version": "0.1.0",
            "tier": "core",
            "summary": "Find company-specific guidance.",
            "path": "skills/core/example-skill",
            "tags": ["example"],
            "required_tools": ["not-a-tool"],
            "write_actions": [],
            "adapters": {
                "codex": "experimental",
                "claude-code": "experimental",
                "cursor": "experimental",
                "github-copilot": "experimental",
            },
        }
    )
    catalog_path.write_text(json.dumps(catalog), encoding="utf-8")

    assert any("not-a-tool" in error for error in validate_repository(repo_fixture.root))


def test_adapter_support_requires_tenant_backed_smoke_test_evidence(repo_fixture):
    repo_fixture.add_skill()
    catalog_path = repo_fixture.root / "catalog" / "skills.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    catalog["skills"][0]["adapters"]["codex"] = "supported"
    catalog_path.write_text(json.dumps(catalog), encoding="utf-8")

    assert "adapter support requires tenant-backed smoke-test evidence: codex" in validate_repository(repo_fixture.root)


def test_catalog_rejects_duplicate_array_items(repo_fixture):
    """A repeated capability should not create an ambiguous catalog contract."""
    repo_fixture.add_skill()
    catalog_path = repo_fixture.root / "catalog" / "skills.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    catalog["skills"][0]["required_tools"] = ["search", "search"]
    catalog_path.write_text(json.dumps(catalog), encoding="utf-8")

    errors = validate_repository(repo_fixture.root)

    assert any("required_tools" in error and "non-unique" in error for error in errors)


def test_catalog_requires_write_actions_to_be_required_tools(repo_fixture):
    """A declared write cannot be permitted without being a required capability."""
    repo_fixture.add_skill()
    catalog_path = repo_fixture.root / "catalog" / "skills.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    catalog["skills"][0]["write_actions"] = ["create_QA"]
    catalog_path.write_text(json.dumps(catalog), encoding="utf-8")

    assert (
        "catalog write actions must be included in required_tools: example-skill "
        "(missing: create_QA)"
    ) in validate_repository(repo_fixture.root)


def test_initial_release_has_one_core_and_three_extended():
    root = Path(__file__).parents[2]
    catalog = load_catalog(root / "catalog" / "skills.json")
    tiers = [entry["tier"] for entry in catalog["skills"]]

    assert tiers.count("core") == 1
    assert tiers.count("extended") == 3


def test_all_documented_mcp_tools_are_known():
    root = Path(__file__).parents[2]
    schema = json.loads((root / "standards" / "catalog-schema.json").read_text(encoding="utf-8"))
    expected = {
        "search",
        "get_question",
        "get_article",
        "get_comments",
        "get_questions_to_answer",
        "get_existing_tags",
        "recommend_SME",
        "create_article",
        "create_question",
        "create_QA",
        "draft_question",
        "submit_user_answer",
        "update_answer",
        "update_question",
        "vote",
    }

    assert set(schema["$defs"]["tool"]["enum"]) == expected


def test_catalog_write_actions_are_known_required_tools():
    root = Path(__file__).parents[2]
    catalog = load_catalog(root / "catalog" / "skills.json")
    schema = json.loads((root / "standards" / "catalog-schema.json").read_text(encoding="utf-8"))
    known_write_actions = set(schema["$defs"]["write_action"]["enum"])

    for entry in catalog["skills"]:
        assert set(entry["write_actions"]) <= known_write_actions
        assert set(entry["write_actions"]) <= set(entry["required_tools"])
