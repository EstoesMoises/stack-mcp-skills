from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import re

from stack_skill_catalog.validation import validate_repository


ROOT = Path(__file__).parents[2]
WRITE_ACTIONS = (
    "draft_question",
    "create_question",
    "create_QA",
    "create_article",
    "submit_user_answer",
    "update_question",
    "update_answer",
    "vote",
)
ONBOARDING_TOPICS = (
    "prerequisites",
    "setup",
    "architecture",
    "workflows",
    "first-tasks",
)


def _cases(path: str) -> list[dict[str, object]]:
    return json.loads((ROOT / path / "evals/evals.json").read_text(encoding="utf-8"))["cases"]


def _skill(path: str) -> str:
    return (ROOT / path / "SKILL.md").read_text(encoding="utf-8")


def test_uncertainty_guardrail_is_local_first_read_only_and_partial_progress_safe():
    path = "skills/core/uncertainty-guardrail"
    body = _skill(path)
    cases = {case["id"]: case for case in _cases(path)}
    triggers = json.loads((ROOT / path / "evals/trigger-evals.json").read_text(encoding="utf-8"))

    assert {"supported", "conflicting", "unknown"} <= set(re.findall(r"`([^`]+)`", body))
    assert "If local evidence establishes it" in body
    assert "Continue the supported, safe portion" in body
    assert "access or retrieval failed" in body
    assert "This workflow performs no Stack Internal writes." in body
    assert len(triggers["positive"]) >= 8
    assert len(triggers["negative"]) >= 8
    assert not set(triggers["positive"]) & set(triggers["negative"])

    local = cases["local-evidence-is-sufficient"]
    assert "makes no Stack Internal call" in local["expected"]
    partial = cases["partial-permission-decision"]
    assert "leaves that permission unchanged" in partial["expected"]
    failed = cases["internal-access-fails"]
    assert "classifies the decision as unknown" in failed["expected"]
    assert "does not treat failure as a knowledge gap" in failed["expected"]
    for case in cases.values():
        assert case["forbidden_actions"] == list(WRITE_ACTIONS)


def test_onboarding_composes_a_bounded_five_topic_path():
    path = "skills/extended/onboarding"
    body = _skill(path)
    cases = _cases(path)
    template = (ROOT / path / "assets/learning-path-template.md").read_text(encoding="utf-8")

    for topic in ONBOARDING_TOPICS:
        assert topic.replace("-", " ") in body.lower()
        assert topic.replace("-", " ") in template.lower()

    for case in cases:
        attempts = case["search_attempts"]
        sequence = case["expected_tool_sequence"]
        responses = case["simulated_mcp"]["search"]
        assert len([step for step in sequence if step.startswith("search:")]) == len(attempts)
        counts = Counter(attempt["topic"] for attempt in attempts)
        assert set(counts) == set(ONBOARDING_TOPICS)
        assert all(count <= 3 for count in counts.values())
        assert {attempt["result_key"] for attempt in attempts} == set(responses)

        for topic in case["missing_topics"]:
            topic_attempts = [attempt for attempt in attempts if attempt["topic"] == topic]
            assert len(topic_attempts) == 3
            assert all(responses[attempt["result_key"]] == [] for attempt in topic_attempts)
            assert f"Missing coverage: {topic}" in case["expected"]

        if len(attempts) > 8:
            assert case["budget_checkpoint"] == {
                "after_search_call": 8,
                "before_search_call": 9,
                "disclosure_step": "disclose_whole_path_budget",
                "confirmation_step": "user_confirms_continue",
            }
        assert case["forbidden_actions"] == list(WRITE_ACTIONS)


def test_incident_workflow_adds_verified_fact_and_format_judgment_with_live_schemas():
    path = "skills/extended/incident-to-knowledge"
    body = _skill(path)
    cases = {case["id"]: case for case in _cases(path)}

    assert "Reject a speculative root cause" in body
    assert "article versus Q&A" in body
    assert "changed payload requires new approval" in body

    article = cases["verified-load-balancer-outage-article"]
    article_payload = article["expected_local_payload"]
    article_args = article_payload["intended_action"]["args"]
    assert article_payload["article_type"] == "KnowledgeArticle"
    assert article_args["articleType"] == article_payload["article_type"]
    assert set(article_args) == set(article["simulated_write_tool_schema"]["input_schema"]["required"])

    qa = cases["related-incident-changes-prevention-actions"]
    qa_payload = qa["expected_local_payload"]
    qa_args = qa_payload["intended_action"]["args"]
    assert qa_args["body"] == qa_payload["question"]
    assert qa_args["draftReviewed"] is True
    assert qa_payload["draftReviewed"] is True
    assert set(qa_args) == set(qa["simulated_write_tool_schema"]["input_schema"]["required"])

    unresolved = cases["unresolved-incident-must-not-publish"]
    assert "expected_local_payload" not in unresolved
    assert "must not publish" in unresolved["expected"]
    unclear = cases["unclear-incident-format-requires-user-choice"]
    assert unclear["expected_tool_sequence"][-1] == "ask_user_to_choose_article_or_qa"
    assert "expected_local_payload" not in unclear
    lost = cases["response-lost-after-success"]
    assert lost["expected_tool_sequence"][-1] == "confirmed_no_retry"

    for case in cases.values():
        assert case["forbidden_actions"] == list(WRITE_ACTIONS)


