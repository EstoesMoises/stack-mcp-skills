"""Validate a Stack Internal skills catalog without contacting an MCP tenant."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from stack_skill_catalog.validation import validate_repository


def main(argv: list[str] | None = None) -> int:
    """Write validation output as JSON and return a shell-friendly status."""
    args = sys.argv[1:] if argv is None else argv
    if len(args) > 1:
        print(json.dumps({"errors": ["expected at most one ROOT argument"], "valid": False}, sort_keys=True))
        return 1
    root = Path(args[0]) if args else Path.cwd()
    errors = validate_repository(root)
    print(json.dumps({"errors": errors, "valid": not errors}, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
