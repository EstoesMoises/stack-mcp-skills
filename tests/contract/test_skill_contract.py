from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from stack_skill_catalog.validation import validate_repository


_QA_WRITE_ACTIONS = (
    "draft_question",
    "create_question",
    "create_QA",
    "submit_user_answer",
    "update_question",
    "update_answer",
    "vote",
)

_KNOWLEDGE_GAP_WRITE_ACTIONS = (
    "draft_question",
    "create_question",
    "create_QA",
    "create_article",
    "submit_user_answer",
    "update_question",
    "update_answer",
    "vote",
)

_ONBOARDING_TOPICS = (
    "prerequisites",
    "setup",
    "architecture",
    "workflows",
    "first-tasks",
)


def _assert_onboarding_search_contract(
    sequence: list[str],
    attempts: list[dict[str, str]],
    responses: dict[str, list[object]],
    budget_checkpoint: dict[str, object] | None,
) -> None:
    """Validate explicit topic metadata, result mapping, and hard search guards."""
    search_steps = [step for step in sequence if step.startswith("search:")]
    assert len(search_steps) == len(attempts)
    result_keys = [attempt.get("result_key") for attempt in attempts]
    assert all(isinstance(result_key, str) for result_key in result_keys)
    assert len(set(result_keys)) == len(result_keys)
    assert set(result_keys) == set(responses)

    searches_by_topic: dict[str, int] = {}
    for step, attempt in zip(search_steps, attempts, strict=True):
        assert set(("topic", "query_kind", "result_key")) <= set(attempt)
        topic = attempt["topic"]
        query_kind = attempt["query_kind"]
        result_key = attempt["result_key"]
        assert topic in _ONBOARDING_TOPICS
        assert query_kind in {"focused", "broadened"}
        assert step == f"search:{result_key}"
        assert result_key in responses

        searches_by_topic[topic] = searches_by_topic.get(topic, 0) + 1
        assert searches_by_topic[topic] <= 3
        assert query_kind == ("focused" if searches_by_topic[topic] == 1 else "broadened")

    disclosure_step = "disclose_whole_path_budget"
    confirmation_step = "user_confirms_continue"
    if len(search_steps) <= 8:
        assert budget_checkpoint is None
        assert disclosure_step not in sequence
        assert confirmation_step not in sequence
        return

    assert budget_checkpoint == {
        "after_search_call": 8,
        "before_search_call": 9,
        "disclosure_step": disclosure_step,
        "confirmation_step": confirmation_step,
    }
    disclosure_index = sequence.index(disclosure_step)
    confirmation_index = sequence.index(confirmation_step)
    ninth_search_index = sequence.index(search_steps[8])
    assert sum(step.startswith("search:") for step in sequence[:disclosure_index]) == 8
    assert sum(step.startswith("search:") for step in sequence[:confirmation_index]) == 8
    assert disclosure_index < confirmation_index < ninth_search_index


def test_onboarding_evals_search_every_topic_and_exhaust_missing_coverage():
    """A rendered gap is evidence of three empty topic searches, never an assumption."""
    eval_path = Path(__file__).parents[2] / "skills/extended/onboarding/evals/evals.json"
    cases = json.loads(eval_path.read_text(encoding="utf-8"))["cases"]

    for case in cases:
        sequence = case["expected_tool_sequence"]
        responses = case["simulated_mcp"]["search"]
        _assert_onboarding_search_contract(
            sequence,
            case["search_attempts"],
            responses,
            case.get("budget_checkpoint"),
        )
        for topic in _ONBOARDING_TOPICS:
            assert f"search:{topic}" in sequence
            assert topic in responses

        for topic in case["missing_topics"]:
            attempts = (
                f"search:{topic}",
                f"search:{topic}-broadened-1",
                f"search:{topic}-broadened-2",
            )
            assert all(attempt in sequence for attempt in attempts)
            assert all(responses[attempt.removeprefix("search:")] == [] for attempt in attempts)
            assert f"Missing coverage: {topic}" in case["expected"]


