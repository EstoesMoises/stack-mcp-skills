"""Build or check the committed native marketplace package distribution."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from stack_skill_catalog.marketplace_distribution import distribution_diff, write_distribution
from stack_skill_catalog.marketplace_config import load_marketplace_config
from stack_skill_catalog.site import write_site


def build_parser() -> argparse.ArgumentParser:
    """Create the marketplace build command parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    packages = subparsers.add_parser("packages", help="write or check native plugin packages")
    packages.add_argument("--mode", choices=("write", "check"), required=True)
    packages.add_argument("--root", type=Path, default=Path.cwd())
    site = subparsers.add_parser("site", help="build the deterministic static marketplace site")
    site.add_argument("--root", type=Path, default=Path.cwd())
    site.add_argument("--output", type=Path, required=True)
    site.add_argument("--source-commit", required=True)
    version = subparsers.add_parser("version", help="print the marketplace semantic version")
    version.add_argument("--root", type=Path, default=Path.cwd())
    return parser


def _display_output(root: Path, output: Path) -> str:
    """Return a non-absolute output path for machine-readable command output."""
    try:
        return output.relative_to(root).as_posix()
    except ValueError:
        return Path(os.path.relpath(output, root)).as_posix()


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
    if args.command == "site":
        output = Path(os.path.abspath(args.output))
        try:
            write_site(root, output, args.source_commit)
        except ValueError as error:
            print(json.dumps({"error": str(error), "valid": False}, sort_keys=True))
            return 1
        except OSError:
            print(json.dumps({"error": "site build failed", "valid": False}, sort_keys=True))
            return 1
        print(
            json.dumps(
                {
                    "output": _display_output(root, output),
                    "source_commit": args.source_commit,
                    "valid": True,
                },
                sort_keys=True,
            )
        )
        return 0
    if args.command == "version":
        print(load_marketplace_config(root / "catalog" / "marketplace.json").marketplace_version)
        return 0
    parser.error("unsupported command")


if __name__ == "__main__":
    raise SystemExit(main())
