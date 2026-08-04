"""Build or check the committed native marketplace package distribution."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil

from stack_skill_catalog.marketplace_distribution import distribution_diff, write_distribution
from stack_skill_catalog.marketplace_config import load_marketplace_config
from stack_skill_catalog.site import write_site


_OPERATIONAL_ERRORS = (OSError, ValueError, KeyError, TypeError, shutil.Error)


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


def _resolve_root(root: Path) -> Path:
    """Resolve a repository root while normalizing platform symlink-loop errors."""
    try:
        return root.resolve()
    except RuntimeError as error:
        raise OSError("could not resolve repository root") from error


def main(argv: list[str] | None = None) -> int:
    """Run the requested package operation and emit stable JSON."""
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "packages" and args.mode == "check":
        try:
            differences = distribution_diff(_resolve_root(args.root))
        except _OPERATIONAL_ERRORS:
            print(json.dumps({"error": "package check failed", "valid": False}, sort_keys=True))
            return 1
        print(json.dumps({"differences": differences, "valid": not differences}, sort_keys=True))
        return 0 if not differences else 1
    if args.command == "packages" and args.mode == "write":
        try:
            root = _resolve_root(args.root)
            write_distribution(root)
        except _OPERATIONAL_ERRORS:
            print(json.dumps({"error": "package write failed", "generated": False}, sort_keys=True))
            return 1
        print(json.dumps({"generated": True, "root": str(root)}, sort_keys=True))
        return 0
    if args.command == "site":
        try:
            root = _resolve_root(args.root)
            output = Path(os.path.abspath(args.output))
            write_site(root, output, args.source_commit)
            displayed_output = _display_output(root, output)
        except _OPERATIONAL_ERRORS:
            print(json.dumps({"error": "site build failed", "valid": False}, sort_keys=True))
            return 1
        print(
            json.dumps(
                {
                    "output": displayed_output,
                    "source_commit": args.source_commit,
                    "valid": True,
                },
                sort_keys=True,
            )
        )
        return 0
    if args.command == "version":
        try:
            root = _resolve_root(args.root)
            version = load_marketplace_config(root / "catalog" / "marketplace.json").marketplace_version
        except _OPERATIONAL_ERRORS:
            print("marketplace version unavailable")
            return 1
        print(version)
        return 0
    parser.error("unsupported command")


if __name__ == "__main__":
    raise SystemExit(main())