def test_stale_review_requires_independent_evidence_classification_and_edit_eligibility():
    path = "skills/extended/review-stale-content"
    body = _skill(path)
    cases = {case["id"]: case for case in _cases(path)}

    assert "confirmed-divergence" in body
    assert "possible-divergence" in body
    assert "still-current" in body
    assert "confirm that the connected update tool permits the authenticated user to edit it" in body
    assert "edit ownership or eligibility cannot be established" in body

    editable_answer = cases["jenkins-guidance-after-verified-github-actions-migration"]
    editable_question = cases["deprecated-webhook-question-removes-sensitive-data"]
    not_editable = cases["confirmed-divergence-target-not-editable"]
    assert editable_answer["classification"] == "confirmed-divergence"
    assert editable_answer["simulated_edit_eligibility"]["established"] is True
    assert editable_question["classification"] == "confirmed-divergence"
    assert editable_question["simulated_edit_eligibility"]["established"] is True
    assert not_editable["classification"] == "confirmed-divergence"
    assert not_editable["simulated_edit_eligibility"]["established"] is False
    assert "expected_local_payload" not in not_editable
    assert "without rendering an approval-ready update payload" in not_editable["expected"]
    assert cases["old-article-remains-accurate"]["classification"] == "still-current"
    assert cases["conflicting-sources-require-human-resolution"]["classification"] == "possible-divergence"

    for case in cases.values():
        assert case["forbidden_actions"] == list(WRITE_ACTIONS)
        if "expected_local_payload" not in case:
            continue
        action = case["expected_local_payload"]["intended_action"]
        schema = case["simulated_write_tool_schema"]
        assert action["tool"] == schema["tool"]
        assert set(action["args"]) == set(schema["input_schema"]["required"])

    lost = cases["response-lost-after-success"]
    assert lost["expected_tool_sequence"][-1] == "confirmed_no_retry"


def test_write_skill_requires_approval_gate(repo_fixture):
    repo_fixture.add_skill(write_actions="create_QA", body="# Skill\n\n## Workflow\nDraft content.")

    assert "write-capable skill must contain ## Approval gate" in validate_repository(repo_fixture.root)


def test_every_retained_write_action_is_covered_by_exact_approval():
    catalog = json.loads((ROOT / "catalog/skills.json").read_text(encoding="utf-8"))

    for entry in catalog["skills"]:
        if not entry["write_actions"]:
            continue
        body = _skill(entry["path"])
        approval_match = re.search(
            r"^## Approval gate\s*$\n(?P<section>.*?)(?=^## |\Z)",
            body,
            flags=re.MULTILINE | re.DOTALL,
        )
        assert approval_match, f"missing exact approval section: {entry['id']}"
        approval_section = approval_match.group("section")
        assert "changed payload requires new approval" in approval_section.lower()
        for action in entry["write_actions"]:
            assert f"`{action}`" in approval_section


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
        skill_file.read_text(encoding="utf-8").replace(
            "license: Apache-2.0", "allowed-tools: search\nlicense: Apache-2.0"
        ),
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
        body=(
            "# Skill\n\n## Workflow\nDraft content.\n\n## Failure handling\nReport failures.\n\n"
            "## Approval gatekeeping\nAsk first."
        ),
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
        skill_file.read_text(encoding="utf-8").replace(
            "metadata:\n", "metadata:\n  unscoped: value\n"
        ),
        encoding="utf-8",
    )

    assert "metadata keys must start with stack-internal-: unscoped" in validate_repository(repo_fixture.root)


def test_metadata_values_must_be_strings(repo_fixture):
    repo_fixture.add_skill()
    skill_file = repo_fixture.root / "skills/core/example-skill/SKILL.md"
    skill_file.write_text(
        skill_file.read_text(encoding="utf-8").replace(
            'stack-internal-version: "0.1.0"', "stack-internal-version: 1"
        ),
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
