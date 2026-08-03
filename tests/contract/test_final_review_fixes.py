from __future__ import annotations

import json
from pathlib import Path

from stack_skill_catalog.validation import validate_repository


ROOT = Path(__file__).parents[2]
WRITE_SKILLS = (
    "skills/core/capture-quality-qa",
    "skills/extended/incident-to-knowledge",
    "skills/extended/fill-knowledge-gap",
    "skills/extended/review-stale-content",
    "skills/extended/triage-unanswered",
)
ALL_WRITES = {
    "draft_question", "create_question", "create_QA", "create_article",
    "submit_user_answer", "update_question", "update_answer", "vote",
}


def _cases(skill: str) -> list[dict[str, object]]:
    return json.loads((ROOT / skill / "evals/evals.json").read_text(encoding="utf-8"))["cases"]


def test_all_write_skills_define_response_lost_reconciliation_and_fresh_approval():
    for skill in WRITE_SKILLS:
        body = (ROOT / skill / "SKILL.md").read_text(encoding="utf-8").lower()
        retry_cases = [case for case in _cases(skill) if case["id"] == "response-lost-after-success"]

        assert "response is lost" in body
        assert "read-only" in body and "reconcile" in body
        assert "fresh explicit approval" in body
        assert len(retry_cases) == 1
        case = retry_cases[0]
        assert set(case["forbidden_actions"]) == ALL_WRITES
        assert "reconcile" in str(case["expected"]).lower()
        assert "fresh explicit approval" in str(case["expected"]).lower()

    policy = (ROOT / "standards/policy-contract.md").read_text(encoding="utf-8").lower()
    assert "ambiguous write outcome" in policy
    assert "fresh explicit approval" in policy


def test_every_preapproval_eval_forbids_complete_catalog_write_set():
    catalog = json.loads((ROOT / "catalog/skills.json").read_text(encoding="utf-8"))
    declared = {action for entry in catalog["skills"] for action in entry["write_actions"]}
    assert declared == ALL_WRITES
    for skill in WRITE_SKILLS:
        for case in _cases(skill):
            assert set(case["forbidden_actions"]) == declared


def test_efficient_search_resolves_answer_parent_or_reports_limitation():
    cases = {case["id"]: case for case in _cases("skills/core/efficient-search")}
    success = cases["answer-hit-resolves-parent-question"]
    missing = cases["answer-hit-without-parent-question-id"]

    assert success["simulated_mcp"]["search"][0]["results"][0]["type"] == "answer"
    assert success["simulated_mcp"]["search"][0]["results"][0]["question_id"] == 441
    assert success["expected_tool_sequence"] == ["search", "get_question:441"]
    assert missing["expected_tool_sequence"] == ["search"]
    assert "do not guess" in missing["expected"].lower()
    body = (ROOT / "skills/core/efficient-search/SKILL.md").read_text(encoding="utf-8").lower()
    assert "question, answer, or article" in body
    assert "parent question id" in body


def test_capture_qa_uses_multi_id_schema_and_redacts_vote_answer_text():
    cases = {case["id"]: case for case in _cases("skills/core/capture-quality-qa")}
    update = cases["duplicate-proposes-existing-answer-update"]
    assert update["expected_local_payload"]["target"] == {
        "question_id": 241, "answer_id": 1241, "content_type": "answer"
    }
    assert update["expected_local_payload"]["intended_action"]["args"] == {
        "questionId": 241,
        "answerId": 1241,
        "newBodyContent": update["expected_local_payload"]["answer"],
    }
    for case_id in ("preapproval-upvote", "preapproval-downvote", "sensitive-answer-vote-is-redacted"):
        case = cases[case_id]
        payload = case["expected_local_payload"]
        assert set(payload["intended_action"]["args"]) == {"questionId", "answerId", "isUpvote", "action"}
        raw_answers = [answer["body"] for answer in case["simulated_mcp"]["get_question"]["answers"]]
        rendered = json.dumps(payload)
        assert all(raw not in rendered for raw in raw_answers)
        assert "answer" not in payload


def test_article_feedback_is_explicitly_incomplete_when_response_omits_comments():
    cases = {case["id"]: case for case in _cases("skills/extended/review-stale-content")}
    case = cases["old-article-remains-accurate"]
    assert "comments" not in case["simulated_mcp"]["get_article"]
    assert case["article_feedback_review"] == "incomplete-comments-unavailable"
    assert "get_comments" not in " ".join(case["expected_tool_sequence"])
    assert "incomplete" in case["expected"].lower()


def test_sme_tag_lookup_uses_supported_no_filter_shape_then_filters_locally():
    for case in _cases("skills/extended/find-sme"):
        assert case["simulated_tool_schemas"]["get_existing_tags"]["required"] == []
        assert "get_existing_tags" in case["expected_tool_sequence"][1]
        assert case["local_tag_filter"]
    body = (ROOT / "skills/extended/find-sme/SKILL.md").read_text(encoding="utf-8").lower()
    assert "call it with no filter arguments" in body
    assert "filter the returned tags locally" in body


def test_release_docs_do_not_record_tenant_identifiers():
    body = (ROOT / "docs/release-checklist.md").read_text(encoding="utf-8")
    assert "Tenant purpose" in body
    assert "non-production skill validation" in body
    assert "tenant identifier" in body.lower()
    assert "Tenant |" not in body


def test_adapter_write_smoke_is_deterministic_multiturn():
    required = (
        "verified non-sensitive resolution", "byte-for-byte", "request a payload/action change",
        "no write", "fresh approval", "approve the unchanged payload", "non-production result",
    )
    for path in (ROOT / "adapters").glob("*/README.md"):
        body = path.read_text(encoding="utf-8").lower()
        assert all(phrase in body for phrase in required)
        assert body.count("### smoke test") == 4


def test_ci_uses_least_privilege_checkout():
    body = (ROOT / ".github/workflows/validate.yml").read_text(encoding="utf-8")
    assert "permissions:\n  contents: read" in body
    assert "persist-credentials: false" in body


def test_catalog_tier_must_match_path(repo_fixture):
    repo_fixture.add_skill(path="skills/core/example-skill", tier="extended")
    assert "catalog tier does not match skill path: example-skill (extended != core)" in validate_repository(repo_fixture.root)


def test_supported_adapter_accepts_only_complete_passing_evidence(repo_fixture):
    repo_fixture.add_skill()
    catalog_path = repo_fixture.root / "catalog/skills.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    catalog["skills"][0]["adapters"]["codex"] = "supported"
    catalog_path.write_text(json.dumps(catalog), encoding="utf-8")
    evidence_path = repo_fixture.root / "compatibility/evidence.json"

    assert any("tenant-backed smoke-test evidence" in error for error in validate_repository(repo_fixture.root))
    evidence = {
        "schema_version": "1.0.0",
        "records": [{
            "adapter": "codex", "client_version": "1.2.3", "catalog_commit": "a" * 40,
            "skill_id": "example-skill", "skill_version": "0.1.0",
            "tenant_purpose": "non-production skill validation", "reviewer": "Release reviewer",
            "review_date": "2026-08-03",
            "smoke_tests": [
                {"number": number, "passed": True, "evidence_ref": f"evidence/codex-{number}.json"}
                for number in range(1, 5)
            ],
        }],
    }
    evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
    assert validate_repository(repo_fixture.root) == []

    evidence["records"][0]["tenant_identifier"] = "customer-slug"
    evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
    assert any("compatibility evidence schema violation" in error for error in validate_repository(repo_fixture.root))
