from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil

import pytest

from stack_skill_catalog.marketplace_distribution import generate_distribution


ROOT = Path(__file__).parents[2]
SCRIPT_PATH = ROOT / "scripts/build_marketplace.py"
SPEC = importlib.util.spec_from_file_location("build_marketplace", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
main = MODULE.main


def _source_root(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    shutil.copytree(ROOT / "catalog", root / "catalog")
    shutil.copytree(ROOT / "standards", root / "standards")
    shutil.copytree(ROOT / "skills", root / "skills")
    shutil.copyfile(ROOT / "LICENSE", root / "LICENSE")
    return root


def test_check_reports_relative_missing_surfaces_before_generation(tmp_path, capsys):
    """A clean source tree must report missing outputs without leaking its absolute path."""
    root = _source_root(tmp_path)

    exit_code = main(["packages", "--mode", "check", "--root", str(root)])

    output = capsys.readouterr().out
    payload = json.loads(output)
    assert exit_code == 1
    assert payload == {
        "differences": [
            "missing: .agents/plugins/marketplace.json",
            "missing: .claude-plugin/marketplace.json",
            "missing: plugins",
        ],
        "valid": False,
    }
    assert str(root) not in output


def test_write_then_check_creates_an_exact_distribution(tmp_path, capsys):
    """Write mode must create all surfaces that a following check accepts byte-for-byte."""
    root = _source_root(tmp_path)

    assert main(["packages", "--mode", "write", "--root", str(root)]) == 0
    write_payload = json.loads(capsys.readouterr().out)
    assert write_payload == {"generated": True, "root": str(root.resolve())}
    assert main(["packages", "--mode", "check", "--root", str(root)]) == 0
    assert json.loads(capsys.readouterr().out) == {"differences": [], "valid": True}


def test_check_reports_changed_generated_bytes_and_unexpected_stale_files(tmp_path, capsys):
    """Byte edits and stale packages must both appear in deterministic drift output."""
    root = _source_root(tmp_path)
    assert main(["packages", "--mode", "write", "--root", str(root)]) == 0
    capsys.readouterr()
    readme = root / "plugins/efficient-search/README.md"
    readme.write_bytes(readme.read_bytes() + b"changed\n")
    stale = root / "plugins/stale/file.txt"
    stale.parent.mkdir(parents=True)
    stale.write_text("stale\n", encoding="utf-8")

    assert main(["packages", "--mode", "check", "--root", str(root)]) == 1

    output = capsys.readouterr().out
    differences = json.loads(output)["differences"]
    assert "changed: plugins/efficient-search/README.md" in differences
    assert "unexpected: plugins/stale/file.txt" in differences
    assert str(root) not in output


def test_write_refuses_unmarked_plugins_and_preserves_existing_content(tmp_path, capsys):
    """Write mode must not replace a plugins tree it cannot prove was generated."""
    root = _source_root(tmp_path)
    keep = root / "plugins/keep-me.txt"
    keep.parent.mkdir()
    keep.write_text("keep me\n", encoding="utf-8")

    assert main(["packages", "--mode", "write", "--root", str(root)]) == 1

    payload = json.loads(capsys.readouterr().out)
    assert payload["generated"] is False
    assert keep.read_text(encoding="utf-8") == "keep me\n"
    assert not (root / ".agents/plugins/marketplace.json").exists()
    assert not (root / ".claude-plugin/marketplace.json").exists()


def test_write_refuses_a_plugins_tree_with_an_edited_marker(tmp_path, capsys):
    """Only the exact generated marker authorizes destructive replacement."""
    root = _source_root(tmp_path)
    marker = root / "plugins/.generated-marketplace"
    marker.parent.mkdir()
    marker.write_text("generated but edited\n", encoding="utf-8")

    assert main(["packages", "--mode", "write", "--root", str(root)]) == 1

    payload = json.loads(capsys.readouterr().out)
    assert payload["generated"] is False
    assert marker.read_text(encoding="utf-8") == "generated but edited\n"


@pytest.mark.parametrize("symlinked_parent", [".agents", ".agents/plugins", ".claude-plugin"])
def test_write_refuses_symlinked_manifest_parents(tmp_path, capsys, symlinked_parent):
    """Write mode must not redirect either manifest outside the requested repository root."""
    root = _source_root(tmp_path)
    generated = tmp_path / "generated"
    generate_distribution(root, generated)
    shutil.move(str(generated / "plugins"), root / "plugins")
    outside = tmp_path / "outside"
    outside.mkdir()
    symlink = root / symlinked_parent
    symlink.parent.mkdir(parents=True, exist_ok=True)
    symlink.symlink_to(outside, target_is_directory=True)

    assert main(["packages", "--mode", "write", "--root", str(root)]) == 1

    payload = json.loads(capsys.readouterr().out)
    assert payload["generated"] is False
    assert list(outside.iterdir()) == []
    assert (root / "plugins/.generated-marketplace").is_file()