def test_onboarding_eval_exposes_whole_path_search_budget_guard():
    """Every ninth path search needs a checkpoint, whatever kind of query it is."""
    eval_path = Path(__file__).parents[2] / "skills/extended/onboarding/evals/evals.json"
    cases = json.loads(eval_path.read_text(encoding="utf-8"))["cases"]
    case = next(item for item in cases if item["id"] == "payments-team-transfer-path")
    sequence = case["expected_tool_sequence"]
    checkpoint = sequence.index("disclose_whole_path_budget")

    assert sum(step.startswith("search:") for step in sequence[:checkpoint]) == 8
    assert sequence[checkpoint + 1] == "user_confirms_continue"
    assert any(step.startswith("search:") for step in sequence[checkpoint + 2:])
    assert "completed searches" in case["expected"]
    assert "remaining topics" in case["expected"]

    skill_path = Path(__file__).parents[2] / "skills/extended/onboarding/SKILL.md"
    body = skill_path.read_text(encoding="utf-8")
    assert "including focused" in body
    assert "before call 9 of any kind" in body
    assert case["budget_checkpoint"] == {
        "after_search_call": 8,
        "before_search_call": 9,
        "disclosure_step": "disclose_whole_path_budget",
        "confirmation_step": "user_confirms_continue",
    }


def test_onboarding_continuation_cannot_permit_a_fourth_topic_search():
    """Confirmation may resume the path, but it cannot reopen an exhausted topic."""
    skill_path = Path(__file__).parents[2] / "skills/extended/onboarding/SKILL.md"
    body = skill_path.read_text(encoding="utf-8")

    assert "even if the user asks to continue" in body
    assert "separately scoped follow-up" in body
    with pytest.raises(AssertionError):
        _assert_onboarding_search_contract(
            [
                "search:architecture-primary",
                "search:architecture-alternate-1",
                "search:architecture-alternate-2",
                "search:architecture-alternate-3",
            ],
            [
                {"topic": "architecture", "query_kind": "focused", "result_key": "architecture-primary"},
                {"topic": "architecture", "query_kind": "broadened", "result_key": "architecture-alternate-1"},
                {"topic": "architecture", "query_kind": "broadened", "result_key": "architecture-alternate-2"},
                {"topic": "architecture", "query_kind": "broadened", "result_key": "architecture-alternate-3"},
            ],
            {
                "architecture-primary": [],
                "architecture-alternate-1": [],
                "architecture-alternate-2": [],
                "architecture-alternate-3": [],
            },
            None,
        )


def test_onboarding_early_confirmation_cannot_bypass_ninth_search_gate():
    """A checkpoint before call eight cannot authorize call nine."""
    with pytest.raises(AssertionError):
        _assert_onboarding_search_contract(
            [
                "search:prerequisites",
                "search:setup",
                "search:architecture",
                "search:workflows",
                "search:first-tasks",
                "search:prerequisites-broadened-1",
                "search:setup-broadened-1",
                "disclose_whole_path_budget",
                "user_confirms_continue",
                "search:architecture-broadened-1",
                "search:workflows-broadened-1",
            ],
            [
                {"topic": "prerequisites", "query_kind": "focused", "result_key": "prerequisites"},
                {"topic": "setup", "query_kind": "focused", "result_key": "setup"},
                {"topic": "architecture", "query_kind": "focused", "result_key": "architecture"},
                {"topic": "workflows", "query_kind": "focused", "result_key": "workflows"},
                {"topic": "first-tasks", "query_kind": "focused", "result_key": "first-tasks"},
                {"topic": "prerequisites", "query_kind": "broadened", "result_key": "prerequisites-broadened-1"},
                {"topic": "setup", "query_kind": "broadened", "result_key": "setup-broadened-1"},
                {"topic": "architecture", "query_kind": "broadened", "result_key": "architecture-broadened-1"},
                {"topic": "workflows", "query_kind": "broadened", "result_key": "workflows-broadened-1"},
            ],
            {
                "prerequisites": [],
                "setup": [],
                "architecture": [],
                "workflows": [],
                "first-tasks": [],
                "prerequisites-broadened-1": [],
                "setup-broadened-1": [],
                "architecture-broadened-1": [],
                "workflows-broadened-1": [],
            },
            {
                "after_search_call": 8,
                "before_search_call": 9,
                "disclosure_step": "disclose_whole_path_budget",
                "confirmation_step": "user_confirms_continue",
            },
        )


def test_onboarding_duplicate_result_key_is_rejected():
    """Two search calls may not share one simulated response key."""
    with pytest.raises(AssertionError):
        _assert_onboarding_search_contract(
            ["search:shared-result", "search:shared-result"],
            [
                {"topic": "setup", "query_kind": "focused", "result_key": "shared-result"},
                {"topic": "architecture", "query_kind": "focused", "result_key": "shared-result"},
            ],
            {"shared-result": []},
            None,
        )


