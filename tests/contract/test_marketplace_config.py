from pathlib import Path

import pytest

from stack_skill_catalog.marketplace_config import (
    MarketplaceConfig,
    load_marketplace_config,
    validate_marketplace,
)
from stack_skill_catalog.validation import validate_repository


ROOT = Path(__file__).parents[2]


def test_public_marketplace_config_loads_as_typed_value():
    config = load_marketplace_config(ROOT / "catalog/marketplace.json")

    assert config == MarketplaceConfig(
        schema_version="1.0.0",
        marketplace_version="0.1.0",
        name="stack-internal",
        display_name="Stack Internal Skills",
        repository="EstoesMoises/stack-mcp-skills",
        site_url="https://estoesmoises.github.io/stack-mcp-skills/",
        publisher_name="Stack Internal Skills",
        category="Productivity",
    )


def test_marketplace_schema_rejects_credentials(tmp_path):
    (tmp_path / "catalog").mkdir()
    (tmp_path / "standards").mkdir()
    (tmp_path / "standards/marketplace-schema.json").write_bytes(
        (ROOT / "standards/marketplace-schema.json").read_bytes()
    )
    config = (ROOT / "catalog/marketplace.json").read_text(encoding="utf-8")
    path = tmp_path / "catalog/marketplace.json"
    path.write_text(config[:-2] + ', "token": "secret"}\n', encoding="utf-8")

    with pytest.raises(ValueError, match="Additional properties"):
        load_marketplace_config(path)


def test_repository_validation_reports_missing_marketplace_config(repo_fixture):
    (repo_fixture.root / "catalog/marketplace.json").unlink()
    assert validate_marketplace(repo_fixture.root) == [
        "marketplace config could not be loaded: catalog/marketplace.json"
    ]


def test_marketplace_validation_reports_missing_schema_with_its_relative_path(repo_fixture):
    (repo_fixture.root / "standards/marketplace-schema.json").unlink()

    assert validate_marketplace(repo_fixture.root) == [
        "marketplace config could not be loaded: standards/marketplace-schema.json"
    ]


def test_repository_validation_sanitizes_invalid_marketplace_values(repo_fixture):
    path = repo_fixture.root / "catalog/marketplace.json"
    config = path.read_text(encoding="utf-8").replace(
        "https://estoesmoises.github.io/stack-mcp-skills/",
        "https://customer.example.invalid/credential=secret",
    )
    path.write_text(config, encoding="utf-8")

    errors = validate_repository(repo_fixture.root)

    assert errors == ["marketplace config is invalid"]
    assert "credential=secret" not in "\n".join(errors)
