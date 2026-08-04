"""Build or check the committed native marketplace package distribution."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from stack_skill_catalog.marketplace_distribution import distribution_diff, write_distribution


def build_parser() -> argparse.ArgumentParser:
    """Create the marketplace build command parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    packages = subparsers.add_parser("packages", help="write or check native plugin packages")
    packages.add_argument("--mode", choices=("write", "check"), required=True)
    packages.add_argument("--root", type=Path, default=Path.cwd())
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the requested package operation and emit stable JSON."""
    parser = build_parser()
    args = parser.parse_args(argv)
    root = args.root.resolve()
    if args.command == "packages" and args.mode == "check":
        differences = distribution_diff(root)
        print(json.dumps({"differences": differences, "valid": not differences}, sort_keys=True))
        return 0 if not differences else 1
    if args.command == "packages" and args.mode == "write":
        try:
            write_distribution(root)
        except (OSError, ValueError) as error:
            print(json.dumps({"error": str(error), "generated": False}, sort_keys=True))
            return 1
        print(json.dumps({"generated": True, "root": str(root)}, sort_keys=True))
        return 0
    parser.error("unsupported command")


if __name__ == "__main__":
    raise SystemExit(main())