def test_onboarding_unused_simulated_response_is_rejected():
    """The simulated search map must not contain a response without an attempt."""
    with pytest.raises(AssertionError):
        _assert_onboarding_search_contract(
            ["search:setup-focused"],
            [{"topic": "setup", "query_kind": "focused", "result_key": "setup-focused"}],
            {"setup-focused": [], "unused-response": []},
            None,
        )


def test_capture_quality_qa_evals_forbid_every_write_before_approval():
    """Keep every capture scenario safely paused at its approval gate."""
    eval_path = Path(__file__).parents[2] / "skills/core/capture-quality-qa/evals/evals.json"
    cases = json.loads(eval_path.read_text(encoding="utf-8"))["cases"]
    cases_by_id = {case["id"]: case for case in cases}

    assert {
        "validated-connection-timeout-fix",
        "duplicate-proposes-existing-answer-update",
        "sensitive-draft-is-sanitized-before-display",
        "preapproval-upvote",
        "preapproval-downvote",
    } <= cases_by_id.keys()

    required_guard = "Before explicit approval, do not call any write action."
    for case in cases:
        assert case["forbidden_actions"] == list(_QA_WRITE_ACTIONS)
        assert required_guard in case["expected"]
        assert not set(case["expected_tool_sequence"]) & set(_QA_WRITE_ACTIONS)

    duplicate = cases_by_id["duplicate-proposes-existing-answer-update"]
    assert duplicate["simulated_mcp"]["get_question"]["answers"] == [
        {"id": "a-241", "body": "Retry the migration manually after lock contention."}
    ]
    assert duplicate["expected_local_payload"]["target_id"] == "a-241"
    assert duplicate["expected_local_payload"]["intended_action"] == {
        "tool": "update_answer",
        "args": {
            "answer_id": "a-241",
            "answer_body": "Resolution: set the orders schema lock timeout to 30 seconds before the backfill instead of manually retrying the migration.",
        },
    }

    for case_id, operation in (("preapproval-upvote", "upvote"), ("preapproval-downvote", "downvote")):
        assert cases_by_id[case_id]["expected_local_payload"]["intended_action"] == {
            "tool": "vote",
            "args": {
                "content_id": "a-512" if operation == "upvote" else "a-513",
                "content_type": "answer",
                "operation": operation,
            },
        }


def test_capture_quality_qa_reports_only_confirmed_write_results():
    """A Q&A write is not successful until the server confirms it."""
    skill_path = Path(__file__).parents[2] / "skills/core/capture-quality-qa/SKILL.md"
    body = skill_path.read_text(encoding="utf-8")

    assert "Report the confirmed result and returned created or updated content ID when available." in body
    assert "Never claim success without server confirmation." in body


def test_capture_quality_qa_evals_require_complete_live_schema_arguments():
    """The displayed action args must be the complete post-approval MCP call."""
    eval_path = Path(__file__).parents[2] / "skills/core/capture-quality-qa/evals/evals.json"
    cases = json.loads(eval_path.read_text(encoding="utf-8"))["cases"]
    visible_mappings = {
        "create_QA": {"title": "title", "question": "question", "answer": "answer", "tags": "tags"},
        "update_answer": {"answer_id": "target_id", "answer_body": "answer"},
        "vote": {"content_id": "target_id"},
    }

    for case in cases:
        payload = case["expected_local_payload"]
        action = payload["intended_action"]
        schema = case["simulated_write_tool_schema"]
        args = action["args"]

        assert action["tool"] == schema["tool"]
        assert set(args) == set(schema["input_schema"]["required"])
        assert args
        for argument_name, visible_field in visible_mappings[action["tool"]].items():
            assert args[argument_name] == payload[visible_field]
        if action["tool"] == "vote":
            assert args["content_type"] == "answer"
            assert args["operation"] in {"upvote", "downvote"}

    skill_path = Path(__file__).parents[2] / "skills/core/capture-quality-qa/SKILL.md"
    body = skill_path.read_text(encoding="utf-8")
    assert "inspect the connected MCP tool's current input schema" in body
    assert "byte-for-byte" in body


