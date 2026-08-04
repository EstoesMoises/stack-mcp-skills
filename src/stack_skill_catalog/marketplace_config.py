"""Marketplace configuration loading and validation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from jsonschema import Draft202012Validator


@dataclass(frozen=True)
class MarketplaceConfig:
    """Canonical marketplace metadata."""

    schema_version: str
    marketplace_version: str
    name: str
    display_name: str
    repository: str
    site_url: str
    publisher_name: str
    category: str


def load_marketplace_config(path: Path) -> MarketplaceConfig:
    """Load and validate a marketplace configuration file."""
    value = json.loads(path.read_text(encoding="utf-8"))
    schema_path = path.parents[1] / "standards" / "marketplace-schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    errors = sorted(
        Draft202012Validator(schema).iter_errors(value),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        raise ValueError("; ".join(error.message for error in errors))
    return MarketplaceConfig(**value)


def validate_marketplace(root: Path) -> list[str]:
    """Return deterministic marketplace configuration validation errors."""
    path = root / "catalog" / "marketplace.json"
    try:
        load_marketplace_config(path)
    except FileNotFoundError:
        return ["marketplace config could not be loaded: catalog/marketplace.json"]
    except (OSError, ValueError, json.JSONDecodeError) as error:
        return [f"marketplace config could not be loaded: {error}"]
    return []
