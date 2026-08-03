import json
from pathlib import Path

import pytest


EXPECTED_SKILLS = {"efficient-search", "company-debugging", "capture-quality-qa", "onboarding"}


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).parents[2]


@pytest.fixture
def catalog(repo_root: Path) -> dict[str, object]:
    return json.loads((repo_root / "catalog" / "skills.json").read_text(encoding="utf-8"))


def test_catalog_has_expected_skills(repo_root, catalog):
    assert {entry["id"] for entry in catalog["skills"]} == EXPECTED_SKILLS