def test_fill_knowledge_gap_requires_exhausted_search_and_exact_question_approval():
    """A gap draft follows three empty searches, full duplicate retrieval, and no hidden write."""
    root = Path(__file__).parents[2]
    skill_path = root / "skills/extended/fill-knowledge-gap/SKILL.md"
    eval_path = root / "skills/extended/fill-knowledge-gap/evals/evals.json"

    assert skill_path.is_file()
    assert eval_path.is_file()
    body = skill_path.read_text(encoding="utf-8")
    cases = json.loads(eval_path.read_text(encoding="utf-8"))["cases"]
    cases_by_id = {case["id"]: case for case in cases}
    assert {
        "missing-internal-api-rate-limit-standard",
        "near-match-prevents-duplicate-question",
        "authentication-failure-is-not-a-gap",
    } <= cases_by_id.keys()

    canonical_draft_question_schema = {
        "type": "object",
        "required": ["title", "question", "tags"],
        "properties": {
            "title": {"type": "string"},
            "question": {"type": "string"},
            "tags": {"type": "array", "items": {"type": "string"}},
        },
    }

    def assert_missing_gap_case(case: dict[str, object]) -> None:
        assert case["expected_tool_sequence"] == [
            "search:focused",
            "search:broadened-1",
            "search:broadened-2",
            "get_existing_tags",
        ]
        assert case["search_attempts"] == [
            {"query_kind": "focused", "result_key": "focused"},
            {"query_kind": "broadened", "result_key": "broadened-1"},
            {"query_kind": "broadened", "result_key": "broadened-2"},
        ]
        simulated_mcp = case["simulated_mcp"]
        assert isinstance(simulated_mcp, dict)
        searches = simulated_mcp["search"]
        assert isinstance(searches, dict)
        assert set(searches) == {"focused", "broadened-1", "broadened-2"}
        assert all(results == [] for results in searches.values())

    def assert_exact_draft_question_args(
        payload: dict[str, object], schema: dict[str, object]
    ) -> None:
        assert schema == {"tool": "draft_question", "input_schema": canonical_draft_question_schema}
        action = payload["intended_action"]
        assert isinstance(action, dict)
        assert action["tool"] == "draft_question"
        args = action["args"]
        assert isinstance(args, dict)
        assert set(args) == {"title", "question", "tags"}
        assert args["title"] == payload["title"]
        assert args["question"] == payload["question"]
        assert args["tags"] == payload["tags"]

    def assert_near_match_halts(case: dict[str, object]) -> None:
        assert case["expected_tool_sequence"] == ["search:focused", "get_question"]
        simulated_mcp = case["simulated_mcp"]
        assert isinstance(simulated_mcp, dict)
        retrieved = simulated_mcp["get_question"]
        assert retrieved == {
            "id": "q-913",
            "title": "What retention period applies to Billing exports?",
            "question": "What retention period applies to Billing exports?",
            "answer": "Billing exports are retained for 30 days in the managed export store.",
        }
        assert "expected_local_payload" not in case

    def assert_auth_failure_halts(case: dict[str, object]) -> None:
        assert case["expected_tool_sequence"] == ["search:focused"]
        assert case["simulated_mcp"] == {"search": {"error": "authentication_failed"}}
        assert "access is unknown" in case["expected"]
        assert "expected_local_payload" not in case

    for case in cases:
        assert case["forbidden_actions"] == list(_KNOWLEDGE_GAP_WRITE_ACTIONS)
        assert not set(case["expected_tool_sequence"]) & set(_KNOWLEDGE_GAP_WRITE_ACTIONS)
        assert "Before explicit approval, do not call any write action." in case["expected"]

    missing = cases_by_id["missing-internal-api-rate-limit-standard"]
    assert_missing_gap_case(missing)
    payload = missing["expected_local_payload"]
    schema = missing["simulated_write_tool_schema"]
    assert_exact_draft_question_args(payload, schema)

    near_match = cases_by_id["near-match-prevents-duplicate-question"]
    assert_near_match_halts(near_match)

    auth_failure = cases_by_id["authentication-failure-is-not-a-gap"]
    assert_auth_failure_halts(auth_failure)

    changed_search_budget = deepcopy(missing)
    changed_search_budget["expected_tool_sequence"].pop(2)
    with pytest.raises(AssertionError):
        assert_missing_gap_case(changed_search_budget)

    removed_retrieval_content = deepcopy(near_match)
    del removed_retrieval_content["simulated_mcp"]["get_question"]["answer"]
    with pytest.raises(AssertionError):
        assert_near_match_halts(removed_retrieval_content)

    changed_auth_failure = deepcopy(auth_failure)
    changed_auth_failure["simulated_mcp"]["search"]["error"] = "mcp_unavailable"
    with pytest.raises(AssertionError):
        assert_auth_failure_halts(changed_auth_failure)

    removed_question_argument = deepcopy(payload)
    del removed_question_argument["intended_action"]["args"]["question"]
    weakened_question_schema = deepcopy(schema)
    del weakened_question_schema["input_schema"]["properties"]["question"]
    weakened_question_schema["input_schema"]["required"].remove("question")
    with pytest.raises(AssertionError):
        assert_exact_draft_question_args(removed_question_argument, weakened_question_schema)

    changed_tag_item_schema = deepcopy(schema)
    changed_tag_item_schema["input_schema"]["properties"]["tags"]["items"]["type"] = "number"
    with pytest.raises(AssertionError):
        assert_exact_draft_question_args(payload, changed_tag_item_schema)

    assert "No gap claim is permitted" in body
    assert "one focused search and exactly two broadened searches" in body
    assert "get_question" in body and "get_article" in body
    assert "get_existing_tags" in body
    assert "unknown access state" in body
    assert "Do not suggest, presume, or invent an answer" in body
    assert "complete argument object" in body
    assert "byte-for-byte" in body
    assert "Never claim success without server confirmation." in body


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


