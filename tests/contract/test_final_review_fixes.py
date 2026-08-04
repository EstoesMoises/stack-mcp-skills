from __future__ import annotations

import json
from pathlib import Path
import subprocess

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
        assert "already succeeded" in str(case["expected"]).lower()
        assert "no retry" in str(case["expected"]).lower()
        assert case["expected_tool_sequence"][-1] == "confirmed_no_retry"
        assert "redisplay_payload" not in case["expected_tool_sequence"]
        assert "fresh_explicit_approval" not in case["expected_tool_sequence"]
        payload = case["prior_approved_payload"]
        action = payload["intended_action"]
        schema = case["simulated_write_tool_schema"]
        assert action["tool"] == schema["tool"]
        input_schema = schema["input_schema"]
        assert input_schema["type"] == "object"
        assert input_schema["additionalProperties"] is False
        assert set(action["args"]) == set(input_schema["required"])
        assert set(input_schema["properties"]) == set(input_schema["required"])
        args = action["args"]
        for name, value in args.items():
            property_schema = input_schema["properties"][name]
            expected_type = property_schema["type"]
            assert (
                expected_type == "string" and isinstance(value, str)
                or expected_type == "number" and isinstance(value, (int, float)) and not isinstance(value, bool)
                or expected_type == "boolean" and isinstance(value, bool)
                or expected_type == "array" and isinstance(value, list)
            )
            if expected_type == "array":
                assert property_schema["items"] == {"type": "string"}
                assert all(isinstance(item, str) for item in value)
        if action["tool"] == "create_QA":
            assert args == {name: payload[name] for name in ("title", "question", "answer", "tags")}
        elif action["tool"] == "create_article":
            assert args == {name: payload[name] for name in ("title", "body", "tags")}
        elif action["tool"] == "create_question":
            assert args == {
                "title": payload["title"], "body": payload["question"],
                "tags": payload["tags"], "draftReviewed": payload["draftReviewed"],
            }
        elif action["tool"] == "update_answer":
            assert args == {
                "questionId": payload["target"]["question_id"],
                "answerId": payload["target"]["answer_id"],
                "newBodyContent": payload["proposed_answer"],
            }
        else:
            assert args == {"questionId": payload["target"]["question_id"], "answer": payload["answer"]}
        observations = case["simulated_reconciliation"]["observations"]
        if action["tool"] in {"create_QA", "create_article", "create_question"}:
            observed = observations["created_content"]
            retrieval_key = "get_article" if action["tool"] == "create_article" else "get_question"
            assert observed == case["simulated_mcp"][retrieval_key]
            assert observed["title"] == args["title"]
            if action["tool"] == "create_QA":
                assert observed["question"] == args["question"]
                assert observed["answer"] == args["answer"]
            else:
                assert observed["body"] == args["body"]
            assert observed["tags"] == args["tags"]
            if action["tool"] == "create_question":
                assert observed["draftReviewed"] == args["draftReviewed"]
        else:
            retrieved = case["simulated_mcp"]["get_question"]
            if action["tool"] == "submit_user_answer":
                retrieved = retrieved[str(args["questionId"])]
            assert observations["question"]["id"] == args["questionId"]
            assert observations["question"]["id"] == retrieved["id"]
            assert observations["answer"] in retrieved["answers"]
            assert observations["answer"]["body"] == (
                args["newBodyContent"] if action["tool"] == "update_answer" else args["answer"]
            )
            if action["tool"] == "update_answer":
                assert observations["answer"]["id"] == args["answerId"]

    policy = (ROOT / "standards/policy-contract.md").read_text(encoding="utf-8").lower()
    assert "ambiguous write outcome" in policy
    assert "fresh explicit approval" in policy
    shared = json.loads((ROOT / "standards/retry-contract.json").read_text(encoding="utf-8"))
    inconclusive = shared["cases"][0]
    assert inconclusive["outcome"] == "inconclusive"
    assert inconclusive["expected_tool_sequence"] == [
        "reconcile_read_only", "redisplay_complete_payload", "fresh_explicit_approval"
    ]
    assert not set(inconclusive["expected_tool_sequence"]) & ALL_WRITES
    assert inconclusive["prior_approved_payload"] == inconclusive["redisplayed_payload"]
    shared_payload = inconclusive["redisplayed_payload"]
    assert shared_payload["intended_action"]["args"] == {
        name: shared_payload[name] for name in ("title", "body", "tags")
    }


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
        "question_id": 241, "answer_id": 1241
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


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        [
            "git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
            "-c", "core.autocrlf=false", "-C", str(root), *args,
        ],
        check=True, capture_output=True, text=True,
    ).stdout.strip()