def test_find_sme_evals_preserve_discovery_and_tag_resolution_contract():
    """SME recommendations follow discovery only after an exact tag ID is resolved."""
    root = Path(__file__).parents[2]
    skill_path = root / "skills/extended/find-sme/SKILL.md"
    eval_path = root / "skills/extended/find-sme/evals/evals.json"

    assert skill_path.is_file()
    assert eval_path.is_file()
    body = skill_path.read_text(encoding="utf-8")
    cases = json.loads(eval_path.read_text(encoding="utf-8"))["cases"]
    cases_by_id = {case["id"]: case for case in cases}
    all_write_actions = [
        "draft_question",
        "create_question",
        "create_QA",
        "create_article",
        "submit_user_answer",
        "update_question",
        "update_answer",
        "vote",
    ]

    assert {
        "kubernetes-sme-after-insufficient-discovery",
        "ambiguous-auth-tags-require-clarification",
        "no-relevant-discovery-still-resolves-clear-tag",
        "tag-with-no-activity-has-no-sme",
    } <= cases_by_id.keys()
    assert "discovery metadata, not a full-source answer" in body
    assert "current conversation already contains a verified full-source answer" in body
    assert "user says a surfaced source resolves the need" in body
    assert "Do not call `get_question` or `get_article`." in body
    assert "exact semantic match" in body
    assert "do not infer expertise" in body.lower()
    assert "successful search has no relevant results" in body
    assert "continue to `get_existing_tags`" in body

    def assert_resolved_recommendation_order(case):
        sequence = case["expected_tool_sequence"]
        assert len(sequence) == 3
        assert sequence[0].startswith("search:")
        assert sequence[1].startswith("get_existing_tags:")
        assert sequence[2] == f"recommend_SME:{case['resolved_tag']['id']}"

    kubernetes = cases_by_id["kubernetes-sme-after-insufficient-discovery"]
    assert_resolved_recommendation_order(kubernetes)
    assert kubernetes["resolved_tag"] == {"id": "tag-kubernetes", "name": "kubernetes"}

    ambiguous = cases_by_id["ambiguous-auth-tags-require-clarification"]
    assert ambiguous["expected_tool_sequence"][0].startswith("search:")
    assert ambiguous["expected_tool_sequence"][1].startswith("get_existing_tags:")
    assert ambiguous["expected_tool_sequence"][-1] == "ask_user_to_choose_tag"
    assert "recommend_SME" not in ambiguous["expected_tool_sequence"]

    no_relevant = cases_by_id["no-relevant-discovery-still-resolves-clear-tag"]
    assert no_relevant["simulated_mcp"]["search"] == []
    assert_resolved_recommendation_order(no_relevant)
    assert "No relevant sources were found" in no_relevant["expected"]

    no_candidate = cases_by_id["tag-with-no-activity-has-no-sme"]
    assert_resolved_recommendation_order(no_candidate)
    assert no_candidate["simulated_mcp"]["recommend_SME"] == []
    assert "No SME candidates were returned" in no_candidate["expected"]

    for case in cases:
        assert case["forbidden_actions"] == all_write_actions


def test_incident_to_knowledge_requires_verified_facts_and_exact_preapproval_payloads():
    """Incident publishing stays blocked until facts, form, and exact args are approved."""
    root = Path(__file__).parents[2]
    skill_path = root / "skills/extended/incident-to-knowledge/SKILL.md"
    eval_path = root / "skills/extended/incident-to-knowledge/evals/evals.json"
    body = skill_path.read_text(encoding="utf-8")
    cases = json.loads(eval_path.read_text(encoding="utf-8"))["cases"]
    cases_by_id = {case["id"]: case for case in cases}
    all_write_actions = [
        "draft_question",
        "create_question",
        "create_QA",
        "create_article",
        "submit_user_answer",
        "update_question",
        "update_answer",
        "vote",
    ]

    # These literal contracts apply only to deterministic eval schemas. The installed
    # skill still inspects the connected tenant's live schema at runtime.
    simulated_action_contracts = {
        "create_article": {
            "properties": {
                "title": {"type": "string"},
                "body": {"type": "string"},
                "tags": {"type": "array", "items": {"type": "string"}},
            },
            "visible_fields": ("title", "body", "tags"),
        },
        "create_QA": {
            "properties": {
                "title": {"type": "string"},
                "question": {"type": "string"},
                "answer": {"type": "string"},
                "tags": {"type": "array", "items": {"type": "string"}},
            },
            "visible_fields": ("title", "question", "answer", "tags"),
        },
    }

    def assert_schema_derived_args(case, content_argument, section_headings):
        payload = case["expected_local_payload"]
        action = payload["intended_action"]
        schema = case["simulated_write_tool_schema"]
        input_schema = schema["input_schema"]
        args = action["args"]
        properties = input_schema["properties"]
        contract = simulated_action_contracts[action["tool"]]
        expected_property_schemas = contract["properties"]

        assert action["tool"] == schema["tool"]
        assert input_schema["type"] == "object"
        assert input_schema["required"] == list(expected_property_schemas)
        assert properties == expected_property_schemas
        assert set(args) == set(expected_property_schemas)
        for name, expected_property_schema in expected_property_schemas.items():
            expected_type = expected_property_schema["type"]
            value = args[name]
            assert (expected_type == "string" and isinstance(value, str)) or (
                expected_type == "array" and isinstance(value, list)
            )
            if expected_type == "array":
                assert all(isinstance(item, str) for item in value)

        for name in contract["visible_fields"]:
            assert args[name] == payload[name]
        content = args[content_argument]
        for heading in section_headings:
            assert heading in content
        for field in ("summary", "impact", "root_cause", "resolution", "validation"):
            assert payload[field] in content
        for entry in payload["timeline"]:
            assert entry["timestamp"] in content
            assert entry["event"] in content
        for follow_up in payload["follow_ups"]:
            assert follow_up["action"] in content
        for unresolved_fact in payload["unresolved_facts"]:
            assert unresolved_fact["fact"] in content
        for source in payload["related_sources"]:
            assert source["title"] in content
            assert source["id"] in content

    def assert_rejects_changed_argument(case, content_argument, changed_value):
        changed = deepcopy(case)
        changed["expected_local_payload"]["intended_action"]["args"][content_argument] = changed_value
        with pytest.raises(AssertionError):
            assert_schema_derived_args(changed, content_argument, ("Summary:",))

    def assert_rejects_removed_argument_and_schema_property(case, argument, content_argument):
        changed = deepcopy(case)
        args = changed["expected_local_payload"]["intended_action"]["args"]
        input_schema = changed["simulated_write_tool_schema"]["input_schema"]
        del args[argument]
        input_schema["required"].remove(argument)
        del input_schema["properties"][argument]
        with pytest.raises(AssertionError):
            assert_schema_derived_args(changed, content_argument, ("Summary:",))

    def assert_rejects_changed_tags_items_schema(case, content_argument):
        changed = deepcopy(case)
        changed["simulated_write_tool_schema"]["input_schema"]["properties"]["tags"]["items"] = {
            "type": "integer"
        }
        with pytest.raises(AssertionError):
            assert_schema_derived_args(changed, content_argument, ("Summary:",))

    def assert_rejects_removed_tags_items_schema(case, content_argument):
        changed = deepcopy(case)
        changed["simulated_write_tool_schema"]["input_schema"]["properties"]["tags"].pop("items", None)
        with pytest.raises(AssertionError):
            assert_schema_derived_args(changed, content_argument, ("Summary:",))

    assert {
        "verified-load-balancer-outage-article",
        "related-incident-changes-prevention-actions",
        "unresolved-incident-must-not-publish",
        "unclear-incident-format-requires-user-choice",
    } <= cases_by_id.keys()
    assert "speculative root cause" in body
    assert "unresolved material facts" in body
    assert "ask the user to choose" in body
    assert "inspect the selected connected MCP tool's current input schema" in body
    assert "byte-for-byte" in body
    assert "Never claim success without server confirmation." in body

    for case in cases:
        assert case["forbidden_actions"] == all_write_actions
        assert "Before explicit approval, do not call any write action." in case["expected"]
        assert not set(case["expected_tool_sequence"]) & set(all_write_actions)

    article = cases_by_id["verified-load-balancer-outage-article"]
    assert article["expected_local_payload"]["intended_action"]["tool"] == "create_article"
    assert article["expected_local_payload"]["unresolved_facts"] == []
    assert_schema_derived_args(
        article,
        "body",
        ("Summary:", "Impact:", "Timeline:", "Root cause:", "Resolution:", "Validation:", "Follow-up:"),
    )
    assert_rejects_changed_argument(article, "body", "wrong content")
    wrong_article_tags = deepcopy(article)
    wrong_article_tags["expected_local_payload"]["intended_action"]["args"]["tags"] = "wrong type"
    with pytest.raises(AssertionError):
        assert_schema_derived_args(wrong_article_tags, "body", ("Summary:",))
    assert_rejects_changed_tags_items_schema(article, "body")
    assert_rejects_removed_tags_items_schema(article, "body")
    assert_rejects_removed_argument_and_schema_property(article, "body", "body")
    article_payload = json.dumps(article["expected_local_payload"])
    assert "Aurora Labs" not in article_payload
    assert "edge-token-should-not-publish" not in article_payload

    related = cases_by_id["related-incident-changes-prevention-actions"]
    assert related["expected_tool_sequence"][:2] == ["search", "get_article"]
    assert "previous incident" in related["expected"]
    assert related["expected_local_payload"]["intended_action"]["tool"] == "create_QA"
    assert_schema_derived_args(
        related,
        "answer",
        ("Summary:", "Impact:", "Timeline:", "Root cause:", "Resolution:", "Validation:", "Prevention:"),
    )
    assert related["expected_local_payload"]["unresolved_facts"] == [
        {
            "fact": "Owner for the prevention action is not specified.",
            "material": False,
            "reason": "The prevention action itself is verified and can be tracked without an assigned owner.",
        }
    ]
    assert "get_existing_tags" in related["expected_tool_sequence"]
    assert "non-material unresolved owner" in related["expected"]
    assert_rejects_changed_argument(related, "answer", "wrong content")
    wrong_qa_tags = deepcopy(related)
    wrong_qa_tags["expected_local_payload"]["intended_action"]["args"]["tags"] = ["wrong-tag"]
    with pytest.raises(AssertionError):
        assert_schema_derived_args(wrong_qa_tags, "answer", ("Summary:",))
    assert_rejects_changed_tags_items_schema(related, "answer")
    assert_rejects_removed_tags_items_schema(related, "answer")
    assert_rejects_removed_argument_and_schema_property(related, "question", "answer")
    assert_rejects_removed_argument_and_schema_property(related, "answer", "answer")

    unresolved = cases_by_id["unresolved-incident-must-not-publish"]
    assert "expected_local_payload" not in unresolved
    assert "must not publish" in unresolved["expected"]
    assert "get_existing_tags" not in unresolved["expected_tool_sequence"]

    unclear = cases_by_id["unclear-incident-format-requires-user-choice"]
    assert unclear["expected_tool_sequence"] == [
        "search",
        "get_article",
        "get_existing_tags",
        "ask_user_to_choose_article_or_qa",
    ]
    assert "expected_local_payload" not in unclear
    assert "simulated_write_tool_schema" not in unclear
    assert "schema inspection" in unclear["expected"]


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