def _write_smoke_artifacts(root: Path, adapter: str = "codex") -> list[dict[str, object]]:
    evidence_dir = root / "compatibility/smoke-evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    smoke_tests = []
    check_ids = {
        1: "conditional-search-and-full-retrieval",
        2: "negative-trigger-no-mcp-call",
        3: "write-change-reapproval-and-exact-args",
        4: "honest-mcp-failure-reporting",
    }
    for number in range(1, 5):
        path = evidence_dir / f"{adapter}-{number}.json"
        path.write_text(json.dumps({
            "schema_version": "1.0.0", "adapter": adapter, "smoke_test": number,
            "passed": True, "redacted": True, "check_id": check_ids[number],
        }), encoding="utf-8")
        smoke_tests.append({
            "number": number, "passed": True,
            "evidence_ref": f"compatibility/smoke-evidence/{adapter}-{number}.json",
        })
    return smoke_tests


def test_supported_adapter_accepts_only_complete_passing_evidence(repo_fixture):
    repo_fixture.add_skill()
    smoke_tests = _write_smoke_artifacts(repo_fixture.root)
    _git(repo_fixture.root, "init", "-q")
    _git(repo_fixture.root, "add", ".")
    _git(repo_fixture.root, "commit", "-qm", "release candidate")
    release_candidate = _git(repo_fixture.root, "rev-parse", "HEAD")
    catalog_path = repo_fixture.root / "catalog/skills.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    catalog["skills"][0]["adapters"]["codex"] = "supported"
    catalog_path.write_text(json.dumps(catalog), encoding="utf-8")
    evidence_path = repo_fixture.root / "compatibility/evidence.json"

    assert any("tenant-backed smoke-test evidence" in error for error in validate_repository(repo_fixture.root))
    evidence = {
        "schema_version": "1.0.0", "release_candidate_commit": release_candidate,
        "records": [{
            "adapter": "codex", "client_version": "1.2.3", "catalog_commit": release_candidate,
            "skill_id": "example-skill", "skill_version": "0.1.0",
            "tenant_purpose": "non-production skill validation", "reviewer": "Release reviewer",
            "review_date": "2026-08-03", "smoke_tests": smoke_tests,
        }],
    }
    evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
    assert validate_repository(repo_fixture.root) == []

    evidence["records"][0]["catalog_commit"] = "b" * 40
    evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
    assert any("does not match release candidate" in error for error in validate_repository(repo_fixture.root))


def test_supported_adapter_rejects_missing_unrelated_or_unsafe_evidence(repo_fixture):
    repo_fixture.add_skill()
    smoke_tests = _write_smoke_artifacts(repo_fixture.root)
    _git(repo_fixture.root, "init", "-q")
    _git(repo_fixture.root, "add", ".")
    _git(repo_fixture.root, "commit", "-qm", "release candidate")
    release_candidate = _git(repo_fixture.root, "rev-parse", "HEAD")
    catalog_path = repo_fixture.root / "catalog/skills.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    catalog["skills"][0]["adapters"]["codex"] = "supported"
    catalog_path.write_text(json.dumps(catalog), encoding="utf-8")
    evidence_path = repo_fixture.root / "compatibility/evidence.json"
    record = {
        "adapter": "codex", "client_version": "1.2.3", "catalog_commit": release_candidate,
        "skill_id": "example-skill", "skill_version": "0.1.0",
        "tenant_purpose": "non-production skill validation", "reviewer": "Release reviewer",
        "review_date": "2026-08-03", "smoke_tests": smoke_tests,
    }

    for bad_ref in (
        "compatibility/smoke-evidence/missing.json",
        "compatibility/smoke-evidence/../evidence.json",
        "compatibility/smoke-evidence/codex-2.json",
    ):
        changed = json.loads(json.dumps(record))
        changed["smoke_tests"][0]["evidence_ref"] = bad_ref
        evidence_path.write_text(json.dumps({
            "schema_version": "1.0.0", "release_candidate_commit": release_candidate, "records": [changed]
        }), encoding="utf-8")
        assert validate_repository(repo_fixture.root)

    evidence_path.write_text(json.dumps({
        "schema_version": "1.0.0", "release_candidate_commit": "c" * 40, "records": [record]
    }), encoding="utf-8")
    errors = validate_repository(repo_fixture.root)
    assert any("real ancestor commit" in error for error in errors)


def test_supported_adapter_fails_closed_without_git_audit_context(repo_fixture):
    repo_fixture.add_skill()
    smoke_tests = _write_smoke_artifacts(repo_fixture.root)
    catalog_path = repo_fixture.root / "catalog/skills.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    catalog["skills"][0]["adapters"]["codex"] = "supported"
    catalog_path.write_text(json.dumps(catalog), encoding="utf-8")
    candidate = "d" * 40
    (repo_fixture.root / "compatibility/evidence.json").write_text(json.dumps({
        "schema_version": "1.0.0", "release_candidate_commit": candidate,
        "records": [{
            "adapter": "codex", "client_version": "1.2.3", "catalog_commit": candidate,
            "skill_id": "example-skill", "skill_version": "0.1.0",
            "tenant_purpose": "non-production skill validation", "reviewer": "Release reviewer",
            "review_date": "2026-08-03", "smoke_tests": smoke_tests,
        }],
    }), encoding="utf-8")

    errors = validate_repository(repo_fixture.root)
    assert any("real ancestor commit" in error for error in errors)
    assert any("tenant-backed smoke-test evidence" in error for error in errors)


def test_supported_adapter_compares_candidate_artifact_as_raw_bytes(repo_fixture):
    repo_fixture.add_skill()
    smoke_tests = _write_smoke_artifacts(repo_fixture.root)
    artifact_path = repo_fixture.root / smoke_tests[0]["evidence_ref"]
    candidate_artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    crlf_bytes = (json.dumps(candidate_artifact, indent=2) + "\n").replace("\n", "\r\n").encode()
    artifact_path.write_bytes(crlf_bytes)
    _git(repo_fixture.root, "init", "-q")
    _git(repo_fixture.root, "add", ".")
    _git(repo_fixture.root, "commit", "-qm", "release candidate")
    release_candidate = _git(repo_fixture.root, "rev-parse", "HEAD")

    artifact_path.write_bytes(crlf_bytes.replace(b"\r\n", b"\n"))
    catalog_path = repo_fixture.root / "catalog/skills.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    catalog["skills"][0]["adapters"]["codex"] = "supported"
    catalog_path.write_text(json.dumps(catalog), encoding="utf-8")
    (repo_fixture.root / "compatibility/evidence.json").write_text(json.dumps({
        "schema_version": "1.0.0", "release_candidate_commit": release_candidate,
        "records": [{
            "adapter": "codex", "client_version": "1.2.3", "catalog_commit": release_candidate,
            "skill_id": "example-skill", "skill_version": "0.1.0",
            "tenant_purpose": "non-production skill validation", "reviewer": "Release reviewer",
            "review_date": "2026-08-03", "smoke_tests": smoke_tests,
        }],
    }), encoding="utf-8")

    errors = validate_repository(repo_fixture.root)
    assert any("not exact release-candidate content" in error for error in errors)
    assert any("tenant-backed smoke-test evidence" in error for error in errors)
